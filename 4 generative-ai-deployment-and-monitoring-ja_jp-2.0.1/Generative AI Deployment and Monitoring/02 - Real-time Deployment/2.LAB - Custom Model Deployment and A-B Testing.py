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
# MAGIC # ラボ: カスタムモデルのデプロイとA/Bテスト 
# MAGIC
# MAGIC このラボでは、Databricks Model servingを使用してカスタムモデルをデプロイして提供する方法を学習します。 Databricks でのモデルエンドポイントの準備、デプロイ、クエリーに関連するステップを理解します。 このラボでは、カスタム モデルをデプロイし、リアルタイム推論のためにクエリを実行する実践的な側面に焦点を当てます。
# MAGIC
# MAGIC
# MAGIC **ラボの概要:**
# MAGIC
# MAGIC このラボでは、次のタスクを完了する必要があります。
# MAGIC
# MAGIC 1. **タスク 1:** モデル バージョンの取得
# MAGIC 1. **タスク 2:** SDK を使用したモデルのデプロイ
# MAGIC 1. **タスク 3:** UI を使用した A/B テストの構成
# MAGIC 1. **タスク 4:** エンドポイントのクエリー
# MAGIC 1. **タスク 5:** 推論テーブルの検査

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 必要条件
# MAGIC
# MAGIC レッスンを開始する前に、次の要件を確認してください。
# MAGIC
# MAGIC * このノートブックを実行するには、次のいずれかの Databricks Runtime を使用する必要があります。 **`17.3.x-cpu-ml-scala2.13`**

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## 学習環境のセットアップ
# MAGIC
# MAGIC 必要なライブラリをインストールします。

# COMMAND ----------

# MAGIC %pip install -U -qq databricks-sdk

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ラボを開始する前に、用意されているクラスルーム設定スクリプトを実行しましょう。 このスクリプトでは、ラボに必要な構成変数を定義します。 次のセルを実行しましょう。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-02

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の慣習:**
# MAGIC
# MAGIC このラボでは、オブジェクト`DA`を参照します。 Databricks Academy が提供するこのオブジェクトには、ユーザー名、カタログ名、スキーマ名、作業ディレクトリ、データセットの場所などの変数が含まれています。 以下のコードブロックを実行して、これらの詳細を表示してください。

# COMMAND ----------

print(f"Username:          {DA.username}")
print(f"Catalog Name:      {DA.catalog_name}")
print(f"Schema Name:       {DA.schema_name}")
print(f"Working Directory: {DA.paths.working_dir}")
print(f"Dataset Location:  {DA.paths.datasets}")

# COMMAND ----------

# MAGIC %md
# MAGIC ##モデル詳細
# MAGIC モデルは **00-Model-Build** ノートブックで作成されます。 これは、ガバナンスの目的とModel Servingへのデプロイを容易にするために Unity Catalog に登録されます。
# MAGIC
# MAGIC モデルの場所: `genai_shared_catalog.ws_<xxxx>.rag_app`

# COMMAND ----------

