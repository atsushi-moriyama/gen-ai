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
from pathlib import Path


class DemoSetup:
    def __init__(
        self,
        agent_name: str = "nyc_taxi_eval_agent",
        experiment_name: str = "eval_lab_experiment"
    ):
        self.catalog_name = DA.catalog_name
        self.schema_name = DA.schema_name
        self.agent_name = agent_name
        self.experiment_name = experiment_name

    def run(self) -> None:
        print("=" * 60)
        print("Starting Databricks Agent Demo Setup")
        print("=" * 60)

        self.dev_lab_setup()

    def dev_lab_setup(self) -> None:
        spark.sql(f"USE CATALOG {self.catalog_name}")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
        spark.sql(f"USE SCHEMA {self.schema_name}")

    def get_env_vars(self):
        print(f"Using catalog: {self.catalog_name}")
        print(f"Using schema: {self.schema_name}")
        print(f"Getting agent name: {self.agent_name}")
        print(f"Getting experiment name: {self.experiment_name}")
        return self.catalog_name, self.schema_name, self.agent_name, self.experiment_name

# COMMAND ----------

DA = DBAcademyHelper()
DA.init()

# COMMAND ----------

demo_setup = DemoSetup()

# Run the build-pipeline
demo_setup.run()

# Get the catalog, schema, and agent string values
catalog_name, schema_name, agent_name, experiment_name = demo_setup.get_env_vars()

# COMMAND ----------

import mlflow

# Enable MLflow's autologging for tracing
# mlflow.openai.autolog()

# Set up MLflow tracking to Databricks
mlflow.set_tracking_uri("databricks")

# Get username and set experiment name
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()
EXPERIMENT_NAME = f"/Users/{username}/{experiment_name}"
mlflow.set_experiment(EXPERIMENT_NAME)

# Set the registry to Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Load the model using the UC path and alias
alias = "champion"
UC_MODEL_NAME = f"{catalog_name}.{schema_name}.{agent_name}"

# Load by alias
agent = mlflow.pyfunc.load_model(f"models:/{UC_MODEL_NAME}@{alias}")

# COMMAND ----------

development_config = "../artifacts/configs/agent_eval_config.yaml"

config = mlflow.models.ModelConfig(development_config=development_config)

correctness_eval_endpoint = config.get('CORRECTNESS_EVAL_ENDPOINT')
safety_endpoint = config.get('SAFETY_EVAL_ENDPOINT')
guidelines_endpoint = config.get("GUIDELINES_ENDPOINT")

print(f"Correctness Endpoint: {correctness_eval_endpoint}")
print(f"Safety Endpoint: {safety_endpoint}")
print(f"Guidelines Endpoint: {guidelines_endpoint}")