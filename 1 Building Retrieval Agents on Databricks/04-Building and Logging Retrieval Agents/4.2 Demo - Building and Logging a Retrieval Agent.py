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
# MAGIC # デモ - 検索エージェントの構築とログ記録
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このデモでは、Databricks Mosaic AIを使用して本番環境対応の検索エージェントを構築し、ログ記録する方法を探ります。検索エージェントは、大規模言語モデルの力と組織のナレッジベースを組み合わせて、正確でコンテキストを理解した応答を提供します。AI PlaygroundでのVector searchのテスト、LangChainを使用したエージェントの構築、可観測性のためのMLflowトレーシングの実装、デプロイメント用のエージェントのモデル登録について説明します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC このデモの終了時には、以下のことができるようになります：
# MAGIC - 迅速なプロトタイピングのためにAI Playground UIを使用してVector search機能を **テスト** する。
# MAGIC - vector searchインデックスを使用してLangChainで検索エージェントを **構築** する。
# MAGIC - エージェントの相互作用を監視およびデバッグするためにMLflowトレーシングを **実装** する。
# MAGIC - モデルレジストリにエージェントをモデルとして **登録** する。
# MAGIC
# MAGIC ## 要件：
# MAGIC - 事前作成された **vector search endpoint**。これはあなたのために事前作成されています。
# MAGIC - **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC - LangChainと検索拡張生成（RAG）の概念に関する基本的な知識。

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、教室環境を設定します。この手順により、すべての依存関係が利用可能になり、デモ用にワークスペースが準備されます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-04 $section="demo"

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. AI PlaygroundでのVector searchのテスト
# MAGIC
# MAGIC 検索エージェントをプログラムで構築する前に、**AI Playground** を使用してVector searchインデックスをテストします。AI Playgroundは、Vector searchインデックスを実験するための **ユーザーフレンドリーなインターフェース** を提供し、ナレッジベースが正しく動作していることを迅速に検証し、検索システムが異なるクエリにどのように応答するかを理解できます。
# MAGIC
# MAGIC この対話的なテストフェーズは、検索品質の理解、埋め込みやチャンク戦略の潜在的な問題の特定、コード開発に時間を投資する前のアプローチの改良に役立ちます。
# MAGIC
# MAGIC **Dataset Information：** Vector searchインデックスには、Orionという名前のロボット用の架空のロボット製造業者のデータが含まれています。ドキュメントには、内部設計マニュアル、コンプライアンス文書、メンテナンスガイドから調達されたコンテキストに基づく回答が含まれており、技術的および規制情報の正確な検索を可能にします。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. Catalog Explorerを介してPlaygroundでVector searchを設定
# MAGIC
# MAGIC Databricksは現在、AI PlaygroundでのVector searchインデックスのテストプロセスを合理化しています。
# MAGIC
# MAGIC **Vector searchインデックスでプレイグラウンドを起動するには、以下の手順に従ってください：**
# MAGIC
# MAGIC 1. Databricks workspaceで、**Catalog Explorer** を開き、Vector searchインデックスに移動します。
# MAGIC    - 例：`{{{catalog_name}}}.{{{schema_name}}}.docs_chunked_index`
# MAGIC
# MAGIC 1. インデックス詳細ページの右上にある **Try in Playground** ボタンをクリックします。
# MAGIC
# MAGIC 1. AI Playgroundが自動的に開き、Vector searchインデックスが検索ツールとして事前設定されます。
# MAGIC
# MAGIC 1. レイグラウンドインターフェースで希望の大規模言語モデル（LLM）を選択します。`GPT OSS 120B` モデルの使用をお勧めします。
# MAGIC    * **Use Endpoint**」をクリックします。
# MAGIC
# MAGIC 1. クエリの入力を開始して、検索と応答の品質をテストします。
# MAGIC
# MAGIC **ヒント：** レイグラウンドで検索ツールを手動で追加することもできます。しかし、この方法ではVector searchが事前設定されているため時間を節約でき、LLMを選択してすぐに実験を開始できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. クエリのテストと実験
# MAGIC
# MAGIC Vector searchが設定されたので、さまざまなクエリでテストして検索品質と応答精度を評価します。
# MAGIC
# MAGIC **検索システムをテストするには、以下の手順に従ってください：**
# MAGIC
# MAGIC 1. チャットインターフェースで、ナレッジベースに関連する質問を入力します。
# MAGIC    - 例：*「Orionモーションコントローラーは高速移動中の安定性をどのように維持しますか？」*
# MAGIC    - 例：*「OrionはISO 13849-1への準拠をどのように検証しますか？」*
# MAGIC
# MAGIC 1. クエリを送信し、言語モデルからの応答を観察します。
# MAGIC
# MAGIC
# MAGIC **実験のベストプラクティス：**
# MAGIC
# MAGIC 1. **検索されたコンテキストを調べる：** どのドキュメントやチャンクが検索され、質問との関連性を確認します。
# MAGIC
# MAGIC 1. **応答品質を評価する：** 回答がナレッジベースを正確に反映し、検索されたドキュメントに基づいていることを確認します。
# MAGIC
# MAGIC 1. **エッジケースをテスト：** ナレッジベース外の質問をし、異なる表現を試してロバスト性を評価します。
# MAGIC
# MAGIC 1. **反復と改良：** 結果が悪い場合は検索パラメータを調整し、うまく機能するパターンを記録します。
# MAGIC
# MAGIC
# MAGIC プレイグラウンドでの検索品質に満足したら、次のセクションでプログラムによるエージェントの構築に進む準備ができました。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. LangChainを使用した検索エージェントの構築
# MAGIC
# MAGIC このセクションでは、このデモの範囲内にあるframeworkである **LangChain** を使用して検索エージェントを構築します。LangChainは、言語モデルを組織のデータに接続するための堅牢なツールを提供し、コンテキストを理解した応答と柔軟なエージェントworkflowsを可能にします。**ここではベストプラクティスを実証するためにLangChainを使用していますが、大規模言語モデルとVector searchをサポートする他のframeworksやライブラリでも同様の検索エージェントパターンを適用できます。** 概念とアーキテクチャは移植可能です—本番要件に最適な技術を選択してください。
# MAGIC
# MAGIC エージェントの実装をPythonファイル（`agent.py`）に書き込む **「エージェントアズコード」** アプローチに従います。これは `mlflow` でモデルをログ記録する際の推奨方法です。エージェントはUnity CatalogのVector searchをツールとして使用し、ユーザーの質問に答える際に関連するコンテキストを動的に検索できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. MLflowトレーシングの有効化
# MAGIC
# MAGIC エージェントの構築を開始する前に、**LangChain用のMLflowトレーシングを有効化** して、エージェントの入力、ツール使用、出力を詳細に観察できるようにしましょう。
# MAGIC
# MAGIC MLflowは、LangChainを含むGenAI workflowsに対して堅牢なトレーシングと可観測性を提供し、他の多くのframeworksとフレーバーもサポートしています。この幅広い統合により、多様な環境全体でGenerative AIアプリケーションを監視、デバッグ、分析できます—すべて統一されたMLflowインターフェース内で。
# MAGIC
# MAGIC **💡 注意：** MLflowトレーシング（`autolog()`）はクラシックコンピュートではデフォルトで有効になっていますが、サーバーレスコンピュートでは手動で有効にする必要があります。
# MAGIC

