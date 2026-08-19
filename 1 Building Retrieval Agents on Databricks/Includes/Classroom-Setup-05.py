# Databricks notebook source
# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

# MAGIC %md
# MAGIC **使用するドキュメントボリューム:**

# COMMAND ----------

user_docs_volume = f"{catalog}.{schema}.orion_docs"

print(f"✍️ サンプルドキュメントボリューム: {user_docs_volume}")