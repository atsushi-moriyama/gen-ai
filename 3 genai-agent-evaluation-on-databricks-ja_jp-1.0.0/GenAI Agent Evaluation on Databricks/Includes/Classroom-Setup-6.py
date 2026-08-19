# Databricks notebook source
!pip install --upgrade "mlflow[databricks]==3.7.0"
!pip install "backoff==2.2.1"
!pip install "databricks-openai==0.8.0"
!pip install "mlflow==3.8.1"
!pip install "openai==2.16.0"
!pip install "databricks-connect>=16.1"
# Install prerequisites
!pip install "databricks-agents>=1.1.0"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../../Includes/_common

# COMMAND ----------

# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

import json
import mlflow
from mlflow.entities import SpanType
from mlflow.tracking import MlflowClient
from databricks import agents
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from importlib.metadata import version
from typing import Tuple, Dict, Any
import warnings

# IMPORTANT:
# Make sure this is run before this class:
# DA = DBAcademyHelper()
# DA.init()

class DemoSetup:
    def __init__(
        self,
        agent_name: str = "airbnb_eval_agent",
        experiment_name: str = "feedback_experiment",
        feedback_endpoint: str = "databricks:/databricks-gpt-5-mini",
        model_alias: str = "champion",
        session_id: str = "feedback-session-001",
        llm_endpoint_name: str = "databricks-gpt-oss-20b",
        deployed_agent_exp_name: str = "airbnb_experiment"
    ):

        # ✅ Use DA-managed catalog + schema
        self.catalog_name = DA.catalog_name
        self.schema_name = DA.schema_name

        self.agent_name = agent_name
        self.uc_model_name = f"{self.catalog_name}.{self.schema_name}.{self.agent_name}"

        self.model_alias = model_alias

        self.username = (
            dbutils.notebook.entry_point
            .getDbutils()
            .notebook()
            .getContext()
            .userName()
            .get()
        )

        self.experiment_name = f"/Users/{self.username}/{experiment_name}"
        self.feedback_endpoint = feedback_endpoint
        self.session_id = session_id
        self.llm_endpoint_name = llm_endpoint_name

        # Deployment info
        self.deployment = None
        self.endpoint_name = None
        self.deployed_agent_exp_name = deployed_agent_exp_name

    def run(self) -> None:
        print("=" * 60)
        print("Starting Databricks Agent Demo Setup")
        print("=" * 60)

        self.dev_lab_setup()

        queries = self.queries()
        for query in queries:
            print(f"\nRunning query: {query}")
            self.gen_trace_data(query)

    def dev_lab_setup(self) -> None:
        spark.sql(f"USE CATALOG {self.catalog_name}")
        spark.sql(f"USE SCHEMA {self.schema_name}")

        print(f"Using catalog: {self.catalog_name}")
        print(f"Using schema: {self.schema_name}")

        print("Checking MLflow experiment...")

        exp = mlflow.get_experiment_by_name(self.experiment_name)

        client = MlflowClient()

        if exp is None:
            print(f"Experiment not found. Creating: {self.experiment_name}")
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        else:
            print(f"Experiment exists. Deleting and recreating: {self.experiment_name}")
            client.delete_experiment(exp.experiment_id)
            self.experiment_id = mlflow.create_experiment(self.experiment_name)

    def get_env_vars(self):
        print(f"Using catalog: {self.catalog_name}")
        print(f"Using schema: {self.schema_name}")
        print(f"Agent name: {self.agent_name}")
        print(f"Experiment ID: {self.experiment_id}")

        model_username_string = (
            self.username.split('@')[0]
            .replace(".", "_") + "_agent"
        )

        deployed_model_experiment_loc = (
            f"/Workspace/Users/{self.username}/{self.deployed_agent_exp_name}"
        )

        return (
            self.catalog_name,
            self.schema_name,
            self.agent_name,
            model_username_string,
            deployed_model_experiment_loc,
        )

    def load_agent(self):

        # ⚠️ Keep autolog here (not in model file)
        #mlflow.openai.autolog(log_traces=True)

        mlflow.set_tracking_uri("databricks")
        mlflow.set_experiment(self.experiment_name)
        mlflow.set_registry_uri("databricks-uc")

        agent = mlflow.pyfunc.load_model(
            f"models:/{self.uc_model_name}@{self.model_alias}"
        )

        return agent

    def queries(self):
        return [
            "How many Entire home/apt listings are in the Mission neighborhood?",
            "Count the number of Private room listings in Nob Hill.",
            "What is the average listing price in Haight Ashbury?"
        ]

    def gen_trace_data(self, query: str) -> Tuple[Dict[str, Any]]:

        agent = self.load_agent()

        with mlflow.start_span(
            name="populate_agent_trace",
            span_type=SpanType.AGENT
        ) as span:

            mlflow.update_current_trace(
                metadata={
                    "mlflow.trace.session": self.session_id,
                    "mlflow.trace.user": self.username
                },
                tags={
                    "training_type": "human_feedback_training",
                    "model": self.feedback_endpoint,
                    "agent_type": "TOOL-CALLING"
                }
            )

            query_payload = [
                {"input": [{"role": "user", "content": query}]}
            ]

            response = agent.predict(query_payload)

            span.set_inputs({"query": query})
            span.set_outputs({"response": response})

            trace_id = span.trace_id

        return {"trace_id": trace_id, "response": response}

# COMMAND ----------

DA = DBAcademyHelper()
DA.init()

# COMMAND ----------

demo_setup = DemoSetup()

## Run the setup pipeline
demo_setup.run()

## Get demo-relevant variables
catalog_name, schema_name, agent_name, model_username_string, deployed_model_experiment_loc = demo_setup.get_env_vars()