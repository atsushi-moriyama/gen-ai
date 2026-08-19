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
# MAGIC # Databricks Model Servingへの LLM チェーンのデプロイ
# MAGIC
# MAGIC **このデモでは、リアルタイムでの GenAI モデルのデプロイとクエリに焦点を当てます。**
# MAGIC
# MAGIC デプロイは、LLM ベースのアプリケーションを運用する上で重要な部分です。 Databricks 内のデプロイオプションを検討し、それぞれのデプロイ方法を紹介します。
# MAGIC
# MAGIC **学習目標:**
# MAGIC
# MAGIC *このデモを終了すると、あなたは以下を可能にすることができます:*
# MAGIC
# MAGIC * ユースケースに適した展開戦略を決定します。
# MAGIC * カスタム RAG チェーンを Databricks Model Servingのエンドポイントにデプロイする。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必要条件
# MAGIC
# MAGIC レッスンを開始する前に、次の要件を確認してください。
# MAGIC
# MAGIC * このノートブックを実行するには、次のいずれかの Databricks Runtime を使用する必要があります。 **`17.3.x-cpu-ml-scala2.13`**
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ** 前提条件:** このノートブックには **[00-Build-Model]($../00-Build-Model/00-Build-Model)** が必要で、このデモで使用するモデルを作成します。 Databricks が提供するラボ環境では、これはクラスの前に実行されるため、**手動で実行する必要はありません**。  
# MAGIC
# MAGIC このスクリプトは、Databricks Vector Search や Vector Search Index などの RAGアプリケーションを設定しますが、現時点では完了するまでに ~1 時間かかることがあります。 Vector searchとそれに付随するインデックスがワークスペースにすでに作成されている場合は、それらが使用されます。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 学習環境のセットアップ
# MAGIC
# MAGIC 必要なライブラリをインストールします。

# COMMAND ----------

# MAGIC %pip install -U --quiet databricks-sdk databricks-agents

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC デモを開始する前に、提供されているクラスルーム セットアップ スクリプトを実行します。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-02

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の規則:**
# MAGIC
# MAGIC このデモでは、 `DA`オブジェクトを参照します。 Databricks Academy が提供するこのオブジェクトには、ユーザー名、カタログ名、スキーマ名、作業ディレクトリ、データセットの場所などの変数が含まれています。 以下のコードブロックを実行して、これらの詳細を表示してください。

# COMMAND ----------

