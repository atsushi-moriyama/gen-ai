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
# MAGIC # LAB - オンラインモニタリング
# MAGIC
# MAGIC このラボでは、Databricks Lakehouse Monitoringを使用して、サンプル推論テーブルのオンラインモニターを作成します。 デプロイされたmodel serving エンドポイントから抽出されたサンプル推論テーブルがインポートされ、監視に使用できるようになりました。
# MAGIC
# MAGIC **ラボの概要:**
# MAGIC
# MAGIC このラボでは、次のタスクを完了する必要があります。
# MAGIC
# MAGIC * **タスク 1:** 評価メトリックの定義
# MAGIC * **タスク 2:** 要求ペイロードの展開
# MAGIC * **タスク 3:** メトリクスを計算
# MAGIC * **タスク 4:** 処理された推論テーブルを保存する
# MAGIC * **タスク 5:** 推論テーブル上でモニターの作成
# MAGIC * **タスク 6:** モニターの詳細の確認
# MAGIC * **タスク 7:** モニター ダッシュボードの表示

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必要条件
# MAGIC
# MAGIC レッスンを開始する前に、次の要件を確認してください。
# MAGIC
# MAGIC * このノートブックを実行するには、次のいずれかの Databricks Runtime を使用する必要があります。 **`17.3.x-cpu-ml-scala2.13`**

# COMMAND ----------

# MAGIC %md
# MAGIC ## 学習環境のセットアップ
# MAGIC
# MAGIC 必要なライブラリをインストールし、設定を読み込みます。

# COMMAND ----------

# MAGIC %pip install -U -qq databricks-sdk textstat tiktoken evaluate

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-03

# COMMAND ----------

# MAGIC %md
# MAGIC ## 推論テーブル
# MAGIC
# MAGIC デモで使用したのと同じ推論テーブルを使用します。 推論テーブルは事前に読み込まれており、すぐに使用できます。

# COMMAND ----------

