# Databricks notebook source
# MAGIC %run ./Classroom-Setup-Common

# COMMAND ----------

# MAGIC %md
# MAGIC **サーバーレスの確認**

# COMMAND ----------

if not is_serverless_5():
    raise EnvironmentError("⛔️ エラー: このノートブックはDatabricks Serverless 5環境で実行する必要があります。コンピュートをServerless 5に切り替えて再試行してください。")
else:
    print("✅ 環境チェック成功: Serverless 5が検出されました。")

# COMMAND ----------

# MAGIC %md
# MAGIC **Vector Searchエンドポイントの準備状況を確認**

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
    
    print("✅ Vector Searchエンドポイントの準備ができています。 ")
    print(f"\n✍️ 使用するVector Searchエンドポイント: {endpoint_name}")

vector_search_endpoint = "vs_endpoint_1"
check_vector_search_endpoint(vector_search_endpoint)

# COMMAND ----------

docs_table = f"{catalog}.{schema}.docs_chunked"