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
# MAGIC # デモ - タグ付けと再現可能なエージェント
# MAGIC
# MAGIC このデモンストレーションでは、本番対応のAIエージェントを構築するための高度なMLflowトレーシング技術を探求します。基礎的なトレーシング概念を基に、より良いトレース管理のためのタグ付け戦略の実装方法と、Unity Catalog登録による再現可能なエージェントの作成方法を学習します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このデモンストレーションの終了時には、以下のことができるようになります：
# MAGIC
# MAGIC - エージェントトレースを効果的に整理・管理するためのMLflowタグ付け戦略を実装する
# MAGIC - 適切な検証とエラーハンドリングを備えたカスタムトレース関数を作成する
# MAGIC - 適切な設定と依存関係を持つエージェントモデルをMLflowにログする
# MAGIC - ガバナンスと再現性のためにエージェントモデルをUnity Catalogに登録する
# MAGIC - MLflowとUnity Catalogレジストリの両方からエージェントをデプロイし、推論を実行する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境のセットアップ

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバレスコンピュートで実行するように設定されています。従来のコンピュートでも動作する可能性がありますが、テストはサーバレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバレスを使用していることを確認するには、[ノートブックのサーバレスバージョンの確認と変更に関するドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご参照ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC
# MAGIC ワークスペースのセットアップの一環として、いくつかのPythonライブラリをインストールする必要があります。次のセルを実行してインストールしてください。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-3.2

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. Airbnbデータセットの確認
# MAGIC
# MAGIC 教室のセットアップの一環として、AirbnbデータセットはUnity Catalog内のDeltaテーブルとして処理・保存されています。次のセルを実行してデータセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('sf_airbnb_listings')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. MLflowオートロギングの初期化
# MAGIC
# MAGIC MLflowのオートロギングは、LangChainなどのサポートされているframeworksのトレースを自動的にキャプチャします。有効にすると、手動でのインストルメンテーションを必要とせずに、入力、出力、パラメータ、メトリクスを記録します。

# COMMAND ----------

import mlflow

mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A5. エクスペリメント場所の定義
# MAGIC
# MAGIC アーティファクトの **デフォルト場所** を使用し、エクスペリメント場所を **ユーザー** フォルダに設定してエクスペリメントを作成します。
# MAGIC
# MAGIC > ワークスペースMLflowエクスペリメントはGitフォルダ内に作成することはできません。Git以外のワークスペースエクスペリメントを使用してください。Gitフォルダ内のノートブックでも、ノートブックエクスペリメントにログすることは可能ですが、管理に制限があります。

# COMMAND ----------

# ユーザー名を取得
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()

experiment_name = f"/Workspace/Users/{username}/single_agents_demo3" 

# COMMAND ----------

# MAGIC %md
# MAGIC ### A6. エージェントの読み込み
# MAGIC
# MAGIC MLflowオートロギングを有効にしてエージェントを初期化し、トレース収集用のエクスペリメントを設定します。教室のセットアップの一環として、セットアップスクリプトで定義されたヘルパー関数（`create_demo_agent_config`）を使用して `demo_agent1_config.json` という設定ファイルを作成しました。
# MAGIC
# MAGIC > このコースではエージェントの構築方法の詳細には触れませんが、エージェントの概念についてある程度の経験があることを前提としています。

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

import demo_agent1
agent = demo_agent1.DatabricksAgent(
    catalog_name=catalog_name,
    schema_name=schema_name
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. MLflowでのエージェントのタグ付け
# MAGIC
# MAGIC 前回のデモからの最後の例に続いて、LLMにリクエストを送信する前にユーザーの入力を検証するカスタムトレーシングを見ていきます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. タグを使う理由とは？
# MAGIC
# MAGIC タグは以下を可能にすることで、トレース管理を容易にします：
# MAGIC
# MAGIC - **Manage Sessions:** ユーザーの会話やインタラクションセッションによってトレースをグループ化
# MAGIC - **Track Environments:** 開発、ステージング、本番実行を区別
# MAGIC - **Version Models:** 各トレースを生成したモデルバージョンを特定
# MAGIC - **Add User Context:** 特定のユーザーやオーディエンスセグメントにトレースをリンク
# MAGIC - **Monitor Performance:** レイテンシやスループットメトリクスに基づいてトレースにラベルを付ける
# MAGIC - **Support A/B Testing:** 比較のために異なる実験バリアントからのトレースをマーク
# MAGIC
# MAGIC このデモンストレーションではアクティブトレースに焦点を当てますが、異なるタグタイプについては[こちら](https://mlflow.org/docs/3.2.0/genai/tracing/attach-tags/#when-to-use-trace-tags)で詳しく読むことができます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. タグの設定
# MAGIC
# MAGIC `@mlflow.trace` デコレーターコードの外でタグを設定しましょう。以下は、続く検証関数に渡すことができるタグのセットの例です。`tags` オブジェクトはキーと値のペアで構成されます。

# COMMAND ----------

tags = {
        "component": "input_validation",
        "stage": "preprocessing",
        "span_scope": "tool_function",
        "env": "dev",
        "trace_version": "v1.0.0",
        "input_type": "question"
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 必要なライブラリのインポート
# MAGIC
# MAGIC トレーシング実装に必要なライブラリを取り込みましょう。前回のデモから思い出してください。例えば、`span_type=SpanType.TOOL` は関数をトレースUI内でツールスパンとして分類し、トレースをレビューする際に異なるタイプの操作（`FUNC`、`TOOL`、`CHAIN`など）を識別しやすくします。スパンタイプについては[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/data-model#span-types)で詳しく読むことができます。

# COMMAND ----------

from mlflow.entities import SpanType

# COMMAND ----------

# MAGIC %md
# MAGIC ### B4. タグ付き検証関数の作成
# MAGIC
# MAGIC 次に、`mlflow.update_current_trace(tags)` を使用してタグを関数に渡します。これは関数定義の _内部_ で発生します。これは _アクティブトレース_ 用であることを覚えておいてください。

# COMMAND ----------

@mlflow.trace(
    span_type=SpanType.TOOL, 
    name="Validate Input"
)
def validate_input(question: str, tags: dict, min_length: int = 5):
    """Check if the user's question meets basic requirements"""
    
    mlflow.update_current_trace(tags)

    if len(question) < min_length:
        return {
            "valid": False,
            "error": f"Question too short (minimum {min_length} characters)"
        }
    if question.strip() == "":
        return {
            "valid": False,
            "error": "Question cannot be empty"
        }
    return {
        "valid": True,
        "cleaned_question": question.strip()
    }

# COMMAND ----------

@mlflow.trace(
    name="Call LLM",
    span_type=SpanType.CHAT_MODEL
)
def call_llm(question: str):
    return agent.ask(question)

# COMMAND ----------

@mlflow.trace(name="Process Question")
def process_question(user_input: str, tags: dict):
    """Main function that validates input and calls LLM"""
    # ステップ1: 入力を検証
    validation_result = validate_input(user_input, tags)
    
    # ステップ2: 有効な場合、LLMを呼び出し
    cleaned = validation_result["cleaned_question"]
    llm_response = call_llm(cleaned)
    
    return llm_response

# COMMAND ----------

# MAGIC %md
# MAGIC ### B5. タグ付きトレーシングのテスト
# MAGIC
# MAGIC プロンプトを定義し、タグ付きトレーシング実装をテストします。

# COMMAND ----------

prompt = "Can you tell me the average for Mission?"

# COMMAND ----------

# MAGIC %md
# MAGIC 上で定義したプロンプトとタグを使用して `process_question` を呼び出します。MLflowトレースUIに **tags** という追加の出力があることに注目してください。
# MAGIC
# MAGIC **手順:**
# MAGIC 1. 次のセルを実行
# MAGIC 2. **tags** をクリックして、上で定義した変数 `tags` で設定したタグを確認

# COMMAND ----------

# 有効な質問でテスト
result = process_question(prompt, tags)

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 再現可能なエージェント
# MAGIC
# MAGIC `process_question` のエージェントのトレースとタグはありますが、テストやさらなる開発のために他のチームと共有できるコードや、エージェントの適切なガバナンスはまだありません。これを2つのステップで実現します：
# MAGIC 1. エージェントをMLflowでログ
# MAGIC 2. モデルをUnity Catalogに登録

# COMMAND ----------

# MAGIC %md
# MAGIC `demo_agent_config.json` ファイルを構築するカスタム関数を使用することから始めます。これは、このラボ環境で使用している **Catalog** と **Schema** に固有である必要があります。実際には、これを動的または静的にするかは使用ケースによって異なります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. エージェント設定の読み込み
# MAGIC
# MAGIC 以下は、エージェントの設定とツールを定義する設定ファイルを出力します。

# COMMAND ----------

import json
# エージェントJSON設定ファイルを読み込み
with open('demo_agent2_config.json', 'r') as f:
    agent_config = json.load(f)
print(agent_config)

# COMMAND ----------

# MAGIC %reload_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

from demo_agent2 import AGENT

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. エージェントのMLflowへのログ
# MAGIC
# MAGIC `with mlflow.start_run` を使用して、必要なすべての依存関係と設定ファイルを含むPyFuncモデルとしてエージェントをMLflowにログします。さらに、エージェントのframework（`openai`）、開発段階（`dev`）、バージョン番号（`1`）を指定するタグ（`tags_to_register`）を追加して、他のチームによる発見可能性を高めます。これは `mlflow.set_tags(tags)` を使用して行います。
# MAGIC
# MAGIC **注意:** 次のセルでは、MLflowでのログに必要な追加モジュールを取り込んでいます：
# MAGIC 1. `pkg_resources` モジュールと `get_distribution` 関数をインポートします。この関数は実行時にPythonパッケージのインストール済みバージョンをクエリするために使用されます（この場合は `databricks-connect`）
# MAGIC 2. `mlflow.models.resources` モジュールは、`resources` で定義された指定されたリソースの自動認証パススルーを有効にします。詳細は[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#implement-automatic-authentication-passthrough)をお読みください

# COMMAND ----------

from importlib.metadata import version
from mlflow.models.resources import (
    DatabricksFunction,
    DatabricksTable,
    DatabricksServingEndpoint
)

input_example = {
    "input": [
        {
            "role": "user",
            "content": prompt
        }
    ]
}

model_name = "tagging-and-reproducible-agents"

tags_to_register = {
    "framework": "openai",
    "stage": "dev",
    "version": "1"
}

resources = [
    DatabricksFunction(function_name=agent_config["tool_list"][0]),
    DatabricksFunction(function_name=agent_config["tool_list"][1]),
    DatabricksTable(table_name=f"{catalog_name}.{schema_name}.sf_airbnb_listings"),
    DatabricksServingEndpoint(endpoint_name=agent_config["llm_endpoint"])
]

# COMMAND ----------

with mlflow.start_run():
    mlflow.set_tags(tags_to_register)
    logged_agent_info = mlflow.pyfunc.log_model(
        name=model_name,
        python_model="demo_agent2.py",
        code_paths=["demo_agent2_config.json"],
        input_example=input_example,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={version('databricks-connect')}",
        ],
        resources=resources
    )
    model_uri = logged_agent_info.model_uri # 下で使用するためにモデルURIをmodel_uriに保存

# COMMAND ----------

# MAGIC %md
# MAGIC 上記の出力には **View Logged Model at: <url>** が表示されます。URLをクリックして、モデルがMLflowにログされているが、登録されていないことを確認してください。いくつかのタグも設定されていることに注目してください（これらのタグは、このノートブックと同じフォルダにある `demo_agent2.py` ファイルで見つけて編集できます）。
# MAGIC
# MAGIC **手順:**
# MAGIC 1. クリックしたURLのランディングページで、**Runs** に移動
# MAGIC 2. そこで、**tasteful-slug-677** のようなランダムな名前の実行を見つけます。それをクリック
# MAGIC 3. これにより実行の概要ページに移動し、ページの上部に5つのタブが表示されます。**Artifacts** をクリック
# MAGIC 4. **Logged models artifacts** の下で、`tagging-and-reproducible-agents` のドロップダウンメニューをクリックします。これには、MLflowでログされたモデルを定義するさまざまなファイルがすべて含まれています。ここではすべての詳細には触れませんが、この[ドキュメント](https://docs.databricks.com/aws/en/mlflow/models)で詳しく読むことができます

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. MLflowからのエージェント推論
# MAGIC
# MAGIC MLflow実行の一環として、モデルURIを変数 `model_uri` に保存しました。モデルを読み込み、ログされた入力データを使用してエージェントで簡単な推論を実行しましょう（これは上で定義した `prompt` 変数と同じであることに注意してください）。このセルの出力を読んで、UC関数が実際に呼び出され、_"The average listing price for Airbnb properties in the Mission neighborhood is approximately $229.76."_ のような応答が返されたことを確認してください。

# COMMAND ----------

# モデルを読み込み（pyfunc flavor）
pyfunc_model = mlflow.pyfunc.load_model(model_uri)

# モデルは入力例でログされている
input_data = pyfunc_model.input_example

# ログされた依存関係を使用して提供された入力データでモデルを検証
result = mlflow.models.predict(
    model_uri=model_uri,
    input_data=input_data,
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C4. エージェントのUnity Catalogへの登録
# MAGIC
# MAGIC モデルがMLflowにログされたので、Unity Catalogに登録する時です。上でMLflowにモデルをログする際に `model_name` を定義したことを思い出してください。

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")
UC_MODEL_NAME = f"{catalog_name}.{schema_name}.{model_name}"

# モデルをUCに登録
uc_registered_model_info = mlflow.register_model(
    model_uri=model_uri, 
    name=UC_MODEL_NAME
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C5. Unity Catalogからのエージェント推論
# MAGIC
# MAGIC UCに登録されたモデルの推論は、MLflowでログされたエージェントの推論とまったく同じです。次のセルに示すように、`mlflow.set_registry_uri("databricks-uc")` を使用してURIを更新するだけです。次のセルを実行して出力を確認してください。

# COMMAND ----------

import mlflow
from mlflow.types.responses import ResponsesAgentRequest

mlflow.set_registry_uri("databricks-uc")

# モデルを読み込み（pyfunc flavor）
pyfunc_model = mlflow.pyfunc.load_model(model_uri)

# モデルは入力例でログされている
input_data = pyfunc_model.input_example

# ログされた依存関係を使用して提供された入力データでモデルを検証
result = mlflow.models.predict(
    model_uri=model_uri,
    input_data=input_data,
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C6. Unity Catalogモデルインターフェースの探索
# MAGIC
# MAGIC すべてのトレースはMLflowでログされることに注意してください。ただし、UC登録モデルのトレースは、UCのUI内でそのモデルのトレースの下に表示されます。
# MAGIC
# MAGIC **手順:**
# MAGIC モデル（ `catalog_name.schema_name.tagging-and-reproducible-agents` にあります）に移動し、モデルの最新バージョンをクリックします。そこで4つの異なるタブが見つかります：
# MAGIC
# MAGIC - **Overview**: ここでは、モデルでログされたメトリクス、アクティビティログ、モデルのシグネチャ、バージョンに関する情報、アクティブendpoints、タグが表示されます
# MAGIC - **Lineage**: この現在のノートブックが上流資産として表示されます
# MAGIC - **Artifacts**: これらはMLflowに登録されたのと同じアーティファクトです
# MAGIC - **Traces**: これらはこの特定のバージョンでキャプチャされたトレースです

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC このデモンストレーションでは、MLflowとUnity Catalogを使用して本番対応のAIエージェントを構築するための高度な技術を探求しました。以下のことを学習しました：
# MAGIC
# MAGIC - より良いトレース整理と管理のための包括的なタグ付け戦略の実装
# MAGIC - 適切なエラーハンドリングとトレース注釈を備えた堅牢な検証関数の作成
# MAGIC - 完全な設定と依存関係管理を備えたエージェントモデルのMLflowへのログ
# MAGIC - エンタープライズガバナンスと再現性のためのエージェントのUnity Catalogへの登録
# MAGIC - MLflowとUnity Catalog環境の両方からのエージェントのデプロイと推論
# MAGIC
# MAGIC これらの技術は、本番環境でスケーラブルで統制され、再現可能なAIエージェントシステムを構築するための基盤を提供します。MLflowトレーシングとUnity Catalog登録の組み合わせにより、エージェントが機能的であるだけでなく、保守可能でエンタープライズ標準に準拠していることが保証されます。
# MAGIC
# MAGIC ## 次のステップ
# MAGIC
# MAGIC 前回のデモを完了している場合は、MLflowとUnity Catalogを使用した再現可能なエージェント構築の知識と理解をテストするハンズオンラボの準備ができています。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>