# COMMAND ----------

import mlflow
mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. LangChainエージェントの作成

# COMMAND ----------

llm_endpoint_name = "databricks-gpt-oss-120b"

# COMMAND ----------

from langchain.agents import create_agent
from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
from langgraph.checkpoint.memory import InMemorySaver


def build_agent(llm_endpoint:str, index_name: str, num_results: int = 3):
    model = ChatDatabricks(
        endpoint=llm_endpoint,
        max_tokens=500,
    )

    vs_tool = VectorSearchRetrieverTool(
        name="orion_knowledge_search",
        index_name=index_name,
        description="Search Orion knowledge base for relevant information",
        num_results=num_results,
    )

    # オプション：エージェントの状態を保存するためのインメモリセーバーを使用
    checkpointer = InMemorySaver()

    system_prompt = """You are the Orion Knowledge Assistant (OKA). Respond in a clear, professional, and factual tone appropriate for engineers and technical staff. Use only verified information from Orion's internal documents, and include source references when available. If the answer cannot be found, clearly state that and suggest related sections or next steps. Do not speculate, make assumptions, or provide information outside the provided context."""

    agent = create_agent(
        model=model, 
        tools=[vs_tool], 
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        )
    return agent

# `thread_id`は特定の会話の一意識別子です。
config = {"configurable": {"thread_id": "databricks-demo-4"}}