print(f"Username:          {DA.username}")
print(f"Catalog Name:      {DA.catalog_name}")
print(f"Schema Name:       {DA.schema_name}")
print(f"Working Directory: {DA.paths.working_dir}")
print(f"Dataset Location:  {DA.paths.datasets}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## デモの概要
# MAGIC
# MAGIC このデモでは、Databricks の基本的なリアルタイムデプロイ機能について説明します。 Model servingでは、モデルをデプロイし、さまざまな方法でクエリを実行できます。 
# MAGIC
# MAGIC このデモでは、次の手順でこれについて説明します。
# MAGIC
# MAGIC 1. デプロイするモデルを準備します。
# MAGIC
# MAGIC 1. 登録したモデルを Databricks model servingエンドポイントにデプロイします。
# MAGIC
# MAGIC 1.  `python sdk` および `mlflow deployments`などのさまざまな方法を使用してエンドポイントをクエリします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## モデルの準備
# MAGIC
# MAGIC これを行うときは、まずモデルを作成する必要があります。
# MAGIC
# MAGIC このレッスンのセットアップの一環として RAG モデルを作成し、ガバナンスの目的とmodel servingへのデプロイを容易にするために Unity Catalog に記録しました。
# MAGIC
# MAGIC ここです： **'genai_shared_catalog.ws_<xxxxx>.rag_app'** です。 次のコードを実行して、モデルの詳細を表示します。

# COMMAND ----------

shared_schema_name = f"ws_{spark.conf.get('spark.databricks.clusterUsageTags.clusterOwnerOrgId')}"
model_name = f"genai_shared_catalog_04.{shared_schema_name}.rag_app"
print(f"Pre-created model: {model_name}")

# COMMAND ----------

import mlflow
from mlflow import MlflowClient

# UCレジストリを指す
mlflow.set_registry_uri("databricks-uc")

def get_latest_model_version(model_name_in:str = None):
    """
    Get latest version of registered model
    """
    client = MlflowClient()
    model_version_infos = client.search_model_versions("name = '%s'" % model_name_in)
    if model_version_infos:
      return max([model_version_info.version for model_version_info in model_version_infos])
    else:
      return None

# COMMAND ----------

latest_model_version = get_latest_model_version(model_name)

if latest_model_version:
  print(f"Model created and logged to: {model_name}/{latest_model_version}")
else:
  raise(BaseException("Error: Model not created, verify if 00-Build-Model script ran successfully!"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## カスタムモデルをModel servingにデプロイする
# MAGIC
# MAGIC カスタムモデルが Unity Catalog に取り込まれた後のデプロイは、Unity Catalog に取り込まれた後の外部モデルに対して示したワークフローと似ています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 前提条件: シークレットの設定
# MAGIC
# MAGIC サービス エンドポイントへのアクセスをセキュリティで保護するには、ホスト (ワークスペース URL) と個人用アクセス トークンの 2 つのシークレットを設定する必要があります。 このデモでは、これは クラスルームのセットアップ ファイルで行われます。
# MAGIC
# MAGIC シークレットは、Databricks CLI で次のコマンドを使用して設定できます。
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC ```
# MAGIC databricks secrets create-scope <scope-name>
# MAGIC databricks secrets put-secret --json '{
# MAGIC   "scope": "<scope-name>",
# MAGIC   "key": "<key-name>",    
# MAGIC   "string_value": "<value>"
# MAGIC }' 
# MAGIC ```
# MAGIC
# MAGIC だから、この例では、我々は実行した:
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC ```
# MAGIC databricks secrets create-scope <scope-name>
# MAGIC databricks secrets put-secret --json '{
# MAGIC   "scope": "genai_training",
# MAGIC   "key": "depl_demo_host",    
# MAGIC   "string_value": "<host-name>"
# MAGIC }'
# MAGIC databricks secrets put-secret --json '{
# MAGIC   "scope": "genai_training",
# MAGIC   "key": "depl_demo_token",    
# MAGIC   "string_value": "<token_value>"
# MAGIC }' 
# MAGIC ```
# MAGIC
# MAGIC これを設定したら、Databricks のシークレットユーティリティを使用して、ノートブックの変数に値を読み込みます。

# COMMAND ----------

# MAGIC %md
# MAGIC ###  `databricks-sdk` APIを使用してモデルをデプロイ
# MAGIC
# MAGIC ノートブックでは、APIを使用してエンドポイントを作成し、モデルをサービングします。 
# MAGIC
# MAGIC **注 :** このタスクには、単に UI を使用することもできます。
# MAGIC
# MAGIC **⏰ 予想されるデプロイ時間:** ~10分

# COMMAND ----------

from databricks.sdk.service.serving import EndpointCoreConfigInput

# Configure the endpoint
endpoint_config_dict = {
    "served_models": [
        {
            "model_name": model_name,
            "model_version": latest_model_version,
            "scale_to_zero_enabled": True,
            "workload_size": "Small",
            "environment_vars": {
                "DATABRICKS_TOKEN": "{{{{secrets/{0}/depl_demo_token}}}}".format(DA.scope_name),
                "DATABRICKS_HOST": "{{{{secrets/{0}/depl_demo_host}}}}".format(DA.scope_name)
            },
            
        },
    ]
}

endpoint_config = EndpointCoreConfigInput.from_dict(endpoint_config_dict)

# COMMAND ----------

# MAGIC %md
# MAGIC **重要:** 上記の認証の構文設定に注意してください。 シークレット変数を直接渡すのではなく、構文要件に従います **&lcub;&lcub;secrets/&lt;scope&gt;/&lt;key-name&gt;&rcub;&rcub;** を使用して、エンドポイントが静的な値を自動的に構成して公開するのではなく、リアルタイムでシークレットを検索するようにします。

# COMMAND ----------

from databricks.sdk import WorkspaceClient


# ワークスペースクライアントの起動
w = WorkspaceClient()
serving_endpoint_name = f"{DA.unique_name('_')}_endpoint"

# エンドポイントが存在する場合は取得
existing_endpoint = next(
    (e for e in w.serving_endpoints.list() if e.name == serving_endpoint_name), None
)

db_host = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("browserHostName").value()
serving_endpoint_url = f"{db_host}/ml/endpoints/{serving_endpoint_name}"

# エンドポイントが存在しない場合は作成する
if existing_endpoint == None:
    print(f"Creating the endpoint {serving_endpoint_url}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.create_and_wait(name=serving_endpoint_name, config=endpoint_config)

#エンドポイントが存在する場合は、新しいバージョンを提供するように更新します
else:
    print(f"Updating the endpoint {serving_endpoint_url} to version {latest_model_version}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.update_config_and_wait(served_models=endpoint_config.served_models, name=serving_endpoint_name)

displayHTML(f'Your Model Endpoint Serving is now available. Open the <a href="/ml/endpoints/{serving_endpoint_name}">Model Serving Endpoint page</a> for more details.')

# COMMAND ----------

# MAGIC %md
# MAGIC このモデルは、mlflow の [deploy_client](https://mlflow.org/docs/latest/python_api/mlflow.deployments.html) を使用してプログラムでデプロイすることもできます。
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC from mlflow.deployments import get_deploy_client
# MAGIC
# MAGIC
# MAGIC deploy_client = get_deploy_client("databricks")
# MAGIC endpoint = deploy_client.create_endpoint(
# MAGIC     name=serving_endpoint_name,
# MAGIC     config=endpoint_config
# MAGIC )
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### (方法 2) - Model Serving UI を使用した推論テーブルの作成
# MAGIC
# MAGIC
# MAGIC エンドポイントが既に稼働している場合は、Model Serving エンドポイント ページに移動し、推論テーブル フィールドを表示することで、推論テーブルがまだ設定されていないかどうかを確認できます。
# MAGIC
# MAGIC この推論テーブルを手動で設定するには、次の手順に従います。
# MAGIC
# MAGIC 1. [Serving](/ml/endpoints)に移動します。
# MAGIC
# MAGIC 1. 作成したエンドポイントを見つけて、エンドポイント ページの **[編集]** ボタンをクリックします。 
# MAGIC
# MAGIC 1. **推論テーブル** セクションを展開します。
# MAGIC
# MAGIC 1. **推論テーブルを有効にする** チェックボックスをオンにします。
# MAGIC
# MAGIC 1. 推論テーブルのカタログ、スキーマ、およびテーブル情報を入力する。
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC ![genai-as-04-enable-inference-table](../Includes/images/genai-as-04-enable-inference-table)
# MAGIC **注:** 推論テーブルを設定するには、Databricks シークレットを使用してエンドポイントを構成する必要がある。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## モデルに対して推論を実行する
# MAGIC
# MAGIC 次に、モデルを使用して推論を実行する、つまり、入力を提供し、出力を返す。
# MAGIC
# MAGIC まず、1 つの入力の簡単な例から始めます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### SDKを使用した推論

# COMMAND ----------

from databricks.sdk.service.serving import ChatMessage

messages = {"messages" : [
        {"role": "user", "content": "What is PPO?"}
    ]}

answer = w.serving_endpoints.query(
  serving_endpoint_name, 
  inputs=messages
)

print(answer.predictions)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 推論テーブルの表示
# MAGIC
# MAGIC テーブルが作成され、エンドポイントが数回ヒットしたら、「カタログエクスプローラー」でテーブルをビューして、保存されたクエリーデータを検査できます。
# MAGIC
# MAGIC 推論テーブルをビューするには、次のようにします。
# MAGIC
# MAGIC 1. **[カタログ](explore/data)** に移動します。
# MAGIC
# MAGIC 1. 前のステップで推論テーブルの構成時に入力したカタログとスキーマを選択します。
# MAGIC
# MAGIC 1. 推論テーブルを選択し、サンプル データを表示します。 
# MAGIC
# MAGIC **注:** モニタリングデータが表示されるまでに数分かかる場合があります。
# MAGIC
# MAGIC <br/>
# MAGIC
# MAGIC ![genai-as-04-realtime-inference-table](../Includes/images/genai-as-04-realtime-inference-table.png)
# MAGIC <br/>
# MAGIC
# MAGIC **注:** テーブルをクエリしてデータを直接表示することもできます。 これは、何らかの方法でデータをアプリケーションに組み込む場合に役立ちます(たとえば、テスト戦略を決定するために人間のフィードバックを使用するなど)。
# MAGIC
# MAGIC **質問:** 推論テーブルにはどのようなデータが表示されますか?

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## まとめ
# MAGIC
# MAGIC このデモでは、Databricks Model Serving を使用して RAG パイプラインをリアルタイムでデプロイする方法を紹介しました。 モデルが作成され、モデル レジストリに登録され、使用できる状態になりました。 まず、SDK を使用してモデルをmodel servingエンドポイントにデプロイしました。 次に、エンドポイントを構成し、推論テーブルを有効にしました。 最後に、SDK と MLflow のデプロイを使用してエンドポイントにリアルタイムでクエリを実行する方法を示しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>