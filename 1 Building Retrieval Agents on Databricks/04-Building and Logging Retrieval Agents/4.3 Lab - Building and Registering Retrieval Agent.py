# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img
# MAGIC     src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png"
# MAGIC     alt="Databricks Learning"
# MAGIC   >
# MAGIC </div>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC # ラボ - 検索エージェントの構築と登録
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このラボでは、Databricks Mosaic AIを使用して本番運用対応の検索エージェントを構築し登録します。大規模言語モデルとVector searchインデックスを組み合わせたLangChainベースのエージェントを作成し、観測性のためのMLflowトレーシングを実装し、適切なバージョニングとエイリアスでUnity Catalogのモデルレジストリにエージェントを登録します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このラボの終了時には、以下ができるようになります：
# MAGIC
# MAGIC 1. エージェントの動作を監視するためのLangChain用MLflowトレーシングを有効にする。
# MAGIC 1. vector search統合を使用してLangChainで検索エージェントを構築する。
# MAGIC 1. エージェント実行トレースを分析してパフォーマンス特性を特定する。
# MAGIC 1. 「エージェントアズコード」パターンに従ってエージェントコードをPythonファイルに書き込む。
# MAGIC 1. エイリアス付きでUnity Catalogにエージェントモデルを登録する。
# MAGIC 1. 登録されたモデルをテストして機能を検証する。
# MAGIC
# MAGIC ## 要件
# MAGIC
# MAGIC - 事前に作成された **vector search endpoint**。これは事前に作成されています。
# MAGIC - **Serverless Compute（environment version 5）**。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC
# MAGIC
# MAGIC **📌 あなたのタスク：このラボでは、`<FILL_IN>` セクションを適切なコードで置き換えることがあなたのタスクです。**

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、教室環境を設定します。このステップにより、すべての依存関係が利用可能になり、デモ用にワークスペースが準備されます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-04 $section="lab"

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. LangChainを使用した検索エージェントの構築
# MAGIC
# MAGIC このセクションでは、**LangChain** を使用して検索エージェントを構築します。エージェントはUnity CatalogのVector searchをツールとして使用し、ユーザーの質問に答える際に動的に関連するコンテキストを取得できるようにします。
# MAGIC
# MAGIC エージェント実装をPythonファイル（`agent.py`）に書き込む **"agent as code"** アプローチに従います。これは、MLflowでモデルをログ記録する際の推奨方法です。
# MAGIC
# MAGIC **Dataset Information：** Vector searchインデックスには、Orionという名前のロボットの架空のロボット製造業者のデータが含まれています。ドキュメントには、内部設計マニュアル、コンプライアンス文書、メンテナンスガイドから取得されたコンテキストに基づく回答が含まれています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. タスク1 - MLflowトレーシングの有効化
# MAGIC
# MAGIC エージェントを構築する前に、エージェントの入力、ツールの使用、出力を詳細に観察できるように **LangChain用のMLflowトレーシングを有効にする** 必要があります。
# MAGIC
# MAGIC **your task：**
# MAGIC
# MAGIC 1. 適切な方法を使用してLangChain用のMLflow自動ログ記録を有効にします。

# COMMAND ----------

## mlflowをインポートし、LangChain用の自動ログ記録を有効にする

<FILL_IN>

# COMMAND ----------