# 簡単なスモークテスト
agent = build_agent(llm_endpoint_name, vs_index_name, 3)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "What is Orion?"}]},
    config=config
)
print(response['messages'][-1].content)


# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. MLflowトレーシングUIの確認
# MAGIC
# MAGIC MLflowトレーシングUIは、エージェントの実行とツール使用の包括的なビューを提供します。上記の出力はトレーシングUIを示しています。または、以前に実行した実験のトレースを確認したい場合は、**Experiments** ページで表示できます。
# MAGIC 実験のトレースにアクセスするには、実験を選択し、実験内の **Traces** タブに移動します。
# MAGIC
# MAGIC - **Summary** タブには、各トレースの高レベル情報（入力、出力、トレースメタデータを含む）が表示されます。
# MAGIC - **Details & Timeline** タブでは、トレース内のすべてのステップの詳細が提供され、すべてのLLM呼び出し、呼び出されたツール、ツールから返された結果、最終的に生成された出力が表示されます。これにより、エージェントの推論とデータフローを理解できます。
# MAGIC - 左側で、タイムラインアイコンをクリックすると、**timeline view** の実行を有効にして各ステップの継続時間を視覚化でき、ボトルネックやパフォーマンスの問題を特定しやすくなります。
# MAGIC - 個別のトレースを選択すると、右パネルに追加の詳細が表示されます。エラーが発生した場合は、**Events** タブで検査できます。このタブには、エラーメッセージと関連するコンテキストがリストされます。
# MAGIC
# MAGIC
# MAGIC これらのタブを確認することで、エージェントの動作を検証し、問題をデバッグし、明確で実用的な洞察を使用してエージェント開発workflowsを最適化できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. モデルレジストリへのエージェントのログ記録
# MAGIC
# MAGIC このセクションでは、モデルレジストリにモデルをログ記録する方法を示します。まず、すべてのエージェントコードを含むファイルを作成して、このノートブックからエージェントコードを抽象化する必要があります。また、エージェントコードは任意の環境で実行できるため、`.yaml` 設定ファイルを作成します。これはエージェントコードと一緒にログ記録されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. `agent-config` の作成

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
llm_endpoint_name = "databricks-gpt-oss-120b"

agent_config = create_config(llm_endpoint_name, vs_index_name)

