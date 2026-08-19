# Databricks notebook source
# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

# MAGIC %md
# MAGIC **Serverlessの確認**

# COMMAND ----------

if not is_serverless_5():
    raise EnvironmentError("⛔️ エラー: このノートブックはDatabricks Serverless 5環境で実行する必要があります。コンピュートをServerless 5に切り替えて再試行してください。")
else:
    print("✅ 環境チェック成功: Serverless 5が検出されました。")

# COMMAND ----------

# MAGIC %md
# MAGIC **Vector Searchエンドポイントの準備状況確認**

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

def check_vector_search_endpoint(endpoint_name: str):
    vsc = VectorSearchClient(disable_notice=True)
    try:
        endpoint = vsc.get_endpoint(endpoint_name)
    except Exception as e:
        raise RuntimeError(f"⛔️ エラー: Vector searchエンドポイント '{endpoint_name}' が存在しません。詳細: {e}")
    status = endpoint.get("endpoint_status", {}).get("state", "")
    if status != "ONLINE":
        raise RuntimeError(f"⛔️ エラー: Vector searchエンドポイント '{endpoint_name}' は存在しますが、準備ができていません。")
    print(f"✅ Vector searchエンドポイント '{endpoint_name}' が存在し、準備ができています。")

vs_endpoint_name = "vs_endpoint_1"
check_vector_search_endpoint(vs_endpoint_name)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC **Vector Searchインデックスの存在確認**

# COMMAND ----------

section = dbutils.widgets.get("section") or "lab"

if(section == "lab"):
    vs_index_name = f"{catalog}.{schema}.docs_chunked_lab_index"
else:
    vs_index_name = f"{catalog}.{schema}.docs_chunked_index"

vsc = VectorSearchClient(disable_notice=True)
try:
    vsc.get_index(vs_endpoint_name, vs_index_name)
    print(f"✅ Vector searchインデックス '{vs_index_name}' が存在し、準備ができています。")
except Exception as e:
    raise RuntimeError(f"⛔️ エラー: Vector searchインデックス '{vs_index_name}' が存在しません。これは前のデモで作成されているはずです。前のデモを実行していることを確認してください。詳細: {e}")