# DBTITLE 1,タスク1 - 回答
# MAGIC %skip
# MAGIC import mlflow
# MAGIC mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. タスク2 - LangChainエージェントの作成
# MAGIC
# MAGIC 次に、vector searchリトリーバーツールを使用してOrionナレッジベースにアクセスするLangChainエージェントを作成します。
# MAGIC
# MAGIC **your task：**
# MAGIC
# MAGIC 1. LLM endpoint名を `"databricks-gpt-oss-20b"` として定義します。
# MAGIC 1. 以下により `build_agent` 関数を完成させます：
# MAGIC    * 提供されたendpointと `max_tokens=300` で `ChatDatabricks` モデルを作成する。
# MAGIC    * 以下で `VectorSearchRetrieverTool` を作成する：
# MAGIC      - `name="orion_knowledge_search_lab"`
# MAGIC      - パラメータからの `index_name`
# MAGIC      - `description="Search Orion knowledge base for relevant information"`
# MAGIC      - パラメータからの `num_results`（5結果）
# MAGIC    * 提供されたシステムプロンプトを使用する。
# MAGIC    * モデル、ツールリスト、システムプロンプト、チェックポインターで `create_agent` を使用してエージェントを作成する。
# MAGIC 1. 「Orionとは何ですか？」という質問でエージェントをテストします。

# COMMAND ----------

from langchain.agents import create_agent
from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool

llm_endpoint_name = <FILL_IN>

def build_agent(llm_endpoint:str, index_name: str, num_results: int = 3):
   model = <FILL_IN>

   vs_tool = <FILL_IN>

    ## オプション：エージェントの状態を保存するためのインメモリセーバーを使用
    checkpointer = <FILL_IN>

    system_prompt = """You are the Orion Knowledge Assistant (OKA). Respond in a clear, professional, and factual tone appropriate for engineers and technical staff. Use only verified information from Orion's internal documents, and include source references when available. If the answer cannot be found, clearly state that and suggest related sections or next steps. Do not speculate, make assumptions, or provide information outside the provided context."""

    agent = <FILL_IN>
    return agent

## 簡単なスモークテスト
agent = build_agent(llm_endpoint_name, index_name, 3)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "What is Orion?"}]}
)
print(response['messages'][-1].content)

# COMMAND ----------

# DBTITLE 1,タスク2 - 回答
# MAGIC %skip
# MAGIC from langchain.agents import create_agent
# MAGIC from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
# MAGIC
# MAGIC llm_endpoint_name = "databricks-gpt-oss-20b"
# MAGIC
# MAGIC def build_agent(llm_endpoint:str, index_name: str, num_results: int = 5):
# MAGIC     model = ChatDatabricks(
# MAGIC         endpoint=llm_endpoint,
# MAGIC         max_tokens=300,
# MAGIC     )
# MAGIC
# MAGIC     vs_tool = VectorSearchRetrieverTool(
# MAGIC         name="orion_knowledge_search_lab",
# MAGIC         index_name=index_name,
# MAGIC         description="Search Orion knowledge base for relevant information",
# MAGIC         num_results=num_results,
# MAGIC     )
# MAGIC
# MAGIC     system_prompt = """あなたはOrion Knowledge Assistant（OKA）です。エンジニアや技術スタッフに適した明確で専門的で事実に基づいたトーンで応答してください。Orionの内部文書からの検証済み情報のみを使用し、利用可能な場合はソース参照を含めてください。回答が見つからない場合は、それを明確に述べ、関連するセクションや次のステップを提案してください。推測、仮定、または提供されたコンテキスト外の情報を提供しないでください。"""
# MAGIC
# MAGIC     agent = create_agent(
# MAGIC         model=model, 
# MAGIC         tools=[vs_tool], 
# MAGIC         system_prompt=system_prompt,
# MAGIC     )
# MAGIC     return agent
# MAGIC
# MAGIC ## 簡単なスモークテスト
# MAGIC agent = build_agent(llm_endpoint_name, vs_index_name, 3)
# MAGIC
# MAGIC response = agent.invoke(
# MAGIC     {"messages": [{"role": "user", "content": "Orionとは何ですか？"}]}
# MAGIC )
# MAGIC print(response['messages'][-1].content)

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. タスク3 - MLflowトレーシングUIの確認
# MAGIC
# MAGIC MLflowトレーシングUIは、エージェントの実行とツールの使用の包括的なビューを提供します。上記の出力はトレーシングUIを示しています。
# MAGIC
# MAGIC **your task：**
# MAGIC
# MAGIC 1. 実行タイムラインで最も長いステップの名前を見つけます。
# MAGIC 1. そのステップの責任を持つツールまたはモデルを特定します。
# MAGIC 1. エージェント実行で使用されたトークンの総数（入力、出力、総トークン）を確認します。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. モデルレジストリへのエージェントのログ記録と登録
# MAGIC
# MAGIC このセクションでは、エージェントをPythonファイルに書き込み、Unity Catalogのモデルレジストリに登録することで、本番運用の準備をします。新しいものを作成する代わりに、デモノートブックの設定ファイルを使用します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. エージェントコードと設定ファイルの書き込み
# MAGIC
# MAGIC 以下のステップでは、エージェントのログ記録と登録に必要なファイルを作成します：
# MAGIC
# MAGIC - **`agent-lab.py`**: このファイルは、MLflow `pyfunc` を使用してエージェントロジックをラップし、`ResponseAgent` リクエストのサポートを可能にします。
# MAGIC - **`agent-config-lab.yaml`**: このファイルにはエージェント設定が含まれています。
# MAGIC
# MAGIC このセクションでは何も操作する必要はありません。単純にコードを実行して必要なファイルを生成してください。
# MAGIC