# YAMLファイルを書き込み（後でagent.pyが読み取るため）
with open("agent-config.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(agent_config, f, sort_keys=False)

print("✅ Config file written: agent-conf.yaml")
print(yaml.safe_dump(agent_config, sort_keys=False))


# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. エージェントコードをファイルに書き込み
# MAGIC
# MAGIC エージェントをログ記録する際に使用する`agent.py`ファイルを作成します。このファイルには以下が含まれます：
# MAGIC - 設定ファイルの読み込み
# MAGIC - 前のステップで作成したLangChainコード
# MAGIC - mlflow APIに基づく予測と応答形式
# MAGIC

# COMMAND ----------

# MAGIC %%writefile agent.py
# MAGIC import os
# MAGIC from uuid import uuid4
# MAGIC from typing import Any, Dict, List
# MAGIC
# MAGIC import yaml
# MAGIC import mlflow
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
# MAGIC
# MAGIC from langchain.agents import create_agent
# MAGIC from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
# MAGIC from langgraph.checkpoint.memory import InMemorySaver
# MAGIC
# MAGIC # YAMLファイルからエージェント設定を読み込み
# MAGIC def _load_config(path: str = "agent-config.yaml") -> Dict[str, Any]:
# MAGIC     if not os.path.exists(path):
# MAGIC         raise FileNotFoundError(f"Config file not found at '{path}'")
# MAGIC     with open(path, "r", encoding="utf-8") as f:
# MAGIC         cfg = yaml.safe_load(f) or {}
# MAGIC     llm_endpoint = cfg.get("llm_endpoint_name")
# MAGIC     vs = cfg.get("vector_search", {}) or {}
# MAGIC     index_name = vs.get("index_name")
# MAGIC     num_results = int(vs.get("num_results", 3))
# MAGIC     if not llm_endpoint or not index_name:
# MAGIC         raise ValueError("Missing 'llm_endpoint_name' or 'vector_search.index_name' in agent-config.yaml")
# MAGIC     return {
# MAGIC         "llm_endpoint_name": llm_endpoint,
# MAGIC         "vs_index_name": index_name,
# MAGIC         "vs_num_results": num_results,
# MAGIC     }
# MAGIC
# MAGIC # LLMとVector searchツールでLangChainエージェントを構築
# MAGIC def build_agent(llm_endpoint: str, index_name: str, num_results: int = 3):
# MAGIC     model = ChatDatabricks(endpoint=llm_endpoint, max_tokens=500)
# MAGIC     vs_tool = VectorSearchRetrieverTool(
# MAGIC         name="orion_knowledge_search",
# MAGIC         index_name=index_name,
# MAGIC         description="Search Orion knowledge base for relevant information",
# MAGIC         num_results=num_results,
# MAGIC     )
# MAGIC     checkpointer = InMemorySaver()
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
# MAGIC         system_prompt=system_prompt,
# MAGIC         checkpointer=checkpointer,
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
# MAGIC         # 各予測に対して一意のスレッドIDを生成
# MAGIC         thread_id = f"oka-{uuid4()}"
# MAGIC
# MAGIC         result = self._agent.invoke(
# MAGIC             {"messages": msgs},
# MAGIC             config={"configurable": {"thread_id": thread_id}},
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
# MAGIC # mlflow用のモデルを設定。これはエージェントアズコードアプローチを使用する際に必要
# MAGIC AGENT = LangChainResponsesAgent()
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. ファイルからエージェントをインポート

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from agent import AGENT as agent

mlflow.langchain.autolog()

response  = agent.predict(
    {"input": [{"role": "user", "content": "What is Orion?"}]}
)


# COMMAND ----------

# MAGIC %md
# MAGIC ## D. モデルレジストリへのモデルのログ記録と登録
# MAGIC
# MAGIC エージェントを読み込んでテストした後、モデルレジストリにエージェントをログ記録できます。これにより、モデルのバージョン管理、エイリアス付与、タグ付け、権限管理が可能になります。Model servingを使用してモデルレジストリからモデルをデプロイできます。なお、エージェントのデプロイメントはこのモジュールの範囲外です。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. モデルリソースの定義
# MAGIC
# MAGIC エージェントをMLflowにログ記録する前に、エージェントが依存する **resources** を定義する必要があります。リソースは、エージェントが推論時に使用するVector searchインデックス、サービングendpoints、テーブル、関数などの外部依存関係を表します。
# MAGIC
# MAGIC これらのリソースを明示的に宣言することで、MLflowは以下のことができます：
# MAGIC * 再現性とリネージのために **依存関係を追跡** する。
# MAGIC * デプロイメント前に必要なリソースの **可用性を検証** する。
# MAGIC * 本番環境での **適切な権限** とアクセス制御を有効にする。
# MAGIC
# MAGIC Orion Knowledge Assistantでは、2つの主要なリソースを定義します：
# MAGIC 1. **DatabricksVectorSearchIndex**：Orionのナレッジベースを含むVector searchインデックス。
# MAGIC 1. **DatabricksServingEndpoint**：応答生成に使用されるLLM endpoint。
# MAGIC
# MAGIC これらのリソースにより、モデルがデプロイされた際に必要なインフラストラクチャコンポーネントにアクセスできることが保証されます。
# MAGIC
# MAGIC **🚨 重要：** 続行する前に、教室セットアップ設定ファイルをインポートしていることを確認してください。前のセクションでPythonカーネルが再起動されたため、正しいリソース設定のためにカタログとスキーマ名を再読み込みする必要があります。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-Common

# COMMAND ----------

# DBTITLE 1,エージェントリソースの定義
from mlflow.models.resources import DatabricksVectorSearchIndex, DatabricksServingEndpoint

# Python再起動後の変数再定義
vs_index_name = f"{catalog}.{schema}.docs_chunked_index"
llm_endpoint_name = "databricks-gpt-oss-120b"

# エージェントが依存するリソースを定義
resources = [
    DatabricksVectorSearchIndex(index_name=vs_index_name),
    DatabricksServingEndpoint(endpoint_name=llm_endpoint_name)
]

print("Resources defined:")
for resource in resources:
    print(f"  - {resource}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. MLflowでエージェントモデルをログ記録
# MAGIC
# MAGIC エージェントのリソースを定義したので、MLflowを使用して **エージェントをモデルとしてログ記録** します。ログ記録により、エージェントコード、設定、依存関係、メタデータがバージョン管理、追跡、デプロイ可能な構造化形式でキャプチャされます。
# MAGIC
# MAGIC MLflowでモデルをログ記録すると、以下を記録する **実行** が作成されます：
# MAGIC * **Model artifacts**：エージェントコード（`agent.py`）と設定（`agent-config.yaml`）。
# MAGIC * **Dependencies**：エージェントを実行するために必要なPythonパッケージ。
# MAGIC * **Resources**：Vector searchインデックスやサービングendpointなどの外部依存関係。
# MAGIC * **Input/output examples**：期待されるモデルインターフェースを実証するサンプルデータ。
# MAGIC * **Metadata and tags**：モデルバージョン、目的、リネージに関する情報。
# MAGIC
# MAGIC このログ記録されたモデルは、同じ依存関係とリソースが利用可能な任意の環境で読み込み、テスト、デプロイできる **再現可能なアーティファクト** になります。

# COMMAND ----------

# DBTITLE 1,MLflowにエージェントモデルをログ記録
import mlflow
from importlib.metadata import version as get_version

# モデル名とタグを定義
model_name = "orion_knowledge_assistant"
tags_to_register = {
    "model_type": "retrieval_agent",
    "framework": "langchain",
    "use_case": "orion_knowledge_base"
}

# モデルシグネチャ用の入力例を作成
input_example = {
    "input": [
        {"role": "user", "content": "What is Orion?"}
    ]
}

# MLflow実行を開始してモデルをログ記録
with mlflow.start_run():
    mlflow.set_tags(tags_to_register)
    
    logged_agent_info = mlflow.pyfunc.log_model(
        name=model_name,
        python_model="agent.py",
        code_paths=["agent-config.yaml"],
        input_example=input_example,
        pip_requirements=[
            f"databricks-vectorsearch=={get_version('databricks-vectorsearch')}",
            f"databricks-langchain=={get_version('databricks-langchain')}",
            f"langchain=={get_version('langchain')}",
            f"mlflow=={get_version('mlflow')}",
        ],
        resources=resources
    )
    
    # 後で使用するためにモデルURIを保存
    model_uri = logged_agent_info.model_uri
    
print(f"✅ Model logged successfully!")
print(f"Model URI: {model_uri}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. Unity Catalogへのモデル登録
# MAGIC
# MAGIC エージェントモデルをログ記録したので、**Unity Catalogのモデルレジストリに登録** します。ログ記録と登録は似ているように見えるかもしれませんが、MLOpsライフサイクルにおいて異なる目的を果たします。
# MAGIC
# MAGIC **違いの理解：**
# MAGIC
# MAGIC * **Logging** は、MLflow実験実行内でバージョン管理されたアーティファクトを作成します。特定の時点でのモデルコード、依存関係、メタデータをキャプチャします。ログ記録されたモデルは個別の実行に関連付けられ、主に実験と開発に使用されます。
# MAGIC
# MAGIC * **Registering** は、ログ記録されたモデルをモデルレジストリに昇格させ、Unity Catalogで一意の名前を持つ **管理された、ガバナンスされた資産** にします。登録されたモデルは以下をサポートします：
# MAGIC   - **Version management**：同じモデルの複数のバージョンを追跡。
# MAGIC   - **Aliases**：特定のバージョンに `Champion` や `Challenger` などのラベルを割り当て。
# MAGIC   - **Governance**：権限、タグ、リネージ追跡を適用。
# MAGIC   - **Deployment**：レジストリから本番endpointsに直接モデルを提供。
# MAGIC
# MAGIC エージェントをUnity Catalogに登録することで、実験的なアーティファクトから組織全体で発見、ガバナンス、デプロイ可能な本番対応資産に変換されます。

# COMMAND ----------

# DBTITLE 1,Unity Catalogにモデルを登録
# レジストリURIをUnity Catalogに設定
mlflow.set_registry_uri("databricks-uc")

# Unity Catalogでの完全修飾モデル名を定義
UC_MODEL_NAME = f"{catalog}.{schema}.orion_knowledge_assistant"

# Unity Catalogにモデルを登録
uc_registered_model_info = mlflow.register_model(
    model_uri=model_uri, 
    name=UC_MODEL_NAME
)

print(f"✅ Model registered successfully to Unity Catalog!")
print(f"Model Name: {UC_MODEL_NAME}")
print(f"Version: {uc_registered_model_info.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. モデル推論のテスト
# MAGIC
# MAGIC エージェントがUnity Catalogに登録されたので、**読み込んでテスト** して正しく動作することを確認できます。レジストリからモデルを読み込むことで、すべての依存関係と設定がそのまま残っているログ記録された正確なバージョンを使用していることが保証されます。
# MAGIC
# MAGIC 2つのアプローチを実証します：
# MAGIC 1. **モデルURIからの読み込み**：ログ記録ステップからのURIを使用。
# MAGIC 1. **Unity Catalogからの読み込み**：完全修飾モデル名を使用。
# MAGIC
# MAGIC 両方の方法により、テスト入力でエージェントを呼び出し、Vector searchインデックスから関連するコンテキストを検索し、適切な応答を生成することを検証できます。

# COMMAND ----------

# DBTITLE 1,モデルの読み込みとテスト
# モデルURI（pyfuncフレーバー）からモデルを読み込み
pyfunc_model = mlflow.pyfunc.load_model(model_uri)

# モデルと一緒にログ記録された入力例を使用
input_data = pyfunc_model.input_example

print("Input data:")
print(input_data)
print("\n" + "="*50 + "\n")

# 読み込まれたモデルを使用して予測を実行
result = mlflow.models.predict(
    model_uri=model_uri,
    input_data=input_data,
    env_manager="uv",
)

print("Agent Response:")
print(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D5. モデルレジストリ UIの探索
# MAGIC
# MAGIC エージェントがUnity Catalogに正常に登録されたので、**モデルレジストリ UIを探索** してモデルの管理、監視、ガバナンス方法を理解できます。モデルレジストリは、モデルバージョン、リネージ、アーティファクト、パフォーマンスを追跡するための集中インターフェースを提供します。
# MAGIC
# MAGIC **登録されたモデルを探索するには、以下の手順に従ってください：**
# MAGIC
# MAGIC 1. Catalog Explorerでモデルに移動します：
# MAGIC    - Databricks workspaceの **Catalog Explorer** に移動します。
# MAGIC    - `{{{catalog_name}}}.{{{schema_name}}}.orion_knowledge_assistant` に移動します。
# MAGIC    - モデルの最新バージョンをクリックします。
# MAGIC
# MAGIC 1. 4つの主要なタブを探索します：
# MAGIC
# MAGIC    * **Overview**：このタブには、モデルバージョンに関する重要な情報が表示されます：
# MAGIC      - **Metrics**：トレーニングや評価中にモデルと一緒にログ記録されたメトリクス。
# MAGIC      - **Activity Log**：変更、更新、デプロイメントの時系列記録。
# MAGIC      - **Model Signature**：期待されるデータ形式を定義する入力/出力スキーマ。
# MAGIC      - **Version Information**：作成日と作成者を含む、この特定のバージョンの詳細。
# MAGIC      - **Active Endpoints**：現在このモデルバージョンを使用しているサービングendpoints。
# MAGIC      - **Tags**：組織と発見のためのカスタムメタデータタグ。
# MAGIC
# MAGIC    * **Lineage**：モデルバージョン追跡のための上流ソースと下流コンシューマーを表示。
# MAGIC
# MAGIC    * **Artifacts**：モデルに登録されたすべてのファイルと依存関係をリスト。
# MAGIC
# MAGIC    * **Traces**：エージェント呼び出しとデバッグのための詳細な実行トレースを表示。
# MAGIC
# MAGIC モデルレジストリ UIは、モデルのライフサイクルの包括的なビューを提供し、バージョン管理、リネージ追跡、組織全体でのガバナンスの確保を容易にします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. まとめ
# MAGIC
# MAGIC このデモでは、Databricks Mosaic AIを使用して本番対応の **retrieval agent** を構築、ログ記録、登録するための完全なワークフローを探索しました。**AI PlaygroundでのVector searchのテスト** から始まり、LLMをVector Searchに保存されたナレッジベースと組み合わせてコンテキストを理解した応答を提供するLangChainベースのエージェントを構築しました。可観測性のために **MLflow Tracing** を活用し、PythonファイルとYAML設定による **"agent as  code"** アプローチを採用し、明示的な **resource dependencies** でエージェントをMLflowにログ記録しました。最後に、エージェントをUnity Catalogのモデルレジストリに登録し、**ガバナンスされた、バージョン管理された本番デプロイメント対応の資産** に変換しました。
# MAGIC
# MAGIC **主要な要点：**
# MAGIC
# MAGIC * コードを書く前に **AI Playground** で **Vector searchインデックスをテスト** して、検索品質と応答精度を検証する。
# MAGIC * **MLflowトレーシングを有効化** して、ツール使用、LLM呼び出し、応答生成を含むエージェントの動作を監視する。
# MAGIC * 移植性と保守性のために **Python files** と **YAML configuratoin** による **「エージェントアズコード」アプローチを採用** する。
# MAGIC * **MLflow** にモデルをログ記録する際に **明示的なリソース依存関係**（Vector searchインデックス、サービングendpoints）を定義する。
# MAGIC * バージョン管理、ガバナンス、リネージ追跡、本番デプロイメントを可能にするために **Unity Catalogのモデルレジストリにモデルを登録** する。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>