inference_table_name = f"{DA.catalog_name}.{DA.schema_name}.rag_app_realtime_payload"
display(spark.sql(f"SELECT * FROM {inference_table_name}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 1: 評価メトリクスの定義
# MAGIC このタスクでは、推論テーブルデータの分析に使用する、毒性、パープレキシティ、可読性などの評価メトリクスを定義します。
# MAGIC
# MAGIC - `pandas_udf`を使用して評価メトリクス関数を定義します。

# COMMAND ----------

##
## Import necessary libraries
import tiktoken, textstat, evaluate
import pandas as pd
from pyspark.sql.functions import pandas_udf

## Define a pandas UDF to compute the number of tokens in the text
@pandas_udf("int")
def compute_num_tokens(texts: pd.Series) -> pd.Series:
  encoding = tiktoken.get_encoding("cl100k_base")
  return pd.Series(<FILL_IN>)

## Define a pandas UDF to compute the toxicity of the text
@pandas_udf("double")
def compute_toxicity(texts: pd.Series) -> pd.Series:
  ## Omit entries with null input from evaluation
  toxicity = <FILL_IN>
  return pd.Series(toxicity.compute(<FILL_IN>)["toxicity"]).where(<FILL_IN>)

## Define a pandas UDF to compute the perplexity of the text
@pandas_udf("double")
def compute_perplexity(texts: pd.Series) -> pd.Series:
  ## Omit entries with null input from evaluation
  perplexity = <FILL_IN>
  return pd.Series(perplexity.compute(<FILL_IN>)["perplexities"]).where(<FILL_IN>)

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC ## 必要なライブラリのインポート
# MAGIC import tiktoken, textstat, evaluate
# MAGIC import pandas as pd
# MAGIC from pyspark.sql.functions import pandas_udf
# MAGIC
# MAGIC ## pandas UDF を定義して、テキスト内のトークンの数を計算する
# MAGIC @pandas_udf("int")
# MAGIC def compute_num_tokens(texts: pd.Series) -> pd.Series:
# MAGIC   encoding = tiktoken.get_encoding("cl100k_base")
# MAGIC   return pd.Series(map(len, encoding.encode_batch(texts)))
# MAGIC
# MAGIC ## pandas UDF を定義してテキストの毒性を計算する
# MAGIC @pandas_udf("double")
# MAGIC def compute_toxicity(texts: pd.Series) -> pd.Series:
# MAGIC   ## Omit entries with null input from evaluation
# MAGIC   toxicity = evaluate.load("toxicity", module_type="measurement", cache_dir="/tmp/hf_cache/")
# MAGIC   return pd.Series(toxicity.compute(predictions=texts.fillna(""))["toxicity"]).where(texts.notna(), None)
# MAGIC
# MAGIC ## pandas UDF を定義してテキストのパープレキシティを計算する
# MAGIC @pandas_udf("double")
# MAGIC def compute_perplexity(texts: pd.Series) -> pd.Series:
# MAGIC   ## Omit entries with null input from evaluation
# MAGIC   perplexity = evaluate.load("perplexity", module_type="measurement", cache_dir="/tmp/hf_cache/")
# MAGIC   return pd.Series(perplexity.compute(data=texts.fillna(""), model_id="gpt2")["perplexities"]).where(texts.notna(), None)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 2: 要求ペイロードの展開
# MAGIC このタスクでは、推論テーブルから要求ペイロードをアンパックし、処理の準備をします。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC - リクエストをストリームとしてアンパックします。
# MAGIC - ジョブを監視するための不要な列を削除します。

# COMMAND ----------

##
import os

## Reset checkpoint [for demo purposes ONLY]
checkpoint_location = os.path.join(DA.paths.working_dir, "checkpoint")
dbutils.fs.rm(checkpoint_location, True)

## Define the JSON path and type for the input requests
INPUT_REQUEST_JSON_PATH = <FILL_IN>
INPUT_JSON_PATH_TYPE = <FILL_IN>
KEEP_LAST_QUESTION_ONLY = False

## Define the JSON path and type for the output responses
OUTPUT_REQUEST_JSON_PATH = <FILL_IN>
OUPUT_JSON_PATH_TYPE = <FILL_IN>

## Unpack the requests as a stream
requests_raw_df = spark.readStream.table(inference_table_name)
requests_processed_df = unpack_requests(
    <FILL_IN>,
    <FILL_IN>,
    <FILL_IN>,
    <FILL_IN>,
    <FILL_IN>,
    <FILL_IN>
)

## Drop un-necessary columns for monitoring jobs
requests_processed_df = <FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC import os
# MAGIC
# MAGIC ## Reset checkpoint [for demo purposes ONLY]
# MAGIC checkpoint_location = os.path.join(DA.paths.working_dir, "checkpoint")
# MAGIC dbutils.fs.rm(checkpoint_location, True)
# MAGIC
# MAGIC ## Define the JSON path and type for the input requests
# MAGIC INPUT_REQUEST_JSON_PATH = "inputs[*].query"
# MAGIC INPUT_JSON_PATH_TYPE = "array<string>"
# MAGIC KEEP_LAST_QUESTION_ONLY = False
# MAGIC
# MAGIC ## Define the JSON path and type for the output responses
# MAGIC OUTPUT_REQUEST_JSON_PATH = "predictions"
# MAGIC OUPUT_JSON_PATH_TYPE = "array<string>"
# MAGIC
# MAGIC ## Unpack the requests as a stream.
# MAGIC requests_raw_df = spark.readStream.table(inference_table_name)
# MAGIC requests_processed_df = unpack_requests(
# MAGIC     requests_raw_df,
# MAGIC     INPUT_REQUEST_JSON_PATH,
# MAGIC     INPUT_JSON_PATH_TYPE,
# MAGIC     OUTPUT_REQUEST_JSON_PATH,
# MAGIC     OUPUT_JSON_PATH_TYPE,
# MAGIC     KEEP_LAST_QUESTION_ONLY
# MAGIC )
# MAGIC
# MAGIC ## Drop un-necessary columns for monitoring jobs
# MAGIC requests_processed_df = requests_processed_df.drop("date", "status_code", "sampling_fraction", "client_request_id", "databricks_request_id")

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 3: メトリクスの計算
# MAGIC
# MAGIC このタスクでは、アンパックされた要求ペイロードに対して定義された評価メトリックを計算します。
# MAGIC
# MAGIC - 入力列と出力列の有害性、パープレキシティ、トークン数を計算します。

# COMMAND ----------

##
## Define the columns to measure
column_to_measure = <FILL_IN>

## Iterate over each column to measure
for column_name in column_to_measure:
    # Compute the metrics and add them as new columns to the DataFrame
    requests_df_with_metrics = <FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC ## 測定する列を定義する
# MAGIC column_to_measure = ["input", "output"]
# MAGIC
# MAGIC ## 測定する各列を反復処理する
# MAGIC for column_name in column_to_measure:
# MAGIC     ## メトリクスを計算し、新しい列として DataFrame に追加する
# MAGIC     requests_df_with_metrics = (
# MAGIC       requests_processed_df
# MAGIC                  .withColumn(f"toxicity({column_name})", compute_toxicity(col(column_name))) 
# MAGIC                  .withColumn(f"perplexity({column_name})", compute_perplexity(col(column_name))) 
# MAGIC                  .withColumn(f"token_count({column_name})", compute_num_tokens(col(column_name))) 
# MAGIC     )

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 4: 処理された推論テーブルの保存
# MAGIC
# MAGIC このタスクでは、計算されたメトリクスを持つ処理された推論テーブルを Delta テーブルに保存します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC - 処理された推論テーブルが存在しない場合は作成します。
# MAGIC - 解凍された新しいペイロードとメトリクスを、処理済みのテーブルに追加します。

# COMMAND ----------

##
from delta.tables import DeltaTable
## Define the name of the processed table
processed_table_name = f"{DA.catalog_name}.{DA.schema_name}.rag_app_processed_inferences_lab"

## Create the table if it does not exist
(DeltaTable.createOrReplace(spark)
        .tableName(<FILL_IN>) 
        .addColumns(<FILL_IN>.schema) 
        .property("delta.enableChangeDataFeed", "true") 
        .property("delta.columnMapping.mode", "name") 
        .execute()) # Execute the table creation

## Write the requests_df_with_metrics DataFrame to the processed table as a stream
(requests_df_with_metrics.writeStream
                      .trigger(availableNow=True) 
                      .format("delta") 
                      .outputMode("append") 
                      .option("checkpointLocation", <FILL_IN>)
                      .toTable(<FILL_IN>).awaitTermination())

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from delta.tables import DeltaTable
# MAGIC ## 処理されたテーブルの名前を定義します
# MAGIC processed_table_name = f"{DA.catalog_name}.{DA.schema_name}.rag_app_processed_inferences_lab"
# MAGIC
# MAGIC ## テーブルが存在しない場合は作成
# MAGIC (DeltaTable.createOrReplace(spark)
# MAGIC         .tableName(processed_table_name)
# MAGIC         .addColumns(requests_df_with_metrics.schema)
# MAGIC         .property("delta.enableChangeDataFeed", "true")
# MAGIC         .property("delta.columnMapping.mode", "name")
# MAGIC         .execute())
# MAGIC ## 処理されたテーブルにrequests_df_with_metrics DataFrame をストリームとして書き込みます
# MAGIC (requests_df_with_metrics.writeStream
# MAGIC                       .trigger(availableNow=True)
# MAGIC                       .format("delta")
# MAGIC                       .outputMode("append")
# MAGIC                       .option("checkpointLocation", checkpoint_location)
# MAGIC                       .toTable(processed_table_name).awaitTermination())

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 5: 推論テーブルでのモニターの作成
# MAGIC
# MAGIC このタスクでは、Databricks Lakehouse Monitoringを使用して、処理された推論テーブルにモニターを作成します。
# MAGIC
# MAGIC -  `databricks-sdk`を使用してモニターを作成します。

# COMMAND ----------

##
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import MonitorTimeSeries
## Initialize the workspace client
w = WorkspaceClient()

try:
  ## Create a monitor using the workspace client's quality_monitors service
  lhm_monitor = w.quality_monitors.create(
    table_name=<FILL_IN>,
    time_series = MonitorTimeSeries(
      timestamp_col = "timestamp",
      granularities = ["5 minutes"],
    ),
    assets_dir = <FILL_IN>,
    slicing_exprs = <FILL_IN>,
    output_schema_name=f"{DA.catalog_name}.{DA.schema_name}"
  )

## Handle any exceptions that occur during monitor creation
except Exception as lhm_exception:
  <FIll_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks.sdk.service.catalog import MonitorTimeSeries
# MAGIC ## ワークスペースクライアントの初期化
# MAGIC w = WorkspaceClient()
# MAGIC
# MAGIC try:
# MAGIC   ## ワークスペースクライアントのquality_monitorsサービスを使用してモニターを作成する
# MAGIC   lhm_monitor = w.quality_monitors.create(
# MAGIC     table_name=processed_table_name,
# MAGIC     time_series = MonitorTimeSeries(
# MAGIC       timestamp_col = "timestamp",
# MAGIC       granularities = ["5 minutes"],
# MAGIC     ),
# MAGIC     assets_dir = os.getcwd(),
# MAGIC     slicing_exprs = ["model_id"],
# MAGIC     output_schema_name=f"{DA.catalog_name}.{DA.schema_name}"
# MAGIC   )
# MAGIC
# MAGIC ## モニター作成中に発生した例外を処理する
# MAGIC except Exception as lhm_exception:
# MAGIC   print(lhm_exception)

# COMMAND ----------

##
from databricks.sdk.service.catalog import MonitorInfoStatus

## Get the monitor information for the processed table
monitor_info = <FILL_IN>
print(monitor_info.status)

## Check if the monitor status is pending
if monitor_info.status == MonitorInfoStatus.<FILL_IN>:
    print("Wait until monitor creation is completed...")

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from databricks.sdk.service.catalog import MonitorInfoStatus
# MAGIC
# MAGIC ## 処理対象テーブルの監視情報を取得する
# MAGIC monitor_info = w.quality_monitors.get(processed_table_name)
# MAGIC print(monitor_info.status)
# MAGIC
# MAGIC ## 監視statusが保留中かどうかの確認
# MAGIC if monitor_info.status == MonitorInfoStatus.MONITOR_STATUS_PENDING:
# MAGIC     print("Wait until monitor creation is completed...")

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 6: モニターの詳細の確認
# MAGIC
# MAGIC このタスクでは、前のステップで作成したモニターの詳細をレビューします。 これには、監視の詳細の**品質**タブをビューし、監視によって生成されたメトリクステーブルを確認することが含まれます。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC
# MAGIC 次の手順を実行します。
# MAGIC
# MAGIC
# MAGIC 1. **[品質] タブでモニターの詳細をビューする**
# MAGIC    - **[カタログ](explore/data)** に移動し、監視したテーブルを見つけます。
# MAGIC    - **品質**タブをクリックして、モニターの詳細をビューします。
# MAGIC
# MAGIC 2. **メトリック テーブル**
# MAGIC    - メトリック テーブル (`*_processed_profile_metrics` and `*_processed_drift_metrics`) を調べます。
# MAGIC
# MAGIC
# MAGIC **注:** 詳細を確認する前に、更新プロセスが完了し、指標テーブルの準備が整っていることを確認してください。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 7: モニターダッシュボードの表示
# MAGIC
# MAGIC このタスクでは、Lakehouse Monitoringによって生成された Databricks SQL ダッシュボードを表示して、モニタリングソリューションのデータとメトリクスを確認します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC
# MAGIC 次の手順を実行します。
# MAGIC
# MAGIC 1. **SQL ダッシュボードの表示**
# MAGIC    - **[ビューダッシュボード] をクリックして、**[Quality] タブから SQL ダッシュボードを開きます。
# MAGIC
# MAGIC 2. **全体的な要約統計量の検査**
# MAGIC    - ダッシュボードに表示される全体的なサマリー統計を調べます。
# MAGIC
# MAGIC 3. **作成されたメトリックのビューを確認する**
# MAGIC    - このラボの最初のステップで作成したメトリクスを確認して、時間の経過に伴うデータ品質とモデルのパフォーマンスを把握します。
# MAGIC
# MAGIC
# MAGIC **注:** ダッシュボードを確実に作成するために、アクセス可能な SQL クラスターが稼働していることを確認してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC このラボでは、Databricks Lakehouse Monitoringを使用してオンライン監視を作成しました。 まず、評価メトリクスを定義し、推論テーブルに対してこれらのメトリクスを計算しました。 次に、推論テーブルにモニターを作成しました。 最後に、監視の詳細と自動作成された Databricks SQL ダッシュボードを確認しました。 このラボを正常に完了すると、デプロイされた AI モデルの推論要求をキャプチャする推論テーブルのオンライン監視を作成できるようになります。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>