# COMMAND ----------

# MAGIC %%writefile agent-lab.py
# MAGIC import os
# MAGIC from typing import Any, Dict, List
# MAGIC
# MAGIC import yaml
# MAGIC import mlflow
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
# MAGIC
# MAGIC from uuid import uuid4
# MAGIC
# MAGIC from langchain.agents import create_agent
# MAGIC from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
# MAGIC
# MAGIC # YAMLファイルからエージェント設定をロード
# MAGIC def _load_config(path: str = "agent-config.yaml") -> Dict[str, Any]:
# MAGIC     if not os.path.exists(path):
# MAGIC         raise FileNotFoundError(f"Config file not found at '{path}'")
# MAGIC     with open(path, "r", encoding="utf-8") as f:
# MAGIC         cfg = yaml.safe_load(f) or {}
# MAGIC     llm_endpoint = cfg.get("llm_endpoint_name")
# MAGIC     vs = cfg.get("vector_search", {}) or {}
# MAGIC     index_name = vs.get("index_name")
# MAGIC     num_results = int(vs.get("num_results", 5))
# MAGIC     if not llm_endpoint or not index_name:
# MAGIC         raise ValueError("Missing 'llm_endpoint_name' or 'vector_search.index_name' in agent-config-lab.yaml")
# MAGIC     return {
# MAGIC         "llm_endpoint_name": llm_endpoint,
# MAGIC         "vs_index_name": index_name,
# MAGIC         "vs_num_results": num_results,
# MAGIC     }
# MAGIC
# MAGIC # LLMとベクター検索ツールでLangChainエージェントを構築
# MAGIC def build_agent(llm_endpoint: str, index_name: str, num_results: int = 5):
# MAGIC     model = ChatDatabricks(endpoint=llm_endpoint, max_tokens=300)
# MAGIC     vs_tool = VectorSearchRetrieverTool(
# MAGIC         name="orion_knowledge_search",
# MAGIC         index_name=index_name,
# MAGIC         description="Search Orion knowledge base for relevant information",
# MAGIC         num_results=num_results,
# MAGIC     )
# MAGIC
# MAGIC     system_prompt = (
# MAGIC         "You are the Orion Knowledge Assistant (OKA). Respond in a clear, professional, and factual tone "
# MAGIC         "appropriate for engineers and technical staff. Use only verified information from Orion's internal "
# MAGIC         "documents, and include source references when available. If the answer cannot be found, clearly state "
# MAGIC         "that and suggest related sections or next steps. Do not speculate, make assumptions, or provide "
# MAGIC         "information outside the provided context."
# MAGIC     )
# MAGIC     agent = create_agent(
# MAGIC         model=model,
# MAGIC         tools=[vs_tool],
# MAGIC         system_prompt=system_prompt
# MAGIC     )
# MAGIC     return agent
# MAGIC
# MAGIC # 会話から最後のユーザーメッセージを抽出
# MAGIC def _last_user_text(messages: List[Dict[str, Any]]) -> str:
# MAGIC     user_msgs = [m for m in messages if (m.get("role") == "user")]
# MAGIC     return str(user_msgs[-1].get("content", "")) if user_msgs else str(messages[-1].get("content", ""))
# MAGIC
# MAGIC # LangChainエージェント用のMLflow ResponsesAgent実装
# MAGIC class LangChainResponsesAgent(ResponsesAgent):
# MAGIC     def __init__(self):
# MAGIC         cfg = _load_config()
# MAGIC         self._cfg = cfg
# MAGIC         self._agent = build_agent(
# MAGIC             llm_endpoint=cfg["llm_endpoint_name"],
# MAGIC             index_name=cfg["vs_index_name"],
# MAGIC             num_results=cfg["vs_num_results"],
# MAGIC         )
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         msgs = [m.model_dump() for m in request.input]  # [{'role': 'user'|'assistant', 'content': '...'}, ...]
# MAGIC         _ = _last_user_text(msgs) if msgs else ""
# MAGIC
# MAGIC         result = self._agent.invoke(
# MAGIC             {"messages": msgs}
# MAGIC         )
# MAGIC         # エージェント応答テキストを抽出
# MAGIC         try:
# MAGIC             text = result["messages"][-1].content
# MAGIC         except Exception:
# MAGIC             text = str(result)
# MAGIC
# MAGIC         return ResponsesAgentResponse(
# MAGIC             output=[self.create_text_output_item(text, str(uuid4()))],
# MAGIC             custom_outputs=request.custom_inputs,
# MAGIC         )
# MAGIC
# MAGIC # mlflow用のモデルを設定。エージェントアズコードアプローチを使用する際に必要
# MAGIC AGENT = LangChainResponsesAgent()
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

