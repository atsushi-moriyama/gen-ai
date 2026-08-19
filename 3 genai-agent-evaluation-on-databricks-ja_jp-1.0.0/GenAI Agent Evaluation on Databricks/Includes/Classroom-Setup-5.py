# Databricks notebook source
!pip install --upgrade "mlflow[databricks]==3.7.0"
!pip install "backoff==2.2.1"
!pip install "databricks-openai==0.8.0"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../../Includes/_common

# COMMAND ----------

# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

import json
import mlflow
from mlflow.tracking import MlflowClient

# IMPORTANT: DA must already be initialized in notebook:
# DA = DBAcademyHelper()
# DA.init()

class DemoSetup:
    def __init__(
        self,
        agent_name: str = "airbnb_eval_agent",
        session_id: str = "custom-eval-001",
        experiment_name: str = "airbnb_experiment",
    ):
        # Use DA-managed catalog & schema
        self.catalog_name = DA.catalog_name
        self.schema_name = DA.schema_name

        self.agent_name = agent_name
        self.session_id = session_id

        # Get user from context (works in DA/Vocareum)
        self.username = (
            dbutils.notebook.entry_point
            .getDbutils()
            .notebook()
            .getContext()
            .userName()
            .get()
        )

        # User-scoped experiment
        self.experiment_name = f"/Users/{self.username}/{experiment_name}"

    def run(self) -> None:
        print("=" * 60)
        print("Starting Databricks Agent Demo Setup")
        print("=" * 60)

        self.dev_lab_setup()

    def dev_lab_setup(self) -> None:
        # Use DA-provided catalog/schema
        spark.sql(f"USE CATALOG {self.catalog_name}")
        spark.sql(f"USE SCHEMA {self.schema_name}")

        print(f"Using catalog: {self.catalog_name}")
        print(f"Using schema: {self.schema_name}")

        print("Checking if experiment exists...")

        exp = mlflow.get_experiment_by_name(self.experiment_name)

        if exp is None:
            print("Creating MLflow experiment...")
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        else:
            self.experiment_id = exp.experiment_id

    def get_env_vars(self):
        print(f"Using catalog: {self.catalog_name}")
        print(f"Using schema: {self.schema_name}")
        print(f"Agent name: {self.agent_name}")
        print(f"Session ID: {self.session_id}")
        print(f"Experiment ID: {self.experiment_id}")

        return (
            self.catalog_name,
            self.schema_name,
            self.agent_name,
            self.session_id,
            self.experiment_id,
        )

# COMMAND ----------

DA = DBAcademyHelper()
DA.init()

# COMMAND ----------

demo_setup = DemoSetup()
demo_setup.run()

# Get the catalog, schema, and agent string values
catalog_name, schema_name, agent_name, session_id, experiment_id = demo_setup.get_env_vars()

# COMMAND ----------

username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()

# Set the location of your experiment
EXPERIMENT_NAME = f"/Users/{username}/airbnb_experiment"

# Print the results
print(f"Your username is: {username}")
print(f"The location of your experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

import mlflow

# Enable MLflow's autologging to instrument your application with Tracing
#mlflow.openai.autolog()

# Set up MLflow tracking to Databricks
mlflow.set_tracking_uri("databricks")
mlflow.set_experiment(EXPERIMENT_NAME)

# COMMAND ----------

# Set the registry to Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Load the model using the UC path and alias
alias = "champion"

UC_MODEL_NAME = f"{catalog_name}.{schema_name}.{agent_name}"

print(UC_MODEL_NAME)

# Load by alias (recommended for production)
agent = mlflow.pyfunc.load_model(f"models:/{UC_MODEL_NAME}@{alias}")

# COMMAND ----------

development_config = "../artifacts/configs/agent_eval_config.yaml"

config = mlflow.models.ModelConfig(development_config=development_config)

custom_eval_endpoint = config.get('CUSTOM_EVAL_ENDPOINT')
coherent_instructions = config.get("COHERENT_INSTRUCTIONS")
tool_usage_instructions = config.get("TOOL_USAGE_INSTRUCTIONS")

print(f"Coherent Instructions: {coherent_instructions}")
print(f"Tool Usage Instructions: {tool_usage_instructions}")

print(f"Custom Judge Endpoint: {custom_eval_endpoint}")

# COMMAND ----------

from pprint import pprint

pprint(coherent_instructions)

# COMMAND ----------

pprint(tool_usage_instructions)