shared_schema_name = f"ws_{spark.conf.get('spark.databricks.clusterUsageTags.clusterOwnerOrgId')}"
model_name = f"genai_shared_catalog_04.{shared_schema_name}.rag_app"
print(f"Model name: {model_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## タスク 1: モデルバージョンの取得
# MAGIC
# MAGIC このタスクでは、モデル レジストリからモデルの詳細とバージョンを取得します。 これは、デプロイするモデルの最新バージョンを特定するのに役立ちます。

# COMMAND ----------

##
import mlflow
from mlflow import MlflowClient

## レジストリ URI を Unity Catalog に設定する
mlflow.set_registry_uri("databricks-uc")

## MLflow クライアントの初期化
client = MlflowClient()

## 指定したモデルの最新バージョンを取得する
model_version_infos = client.<FILL_IN>
latest_model_version = <FILL_IN>

## 最新のモデルバージョンを表示する
<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC import mlflow
# MAGIC from mlflow import MlflowClient
# MAGIC
# MAGIC ## レジストリ URI を Unity Catalog に設定する
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC
# MAGIC ## MLflow クライアントの初期化
# MAGIC client = MlflowClient()
# MAGIC
# MAGIC ## 指定したモデルの最新バージョンを取得する
# MAGIC model_version_infos = client.search_model_versions("name = '%s'" % model_name)
# MAGIC if model_version_infos:
# MAGIC     latest_model_version = max([model_version_info.version for model_version_info in model_version_infos])
# MAGIC else:
# MAGIC     raise(BaseException("Error: Model not created, verify if 00-Build-Model script ran successfully!"))
# MAGIC
# MAGIC ## 最新のモデルバージョンを表示する
# MAGIC print(f"Latest model version: {latest_model_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 2: SDK を使用してモデルをデプロイ
# MAGIC
# MAGIC このタスクでは、SDK を使用してモデルをデプロイし、推論テーブルを有効にします。 これには、環境変数の定義、エンドポイントの構成、推論テーブルの設定が含まれます。
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ###2.1: シークレットの設定
# MAGIC
# MAGIC
# MAGIC サービス エンドポイントへのアクセスをセキュリティで保護するには、ホストのシークレット (ワークスペース URL) と個人用アクセス トークンを設定します。 これは、Databricks CLI を使用して実行できます。
# MAGIC
# MAGIC
# MAGIC ```
# MAGIC databricks secrets create-scope <scope-name>
# MAGIC databricks secrets put-secret --json '{
# MAGIC   "scope": "<scope-name>",
# MAGIC   "key": "<key-name>",
# MAGIC   "string_value": "<value>"
# MAGIC }'
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC **重要:** 上記の認証の構文設定に注意してください。 シークレット変数を直接渡すのではなく、構文要件に従います **&lcub;&lcub;secrets/&lt;scope&gt;/&lt;key-name&gt;&rcub;&rcub;** を使用して、エンドポイントが静的な値を自動的に構成して公開するのではなく、リアルタイムでシークレットを検索するようにします。
# MAGIC
# MAGIC **シークレット値を出力するには:**

# COMMAND ----------

## スコープ, トークンのキー, ホスト のキー の値を出力
print("Scope: ", DA.scope_name)
print("Key for Token: depl_demo_token")
print("Key for Host: depl_demo_host")

# COMMAND ----------

# MAGIC %md
# MAGIC ###2.2: エンドポイントの構成とデプロイ
# MAGIC
# MAGIC エンドポイントを構成し、SDK を使用してモデルをデプロイし、環境変数を適切に設定します。

# COMMAND ----------

##
from databricks.sdk.service.serving import EndpointCoreConfigInput
from databricks.sdk import WorkspaceClient

## エンドポイント設定の定義
endpoint_config_dict = {
    "served_models": [
        {
            "model_name": <FILL_IN>,
            "model_version": <FILL_IN>,
            "scale_to_zero_enabled": True,
            "workload_size": "Small",
            "environment_vars": {
               "DATABRICKS_TOKEN": "{{{{secrets/{0}/depl_demo_token}}}}".format(DA.scope_name),
               "DATABRICKS_HOST": "{{{{secrets/{0}/depl_demo_host}}}}".format(DA.scope_name),
            },
        },
    ]
}

endpoint_config = EndpointCoreConfigInput.from_dict(endpoint_config_dict)

## ワークスペースクライアントの起動
w = WorkspaceClient()
serving_endpoint_name = f"{DA.unique_name('_')}_endpoint"

## エンドポイントが存在する場合は取得
existing_endpoint = next(
    (e for e in w.serving_endpoints.list() if e.name == serving_endpoint_name), None
)

## Databricks ホストを取得する
db_host = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("browserHostName").value()
serving_endpoint_url = f"{db_host}/ml/endpoints/{serving_endpoint_name}"

## エンドポイントが存在しない場合は作成する
if existing_endpoint is None:
    print(f"Creating the endpoint {serving_endpoint_url}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.<FILL_IN>
## エンドポイントが存在する場合は、新しいバージョンを提供するように更新します
else:
    print(f"Updating the endpoint {serving_endpoint_url} to version {latest_model_version}, this will take a few minutes to package and deploy the endpoint...")
    w.serving_endpoints.<FILL_IN>

## エンドポイントURLの表示
displayHTML(f'Your Model Endpoint Serving is now available. Open the <a href="/ml/endpoints/{serving_endpoint_name}">Model Serving Endpoint page</a> for more details.')

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from databricks.sdk.service.serving import EndpointCoreConfigInput
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC
# MAGIC ## エンドポイント設定の定義
# MAGIC endpoint_config_dict = {
# MAGIC     "served_models": [
# MAGIC         {
# MAGIC             "model_name": model_name,
# MAGIC             "model_version": latest_model_version,
# MAGIC             "scale_to_zero_enabled": True,
# MAGIC             "workload_size": "Small",
# MAGIC             "environment_vars": {
# MAGIC                 "DATABRICKS_TOKEN": "{{{{secrets/{0}/depl_demo_token}}}}".format(DA.scope_name),
# MAGIC                 "DATABRICKS_HOST": "{{{{secrets/{0}/depl_demo_host}}}}".format(DA.scope_name),
# MAGIC             },
# MAGIC         },
# MAGIC     ]
# MAGIC }
# MAGIC
# MAGIC endpoint_config = EndpointCoreConfigInput.from_dict(endpoint_config_dict)
# MAGIC
# MAGIC ## ワークスペースクライアントの起動
# MAGIC w = WorkspaceClient()
# MAGIC serving_endpoint_name = f"{DA.unique_name('_')}_endpoint"
# MAGIC
# MAGIC ## エンドポイントが存在する場合は取得
# MAGIC existing_endpoint = next(
# MAGIC     (e for e in w.serving_endpoints.list() if e.name == serving_endpoint_name), None
# MAGIC )
# MAGIC
# MAGIC ## Databricks ホストを取得する
# MAGIC db_host = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("browserHostName").value()
# MAGIC serving_endpoint_url = f"{db_host}/ml/endpoints/{serving_endpoint_name}"
# MAGIC
# MAGIC ## エンドポイントが存在しない場合は作成する
# MAGIC if existing_endpoint is None:
# MAGIC     print(f"Creating the endpoint {serving_endpoint_url}, this will take a few minutes to package and deploy the endpoint...")
# MAGIC     w.serving_endpoints.create_and_wait(name=serving_endpoint_name, config=endpoint_config)
# MAGIC ## エンドポイントが存在する場合は、新しいバージョンを提供するように更新します
# MAGIC else:
# MAGIC     print(f"Updating the endpoint {serving_endpoint_url} to version {latest_model_version}, this will take a few minutes to package and deploy the endpoint...")
# MAGIC     w.serving_endpoints.update_config_and_wait(served_models=endpoint_config.served_models, name=serving_endpoint_name)
# MAGIC
# MAGIC ## エンドポイントURLの表示
# MAGIC displayHTML(f'Your Model Endpoint Serving is now available. Open the <a href="/ml/endpoints/{serving_endpoint_name}">Model Serving Endpoint')

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.3: Model ServingUIを使用した推論テーブルの作成
# MAGIC
# MAGIC Model Serving UI を使用して推論テーブルを設定します。
# MAGIC
# MAGIC 1. **ステップ 2.2** の出力に表示されたリンクをクリックします。
# MAGIC 2. **[編集]** ボタンをクリックします。
# MAGIC 3. **推論テーブル** セクションを展開します。
# MAGIC 4. **推論テーブルを有効にする** チェックボックスをオンにします。
# MAGIC 5. 推論テーブルのカタログ、スキーマ、およびテーブル情報を入力します。
# MAGIC    - **カタログ名:** <Your Catalog Name>
# MAGIC    - **スキーマ名:** <Your Schema Name>
# MAGIC    - **テーブル名の接頭辞:** '<Your Table Name>` (e.g.: `rag_app_realtime')
# MAGIC 6. **更新** ボタンをクリックします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 3: UIを使用したA/Bテストの設定
# MAGIC
# MAGIC このタスクでは、Databricks UI を使用して A/B テスト用に、同じバージョンのモデル間でのトラフィック分割を構成します。 これにより、両方の構成を推論に使用できるようになり、A/B テストまたは段階的なロールアウトのために、トラフィックの一定割合を各構成に向けることができます。
# MAGIC
# MAGIC
# MAGIC  **注:** 通常、モデルの改良版を登録します。 ただし、時間の制約により、私たちが提供したものと同じモデルをデプロイします。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC 1. **[サービング](/ml/endpoints)に移動します**
# MAGIC
# MAGIC 2. 前に作成したエンドポイントを見つけます。
# MAGIC 3. エンドポイント名の横にある **[編集]** ボタンをクリックします。
# MAGIC
# MAGIC 4. **新しいサービス提供エンティティの追加**
# MAGIC     - **[サービス提供エンティティ] セクションで、[**+ サービス提供エンティティを追加] をクリックします。
# MAGIC     - モデル名と一致するエンティティ名を選択します。 **`genai_shared_catalog.ws_<xxx>.rag_app`** モデル名は、このノートブックの冒頭に表示されています。
# MAGIC     - 新しい提供エンティティの **バージョン 1** を選択します。
# MAGIC
# MAGIC 5. **トラフィック分割の構成**
# MAGIC     - **トラフィック分割** セクションで、2 つの構成間でトラフィックを分割します。
# MAGIC     - トラフィックの割合を、新しい構成では60％、古い構成では40％に設定する。
# MAGIC
# MAGIC 6. **高度な構成**
# MAGIC     - 環境変数を次のように入力します (これらの値はラボの冒頭に出力されます)。
# MAGIC       - **DATABRICKS_HOST** : **&lcub;&lcub; secrets/`scope`/`host_key` &rcub;&rcub;**
# MAGIC       - **DATABRICKS_TOKEN** : **&lcub;&lcub; secrets/`scope`/`token_key` &rcub;&rcub;**
# MAGIC     - **📌注記 : 一意のサーブされたエンティティ名を追加してください。**
# MAGIC 7. **推論テーブルの詳細を確認する**
# MAGIC     - 推論テーブルの設定が正しいことを確認してください。
# MAGIC     - テーブルは、分析のために推論結果をキャプチャするべきです。
# MAGIC
# MAGIC 8. **更新して待つ**
# MAGIC     - **更新**ボタンをクリックして、変更を保存します。
# MAGIC     - サービングエンドポイントが更新されるのを待ちます。 これには数分かかる場合があります。
# MAGIC
# MAGIC これらの手順に従うことで、同じバージョンを使用してモデルの A/B テストを正常に構成し、さまざまな構成を評価してパフォーマンスを監視できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 4: エンドポイントにクエリーを実行 
# MAGIC
# MAGIC このタスクでは、Databricks SDK を使用してモデルに対してクエリを実行します

# COMMAND ----------

##
from mlflow.deployments import get_deploy_client

## 推論のためにモデルに送信する質問を定義する
messages = {"messages" : [
        {"role": "user", "content": "What is PPO?"}
    ]}

## 指定されたserving endpointにクエリを送信し、応答を受信する
answer = <FILL_IN>

## 受信したレスポンスからモデルの予測を表示する
print(answer.predictions)

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from mlflow.deployments import get_deploy_client
# MAGIC
# MAGIC ## 推論のためにモデルに送信する質問を定義する
# MAGIC messages = {"messages" : [
# MAGIC         {"role": "user", "content": "What is PPO?"}
# MAGIC     ]}
# MAGIC
# MAGIC ## 指定されたserving endpointにクエリを送信し、応答を受信する
# MAGIC answer = w.serving_endpoints.query(
# MAGIC   serving_endpoint_name, 
# MAGIC   inputs=messages
# MAGIC )
# MAGIC
# MAGIC ## 受信したレスポンスからモデルの予測を表示する
# MAGIC print(answer.predictions)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 5: 推論テーブルの検査
# MAGIC
# MAGIC このタスクでは、デプロイ プロセス中に作成された推論テーブルをビューして検査します。 推論テーブルには、モデルによって行われた推論に関するデータが格納され、モデルのパフォーマンスの監視と分析に役立ちます。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC 1. **[カタログ](explore/data)に移動します。**
# MAGIC
# MAGIC 2. **カタログとスキーマの選択:**
# MAGIC    - カタログエクスプローラーで、推論テーブルの設定時に入力したカタログを見つけて選択します。
# MAGIC    - 選択したカタログ内で、推論テーブルを含むスキーマに移動します。
# MAGIC
# MAGIC 3. **推論テーブルを表示：**
# MAGIC    - 選択したスキーマ内の推論テーブルを見つけます。 テーブル名には、デプロイ構成時に指定したとおりに接頭辞が付きます。
# MAGIC    - 推論テーブルをクリックして開き、保存されているサンプルデータを表示します。
# MAGIC
# MAGIC これらの手順に従うことで、テーブルに保存されている推論データにアクセスして検査できるようになり、モデルのパフォーマンスとモデルが行っている予測の種類を分析できます。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC このラボでは、Databricks Model Servingを使用してカスタムモデルを正常にデプロイしました。 モデルバージョンの取得方法、SDK を使用したモデルのデプロイ方法、UI を使用した 2 番目のバージョンの作成とデプロイ方法、モデルエンドポイントのクエリ方法、テーブルに格納されている推論結果の検査方法を学習しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>