import yaml

def create_config(llm_endpoint_name: str, index_name: str, num_results: int = 3):
    """Create a minimal YAML config for the agent."""
    config = {
        "llm_endpoint_name": llm_endpoint_name,
        "vector_search": {
            "index_name": index_name,
            "num_results": num_results
        }
    }
    return config


# 設定ファイルを作成
llm_endpoint_name = "databricks-gpt-oss-20b"

agent_config = create_config(llm_endpoint_name, vs_index_name)

# YAMLファイルを書き込み（後でagent.pyが読み取るため）
with open("agent-config-lab.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(agent_config, f, sort_keys=False)

print("✅ Config file written: agent-conf.yaml")
print(yaml.safe_dump(agent_config, sort_keys=False))


# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. タスク4 - エイリアス付きでUnity Catalogにエージェントモデルを登録
# MAGIC
# MAGIC 次に、Unity Catalogのモデルレジストリにエージェントモデルを登録します。これにより、ログ記録と登録が単一のワークフローに統合されます。また、登録されたモデルバージョンに **alias** も追加します。
# MAGIC
# MAGIC **your task：**
# MAGIC
# MAGIC 1. モデルリソース（vector searchインデックスとサービングendpoint）を定義します。
# MAGIC 1. 以下で `mlflow.pyfunc.log_model()` を使用してエージェントモデルをログ記録します：
# MAGIC    * モデル名： **`"orion_knowledge_assistant_lab"`**
# MAGIC    * Pythonモデル： **`"agent-lab.py"`**
# MAGIC    * コードパス： **`["agent-config-lab.yaml"]`**
# MAGIC    * UCモデルレジストリに登録するための  **model name**。
# MAGIC    * 入力例
# MAGIC    * 必要なpipパッケージ
# MAGIC    * リソース
# MAGIC 1. 登録されたモデルバージョンにエイリアスを設定します。
# MAGIC
# MAGIC **ヒント：** エイリアスの設定方法については、[MLflow モデルレジストリドキュメント](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/#use-model-aliases)を参照してください。

# COMMAND ----------

from mlflow.models.resources import DatabricksVectorSearchIndex, DatabricksServingEndpoint
from importlib.metadata import version as get_version
import mlflow

## ステップ1：リソースを定義
resources = <FILL_IN>

print("Resources defined:")
for resource in resources:
    print(f"  - {resource}")

## ステップ2：モデル設定を定義
model_name = "orion_knowledge_assistant"
tags_to_register = {
    "model_type": "retrieval_agent",
    "framework": "langchain",
    "use_case": "orion_knowledge_base"
}

input_example = {
    "input": [
        {"role": "user", "content": "What is Orion?"}
    ]
}

## ステップ3：モデルをログ記録
with mlflow.start_run():
    mlflow.set_tags(tags_to_register)
    
    logged_agent_info = <FILL_IN>
    
    model_uri = logged_agent_info.model_uri
    
print(f"✅ Model logged successfully!")
print(f"Model URI: {model_uri}")

## ステップ4：Unity Catalogにモデルを登録
mlflow.set_registry_uri("databricks-uc")
UC_MODEL_NAME = f"{catalog}.{schema}.orion_knowledge_assistant_lab"

uc_registered_model_info = <FILL_IN>

print(f"✅ Model registered successfully to Unity Catalog!")
print(f"Model Name: {UC_MODEL_NAME}")
print(f"Version: {uc_registered_model_info.version}")

## ステップ5：登録されたモデルバージョンにエイリアスを設定
## エイリアスの設定方法についてはドキュメントを参照
client = <FILL_IN>
<FILL_IN>

print(f"✅ Alias 'Champion' set for version {uc_registered_model_info.version}")

# COMMAND ----------

# DBTITLE 1,タスク4 - 回答
# MAGIC %skip
# MAGIC from mlflow.models.resources import DatabricksVectorSearchIndex, DatabricksServingEndpoint
# MAGIC from importlib.metadata import version as get_version
# MAGIC import mlflow
# MAGIC
# MAGIC # ステップ1：リソースを定義
# MAGIC resources = [
# MAGIC     DatabricksVectorSearchIndex(index_name=vs_index_name),
# MAGIC     DatabricksServingEndpoint(endpoint_name=llm_endpoint_name)
# MAGIC ]
# MAGIC
# MAGIC print("定義されたリソース：")
# MAGIC for resource in resources:
# MAGIC     print(f"  - {resource}")
# MAGIC
# MAGIC # ステップ2：モデル設定を定義
# MAGIC model_name = "orion_knowledge_assistant_lab"
# MAGIC UC_MODEL_NAME = f"{catalog}.{schema}.orion_knowledge_assistant_lab"
# MAGIC
# MAGIC input_example = {
# MAGIC     "input": [
# MAGIC         {"role": "user", "content": "Orionとは何ですか？"}
# MAGIC     ]
# MAGIC }
# MAGIC
# MAGIC # ステップ3：一つのステップでモデルをログ記録・登録
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC with mlflow.start_run():
# MAGIC     logged_agent_info = mlflow.pyfunc.log_model(
# MAGIC         name=model_name,
# MAGIC         python_model="agent-lab.py",
# MAGIC         code_paths=["agent-config-lab.yaml"],
# MAGIC         input_example=input_example,
# MAGIC         pip_requirements=[
# MAGIC             f"databricks-vectorsearch=={get_version('databricks-vectorsearch')}",
# MAGIC             f"databricks-langchain=={get_version('databricks-langchain')}",
# MAGIC             f"langchain=={get_version('langchain')}",
# MAGIC             f"mlflow=={get_version('mlflow')}",
# MAGIC         ],
# MAGIC         resources=resources,
# MAGIC         registered_model_name=UC_MODEL_NAME
# MAGIC     )
# MAGIC     model_uri = logged_agent_info.model_uri
# MAGIC     model_version = logged_agent_info.registered_model_version
# MAGIC
# MAGIC print(f"✅ モデルが正常にログ記録・登録されました！")
# MAGIC print(f"モデルURI: {model_uri}")
# MAGIC print(f"モデル名: {UC_MODEL_NAME}")
# MAGIC print(f"バージョン: {model_version}")
# MAGIC
# MAGIC # ステップ4：登録されたモデルバージョンにエイリアスを設定
# MAGIC client = mlflow.MlflowClient()
# MAGIC client.set_registered_model_alias(
# MAGIC     name=UC_MODEL_NAME,
# MAGIC     alias="Champion",
# MAGIC     version=model_version
# MAGIC )
# MAGIC
# MAGIC print(f"✅ バージョン{model_version}にエイリアス'Champion'が設定されました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 登録されたモデルのテスト
# MAGIC
# MAGIC この最後のセクションでは、登録されたモデルをテストして正しく動作することを検証します。Unity Catalogからモデルをロードし、予測を行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. タスク5 - 登録されたモデルのテスト
# MAGIC
# MAGIC エージェントがUnity Catalogに登録されたので、機能を検証するためにテストします。
# MAGIC
# MAGIC **your task：**
# MAGIC
# MAGIC 1. 前のステップのモデルURIを使用して予測を行います。
# MAGIC 1. モデルと一緒にログ記録された入力例を使用します。
# MAGIC 1. エージェントの応答を出力します。
# MAGIC

# COMMAND ----------

## 予測を行って登録されたモデルをテスト

query = <FILL_IN>

result = <FILL_IN>

print("Agent Response:")
print(result)

# COMMAND ----------

# DBTITLE 1,タスク5 - 回答
# MAGIC %skip
# MAGIC import mlflow
# MAGIC
# MAGIC query = {
# MAGIC     "input": [
# MAGIC         {"role": "user", "content": "Orionの安全手順は何ですか？"}
# MAGIC     ]
# MAGIC }
# MAGIC
# MAGIC ## モデルURIを使用して予測を行う
# MAGIC result = mlflow.models.predict(
# MAGIC     model_uri=model_uri,
# MAGIC     input_data=query,
# MAGIC     env_manager="uv",
# MAGIC )
# MAGIC
# MAGIC print("エージェントの応答：")
# MAGIC print(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. タスク6 - モデルレジストリ UIの探索
# MAGIC
# MAGIC エージェントがUnity Catalogに正常に登録されたので、モデルレジストリ UIを探索して、モデルの管理、監視、ガバナンスの方法を理解できます。
# MAGIC
# MAGIC **your tasks：**
# MAGIC
# MAGIC - モデルレジストリ UIの4つの主要なタブを特定し、その目的を説明してください。
# MAGIC - モデルと一緒にアーティファクトとしてログ記録された **model requirements file** を見つけてください。
# MAGIC - 登録されたモデルバージョンに設定した **alias** を見つけてください。
# MAGIC - エージェント呼び出しの **execution traces** を確認してください。
# MAGIC - モデルレジストリ UIが **model lifecycle management** と **governance** をどのようにサポートするかを要約してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. まとめ
# MAGIC
# MAGIC Databricks Mosaic AIを使用して本番運用対応の検索エージェントを正常に構築、ログ記録、登録しました。
# MAGIC
# MAGIC このラボでは、以下を行いました：
# MAGIC
# MAGIC * エージェントの動作と実行を監視するための **MLflowトレーシングを有効化** しました。
# MAGIC * Vector search統合を使用してLangChainで **検索エージェントを構築** しました。
# MAGIC * パフォーマンス特性を特定し実行フローを理解するための **エージェントトレースを分析** しました。
# MAGIC * 「エージェントアズコード」パターンに従って **エージェントコードをPythonファイルに書き込み** ました。
# MAGIC * 適切なバージョニングとエイリアス付きでUnity Catalogのモデルレジストリに **エージェントを登録** しました。
# MAGIC * 機能を検証するために **登録されたモデルをテスト** しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>