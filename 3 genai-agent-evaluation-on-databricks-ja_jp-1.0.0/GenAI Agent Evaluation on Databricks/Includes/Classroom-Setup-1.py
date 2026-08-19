# Databricks notebook source
# MAGIC %pip install --upgrade --quiet backoff databricks-openai uv databricks-agents mlflow-skinny[databricks] databricks-langchain langchain-community langchain unitycatalog-langchain[databricks] unitycatalog-ai[databricks] databricks-sdk databricks-vectorsearch

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../../Includes/_common

# COMMAND ----------

# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

import time
import os
import json
import re

from pyspark.sql.functions import concat, lit, col
from pathlib import Path
from string import Template
from importlib.metadata import version

from typing import Iterable, List, Set, Dict

import mlflow
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from mlflow import MlflowClient

from databricks import agents


class DemoSetup:
    def __init__(
        self,
        # NOTE: catalog/schema are now taken from DA (DBAcademyHelper). No manual params.
        databricks_share_name: str = "databricks_airbnb_sample_data",
        schema_name_fallback: str = "demo_agent_eval",  # only used if DA.schema_name missing
        vs_name: str = "genai_vs_endpoint",
        table_name: str = "sf_airbnb_listings",
        alias: str = "champion",
        correctness_eval_endpoint: str = "databricks:/databricks-gpt-oss-20b",
        safety_endpoint: str = "databricks:/databricks-gpt-oss-20b",
        guidelines_endpoint: str = "databricks:/databricks-gpt-oss-120b",
        custom_endpoint: str = "databricks:/databricks-gpt-5-mini",
        llm_endpoint_name: str = "databricks-gpt-oss-20b",
        username: str = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get(),
        deployed_endpoint_name=None,
    ):
        # ---------------------------------------------------------------------
        # DA-driven catalog/schema (NO MANUAL)
        # Assumes you already did:
        #   DA = DBAcademyHelper()
        #   DA.init()
        # ---------------------------------------------------------------------
        try:
            self.catalog_name = DA.catalog_name
        except Exception as e:
            raise RuntimeError(
                "DA.catalog_name is not available. Make sure you ran:\n"
                "  DA = DBAcademyHelper()\n"
                "  DA.init()\n"
                "before instantiating DemoSetup()."
            ) from e

        # schema: prefer DA.schema_name if present, else fallback
        self.schema_name = getattr(DA, "schema_name", None) or schema_name_fallback

        self.vs_name = vs_name
        self.table_name = table_name
        self.username = username

        # Share name override for Vocareum
        if self.username.endswith("@vocareum.com"):
            self.databricks_share_name = "dbacademy_airbnb_sample_data"
        else:
            self.databricks_share_name = databricks_share_name

        self.alias = alias

        # LLM endpoint (for model serving resource + templates)
        self.llm_endpoint_name = llm_endpoint_name

        # Eval endpoints
        self.correctness_eval_endpoint = correctness_eval_endpoint
        self.safety_endpoint = safety_endpoint
        self.custom_endpoint = custom_endpoint
        self.guidelines_endpoint = guidelines_endpoint

        # UC volume path
        self.volume_path = Path(f"/Volumes/{self.catalog_name}/{self.schema_name}/agent_vol")

        # Artifact paths
        self.artifacts_dir = Path("../artifacts/configs")
        self.eval_config_output_path = self.artifacts_dir / "agent_eval_config.yaml"

        # Will be populated dynamically
        self.evaluations = []
        self.agent_configs = {}  # Maps agent name -> config info
        self.experiments = {}  # Maps agent name -> experiment path

        # Deployed endpoint name of the form labuserXXX_agent
        self.deployed_endpoint_name = self.username.split("@")[0].replace(".", "_") + "_agent"

    def run(self):
        print("=" * 60)
        print("Starting Databricks Agent Demo Setup")
        print("=" * 60)

        self.dev_lab_setup()

        try:
            self.process_csv()
        except Exception as e:
            print("❌ Error: Please check that your `databricks_share_name` is correct.")
            return e

        # Dynamically discover all components
        self.discover_components()

        # Write agent code to parent folder
        self.copy_py_files_from_directory("../Includes/agents", "../artifacts")

        # Create tools
        self.create_tools()

        # Render eval config
        self.render_eval_config()

        # Render agent configs and register each agent
        self.register_all_agents()

        # Deploy first agent only (following original pattern)
        if self.agent_configs:
            first_agent_name = list(self.agent_configs.keys())[0]
            self.deploy_agent(first_agent_name)
            print(f"✅ Agent '{first_agent_name}' successfully deployed")

        # Create any additional experiments
        self.create_experiment("feedback_experiment")

    def discover_components(self):
        """Dynamically discover tools, evaluations, and agents"""
        print("\n" + "=" * 60)
        print("Discovering Components")
        print("=" * 60)

        # Get evaluation datasets
        self.evaluations = self.get_filenames_without_extension(
            "../artifacts/evaluation_datasets",
            extensions=(".json",),
        )
        print(f"✅ Discovered {len(self.evaluations)} evaluation datasets")

        # Discover agent files in ./artifacts/
        agent_files = self.get_agent_files("../artifacts")
        print(f"✅ Discovered {len(agent_files)} agent files: {[f.name for f in agent_files]}")

        # Map each agent file to its configuration
        for agent_file in agent_files:
            self.map_agent_config(agent_file)

        print(f"✅ Mapped {len(self.agent_configs)} agent configurations")

        # Discover tools for each agent from their specific subfolders
        self.discover_agent_tools()
        print(f"✅ Discovered tools for all agents")

    def get_agent_files(self, artifacts_dir: str | Path) -> List[Path]:
        """
        Get all .py files containing 'agent' in the name from artifacts directory.
        """
        artifacts_path = Path(artifacts_dir)
        if not artifacts_path.exists():
            raise FileNotFoundError(f"Artifacts directory does not exist: {artifacts_path}")

        agent_files = []
        for file_path in artifacts_path.glob("*.py"):
            if "agent" in file_path.stem.lower():
                agent_files.append(file_path)

        return sorted(agent_files)

    def count_tool_placeholders(self, config_path: Path) -> int:
        """
        Count how many TOOL placeholders (TOOL1, TOOL2, etc.) exist in a config file.
        """
        if not config_path.exists():
            return 0

        content = config_path.read_text(encoding="utf-8")
        tool_placeholders = re.findall(r"\$TOOL\d+", content)
        return len(set(tool_placeholders))

    def discover_agent_tools(self):
        """
        Discover tools for each agent from their specific subfolders.
        Expected structure: ../Includes/agent tools/{agent_name}/tool1.txt

        Updates each agent's config with a 'tools' list.
        """
        for agent_name, config in self.agent_configs.items():
            agent_tools_dir = Path(f"../Includes/agent tools/{agent_name}")

            if not agent_tools_dir.exists():
                print(f"  ⚠️ Warning: Tool directory not found for '{agent_name}': {agent_tools_dir}")
                config["tools"] = []
                continue

            agent_tools = self.get_filenames_without_extension(
                agent_tools_dir,
                extensions=(".txt",),
                recursive=False,
            )

            required_count = config["required_tools_count"]
            if len(agent_tools) != required_count:
                print(
                    f"  ⚠️ Warning: Agent '{agent_name}' expects {required_count} tools, "
                    f"found {len(agent_tools)} in {agent_tools_dir}"
                )

            config["tools"] = agent_tools
            print(f"  - {agent_name}: {len(agent_tools)} tools from {agent_tools_dir.name}/")

    def assign_tools_to_agents(self) -> Dict[str, List[str]]:
        """
        Return tool assignments from pre-discovered agent-specific subfolders.
        """
        return {agent_name: config["tools"] for agent_name, config in self.agent_configs.items()}

    def dev_lab_setup(self):
        spark.sql(f"USE CATALOG {self.catalog_name}")
        print(f"Using catalog: {self.catalog_name}")

        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
        spark.sql(f"USE SCHEMA {self.schema_name}")
        print(f"Using schema: {self.schema_name}")

        spark.sql("CREATE VOLUME IF NOT EXISTS agent_vol")
        print("✅ Volume 'agent_vol' ready")

        mlflow.set_tracking_uri("databricks")
        return None

    def create_experiment(self, experiment_name: str):
        """Create or recreate an experiment"""
        print(f"Setting up experiment: {experiment_name}")
        experiment_path = f"/Workspace/Users/{self.username}/{experiment_name}"

        exp = mlflow.get_experiment_by_name(experiment_path)
        if exp is not None:
            print(f"Experiment exists. Deleting and recreating: {experiment_name}")
            mfc = MlflowClient()
            mfc.delete_experiment(exp.experiment_id)
            print(f"✅ Deleted experiment {exp.experiment_id}")

        mlflow.create_experiment(experiment_path)
        print(f"✅ Created experiment: {experiment_path}")

        return experiment_path

    def create_experiment_for_agent(self, experiment_name: str, agent_name: str):
        """Create or recreate an experiment for a specific agent"""
        print(f"Setting up experiment: {experiment_name}")
        experiment_path = f"/Workspace/Users/{self.username}/{experiment_name}"

        exp = mlflow.get_experiment_by_name(experiment_path)
        if exp is not None:
            print(f"Experiment exists. Deleting and recreating: {experiment_name}")
            mfc = MlflowClient()
            mfc.delete_experiment(exp.experiment_id)
            print(f"✅ Deleted experiment {exp.experiment_id}")

        mlflow.create_experiment(experiment_path)
        print(f"✅ Created experiment: {experiment_path}")

        if agent_name in self.agent_configs:
            self.agent_configs[agent_name]["experiment_path"] = experiment_path

        return experiment_path

    def render_eval_config(self):
        """Render the evaluation config file"""
        eval_template_path = Path("../Includes/agent configs/agent_eval_config.yaml")

        yaml_text = self.render_text_template(
            template_path=eval_template_path,
            substitutions={
                "CORRECTNESS_EVAL_ENDPOINT": self.correctness_eval_endpoint,
                "SAFETY_EVAL_ENDPOINT": self.safety_endpoint,
                "GUIDELINES_ENDPOINT": self.guidelines_endpoint,
                "CUSTOM_EVAL_ENDPOINT": self.custom_endpoint,
            },
        )

        self.update_yaml_config(yaml_text, self.eval_config_output_path)
        print(f"✅ Evaluation config written: {self.eval_config_output_path}")

        for evaluation in self.evaluations:
            self.write_eval_json_to_volume(f"{evaluation}.json")

    def render_text_template(self, template_path: Path, substitutions: dict) -> str:
        """
        Read a text/YAML template and substitute $VARS using string.Template.
        Leaves {{ inputs }}, {{ outputs }}, {{ trace }} untouched.
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        raw = template_path.read_text(encoding="utf-8")
        return Template(raw).substitute(substitutions)

    def update_yaml_config(self, yaml_text: str, yaml_path: Path) -> None:
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_path.write_text(yaml_text, encoding="utf-8")

    def write_eval_json_to_volume(self, file_name: str) -> None:
        read_path = Path(f"../artifacts/evaluation_datasets/{file_name}")
        write_path = Path(f"{self.volume_path}/{file_name}")

        write_path.parent.mkdir(parents=True, exist_ok=True)

        if read_path.exists():
            with read_path.open("r", encoding="utf-8") as f:
                eval_dataset = json.load(f)
            if isinstance(eval_dataset, dict):
                eval_dataset = [eval_dataset]
        else:
            print(f"⚠️ Evaluation file not found: {read_path}")
            eval_dataset = []

        with write_path.open("w", encoding="utf-8") as f:
            json.dump(eval_dataset, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Evaluation dataset written: {write_path.name}")

    def process_csv(self):
        df = (
            spark.read.format("csv")
            .option("header", "true")
            .option("inferSchema", "true")
            .option("multiLine", "true")
            .option("escape", '"')
            .load(f"/Volumes/{self.databricks_share_name}/v01/sf-listings/sf-airbnb.csv")
            .select("id", "name", "neighbourhood", "neighbourhood_cleansed", "summary", "price", "room_type")
            .withColumn(
                "listing_source_information",
                concat(
                    lit("ID of the property: "),
                    col("id"),
                    lit("\nName of the property: "),
                    col("name"),
                    lit("\nSummary of the property: "),
                    col("summary"),
                ),
            )
            .limit(50)
        )

        df.write.mode("overwrite").saveAsTable(self.table_name)

        print(f"✅ Delta table '{self.table_name}' created successfully")
        return df

    def create_tools(self) -> None:
        """Create all discovered tools as UC functions from agent-specific subfolders"""
        print("\n" + "=" * 60)
        print("Creating Tools")
        print("=" * 60)

        all_tools = set()
        for agent_name, config in self.agent_configs.items():
            agent_tools_dir = Path(f"../Includes/agent tools/{agent_name}")
            for tool in config.get("tools", []):
                all_tools.add((tool, agent_tools_dir))

        for tool_name, tools_dir in all_tools:
            drop_stmt = f"DROP FUNCTION IF EXISTS {tool_name}"

            tool_path = tools_dir / f"{tool_name}.txt"
            if not tool_path.exists():
                raise FileNotFoundError(f"Tool DDL template not found: {tool_path}")

            create_stmt = tool_path.read_text(encoding="utf-8")

            spark.sql(drop_stmt)
            spark.sql(create_stmt).collect()

            print(f"  ✅ UC function created: {tool_name} (from {tools_dir.name}/)")

        return None

    def register_all_agents(self):
        """Register all discovered agents to Unity Catalog"""
        print("\n" + "=" * 60)
        print("Registering Agents")
        print("=" * 60)

        tool_assignments = self.assign_tools_to_agents()

        for agent_name, config in self.agent_configs.items():
            print(f"\nRegistering agent: {agent_name}")

            assigned_tools = tool_assignments.get(agent_name, [])

            self.render_agent_config(agent_name, config, assigned_tools)

            self.register_agent(agent_name, config, assigned_tools)

            print(f"✅ Agent '{agent_name}' successfully registered")

    def render_agent_config(self, agent_name: str, config: dict, assigned_tools: List[str]):
        """Render configuration file for a specific agent"""
        substitutions = {
            "LLM_ENDPOINT_NAME": self.llm_endpoint_name,
            "CATALOG_NAME": self.catalog_name,
            "SCHEMA_NAME": self.schema_name,
        }

        for i, tool in enumerate(assigned_tools, start=1):
            substitutions[f"TOOL{i}"] = tool

        yaml_text = self.render_text_template(
            template_path=config["config_template"],
            substitutions=substitutions,
        )

        self.update_yaml_config(yaml_text, config["config_output"])
        print(f"  ✅ Config written: {config['config_output'].name}")

    def register_agent(self, agent_name: str, config: dict, assigned_tools: List[str]):
        """Register a specific agent to Unity Catalog"""
        experiment_path = self.create_experiment_for_agent(config["experiment_name"], agent_name)

        mlflow.set_tracking_uri("databricks")
        mlflow.set_experiment(experiment_path)

        resources = [DatabricksServingEndpoint(endpoint_name=self.llm_endpoint_name)]

        for tool in assigned_tools:
            uc_tool_name = f"{self.catalog_name}.{self.schema_name}.{tool}"
            resources.append(DatabricksFunction(function_name=uc_tool_name))

        if assigned_tools:
            input_example = {"input": [{"role": "user", "content": "What tools do you have available?"}]}
        else:
            input_example = {"input": [{"role": "user", "content": "Hello"}]}

        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="mlflow.types.type_hints")

        tags = {
            "training_type": "agent_eval_training",
            "model": self.llm_endpoint_name,
            "agent_type": "TOOL-CALLING",
            "agent_id": agent_name,
        }

        with mlflow.start_run(tags=tags):
            logged_agent_info = mlflow.pyfunc.log_model(
                name=agent_name,
                python_model=str(config["agent_file"]),
                model_config=str(config["config_output"]),
                artifacts={
                    "agent_config": str(config["config_output"]),
                    "agent_eval_config": str(self.eval_config_output_path),
                },
                input_example=input_example,
                pip_requirements=[
                    "databricks-openai",
                    "backoff",
                    "pyyaml",
                    f"databricks-connect=={version('databricks-connect')}",
                ],
                resources=resources,
            )

        mlflow.set_registry_uri("databricks-uc")

        uc_registered_model_info = mlflow.register_model(
            model_uri=logged_agent_info.model_uri,
            name=config["uc_model_name"],
        )

        mfc = MlflowClient()
        mfc.set_registered_model_alias(
            config["uc_model_name"],
            self.alias,
            uc_registered_model_info.version,
        )

        for key, value in tags.items():
            mfc.set_model_version_tag(
                name=config["uc_model_name"],
                version=uc_registered_model_info.version,
                key=key,
                value=value,
            )

        print(
            f"  ✅ Model registered: {config['uc_model_name']} "
            f"(version {uc_registered_model_info.version}, alias '{self.alias}')"
        )

    def load_agent(self, agent_name: str):
        """Load a specific agent from Unity Catalog"""
        if agent_name not in self.agent_configs:
            raise ValueError(f"Agent '{agent_name}' not found in configurations")

        mlflow.set_registry_uri("databricks-uc")
        uc_model_name = self.agent_configs[agent_name]["uc_model_name"]
        agent = mlflow.pyfunc.load_model(f"models:/{uc_model_name}@{self.alias}")
        return agent

    def get_experiment_path(self, agent_name: str) -> str:
        """Get the experiment path for a specific agent."""
        if agent_name not in self.agent_configs:
            raise ValueError(f"Agent '{agent_name}' not found in configurations")

        experiment_path = self.agent_configs[agent_name].get("experiment_path")
        if not experiment_path:
            experiment_name = self.agent_configs[agent_name]["experiment_name"]
            experiment_path = f"/Workspace/Users/{self.username}/{experiment_name}"

        return experiment_path

    def get_filenames_without_extension(
        self,
        root_dir: str | Path,
        extensions: Iterable[str] = (".txt", ".json", ".yaml", ".yml"),
        recursive: bool = True,
    ) -> List[str]:
        """
        Crawl a directory and return filenames without extensions for the specified file types.
        """
        root = Path(root_dir)

        if not root.exists():
            print(f"⚠️ Directory does not exist: {root}")
            return []

        ext_set: Set[str] = {ext.lower() for ext in extensions}
        pattern = "**/*" if recursive else "*"

        results: List[str] = []

        for path in root.glob(pattern):
            if path.is_file() and path.suffix.lower() in ext_set:
                results.append(path.stem)

        return sorted(results)

    def map_agent_config(self, agent_file: Path):
        """
        Map an agent .py file to its corresponding config file and metadata.
        """
        agent_stem = agent_file.stem
        config_file_name = f"{agent_stem}_config.yaml"
        config_template_path = Path(f"../Includes/agent configs/{config_file_name}")

        if not config_template_path.exists():
            print(f"⚠️ Warning: Config file not found for {agent_file.name}: {config_template_path}")
            return

        agent_name = f"{agent_stem.replace('_agent', '')}_eval_agent"
        experiment_name = f"{agent_stem.replace('_agent', '')}_experiment"

        endpoint_name = self.deployed_endpoint_name

        required_tools_count = self.count_tool_placeholders(config_template_path)

        self.agent_configs[agent_name] = {
            "agent_file": agent_file,
            "config_template": config_template_path,
            "config_output": self.artifacts_dir / config_file_name,
            "required_tools_count": required_tools_count,
            "experiment_name": experiment_name,
            "uc_model_name": f"{self.catalog_name}.{self.schema_name}.{agent_name}",
            "endpoint_name": endpoint_name,
        }

        print(
            f"  - Mapped '{agent_name}' -> {config_file_name} "
            f"(endpoint: '{endpoint_name}', needs {required_tools_count} tools)"
        )

    def deploy_agent(self, agent_name: str, endpoint_name: str = None):
        """
        Deploy a specific agent to a Databricks serving endpoint.
        """
        if agent_name not in self.agent_configs:
            raise ValueError(f"Agent '{agent_name}' not found in configurations")

        config = self.agent_configs[agent_name]
        uc_model_name = config["uc_model_name"]

        if endpoint_name is None:
            endpoint_name = config["endpoint_name"]

        experiment_path = config.get("experiment_path")
        if experiment_path:
            mlflow.set_tracking_uri("databricks")
            mlflow.set_experiment(experiment_path)
            print(f"Using experiment: {experiment_path}")
        else:
            print(f"⚠️ Warning: No experiment path found for agent '{agent_name}'")

        print("=" * 60)
        print(f"Deploying agent: {uc_model_name}")
        print(f"Endpoint name: {endpoint_name}")
        print("=" * 60)

        client = MlflowClient()

        mv = client.get_model_version_by_alias(uc_model_name, self.alias)
        model_version = int(mv.version)
        print(f"Retrieved model version {model_version} with alias '{self.alias}'")

        try:
            from databricks.agents import get_deployments

            existing = get_deployments(endpoint_name=endpoint_name)
            if existing:
                print(
                    f"Endpoint already exists: {existing.endpoint_name} "
                    f"(model={uc_model_name}, version={model_version})"
                )
                return existing
        except Exception:
            pass

        try:
            deployment = agents.deploy(
                model_name=uc_model_name,
                model_version=model_version,
                endpoint_name=endpoint_name,
                scale_to_zero=True,
            )
            print(f"Deployed endpoint: {deployment.endpoint_name}")
            return deployment
        except Exception as e:
            print(f"Endpoint already exists or deployment failed: {e}")
            return None

    def copy_py_files_from_directory(
        self,
        source_dir: str | Path,
        dest_dir: str | Path,
        recursive: bool = True,
    ) -> None:
        """
        Crawl a source directory for .py files and copy them to destination.
        """
        source = Path(source_dir)
        destination = Path(dest_dir)

        if not source.exists():
            print(f"⚠️ Source directory does not exist: {source}")
            return

        destination.mkdir(parents=True, exist_ok=True)

        pattern = "**/*.py" if recursive else "*.py"

        copied_count = 0
        for py_file in source.glob(pattern):
            if py_file.is_file():
                if recursive:
                    relative_path = py_file.relative_to(source)
                    dest_path = destination / relative_path
                else:
                    dest_path = destination / py_file.name

                dest_path.parent.mkdir(parents=True, exist_ok=True)

                content = py_file.read_text(encoding="utf-8")
                dest_path.write_text(content, encoding="utf-8")

                print(f"  ✅ Copied: {py_file.relative_to(source)} -> {dest_path}")
                copied_count += 1

        print(f"\n✅ Copied {copied_count} .py files from {source} to {destination}")

# COMMAND ----------

DA = DBAcademyHelper()
DA.init()

# COMMAND ----------

demo_setup = DemoSetup()
demo_setup.run()