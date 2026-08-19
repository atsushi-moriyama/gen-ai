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
# MAGIC # LLM RAGチェーンのオンラインモニタリング
# MAGIC
# MAGIC
# MAGIC **このデモでは、Lakehouse Monitoringを使用してGenAIアプリケーションを監視するための基盤を構築します。** Lakehouse Monitoringは、Databricksが提供する自動データモニタリングソリューションです。 これを使用して、GenAIアプリケーションの入出力データを監視します。
# MAGIC
# MAGIC **学習目標:**
# MAGIC
# MAGIC *このデモを終了すると、あなたは以下を可能にすることができます:*
# MAGIC
# MAGIC * 推論テーブルをアンパックして、Model Servingエンドポイントのリクエスト/レスポンスを構造化する
# MAGIC * Lakehouse Monitoringの基本的な使い方を説明する
# MAGIC * アンパックされた/処理された推論テーブルにモニターを設定する

# COMMAND ----------

# MAGIC %md
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

# MAGIC %pip install -U -qq databricks-sdk tiktoken textstat evaluate

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC デモを開始する前に、提供されているクラスルーム セットアップ スクリプトを実行します。 このスクリプトでは、デモに必要な構成変数を定義します。 次のセルを実行しましょう。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-03

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の規約:**
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
# MAGIC このデモでは、GenAIアプリケーション向けの**Lakehouse Monitoring**を紹介します。
# MAGIC
# MAGIC このデモを完了するには、次の手順に従います。
# MAGIC
# MAGIC 1. 既存のmodel servingエンドポイントの推論テーブルを解凍します。
# MAGIC 2. いくつかの LLM メトリクスを計算する。
# MAGIC 2. Lakehouse Monitoring の基本操作を説明する。
# MAGIC 3. Lakehouse Monitoring を使用して、より堅牢なモニターを設定する

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: 推論テーブルの作成
# MAGIC
# MAGIC 監視を示すために、事前設定されたサンプル推論テーブルを作成します。 **推論テーブルは、コース構成ノートブックで既に作成されています。**

# COMMAND ----------

from delta.tables import DeltaTable

inference_table_name = f"{DA.catalog_name}.{DA.schema_name}.rag_app_realtime_payload"

# 先に進む前に、テーブルが存在するかどうかを確認します。
inference_table_exists = DeltaTable.forName(spark, inference_table_name)

if inference_table_exists:
    display(spark.sql(f"SELECT * FROM {inference_table_name} LIMIT 5"))
else:
    raise Exception("Inference table does not exist, please re-run/verify classroom setup script")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2: 推論テーブルの展開と LLM メトリクスを計算する
# MAGIC
# MAGIC <img src="https://github.com/databricks-demos/dbdemos-resources/blob/main/images/product/chatbot-rag/llm-eval-online-1.png?raw=true" style="float: right" width="900px">

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1: テーブルの展開
# MAGIC
# MAGIC リクエストカラムとレスポンスカラムにはモデルのプロンプトが含まれ、`string`として出力されます
# MAGIC
# MAGIC **注:** フォーマットはモデル定義によって異なりますが、入力は通常 TF フォーマットの JSON として表され、出力はモデル定義にも依存します。
# MAGIC
# MAGIC
# MAGIC Spark JSON Path アノテーションを使用して、プロンプトと入力候補を文字列として直接アクセスし、それらを `array_zip` と結合する、最後に `explode` 内容を 1 つのプロンプト/入力候補行にします。
# MAGIC
# MAGIC *注: これは製品内で直接簡単になります -- 今のところ、このタスクを簡略化するためにこのノートブックを提供しています。*

# COMMAND ----------

#入力ペイロードのフォーマットは、TFの「inputs」サービングフォーマットに従い、「query」フィールドを含みます。
# 単一クエリ入力フォーマット: {"入力": [{"クエリ": "ユーザーの質問?"}]}
INPUT_REQUEST_JSON_PATH = "inputs[*].query"

# JSON セレクタが返すスキーマに一致 (inputs[*].query は文字列の配列)
INPUT_JSON_PATH_TYPE = "array<string>"
KEEP_LAST_QUESTION_ONLY = False

# 回答フォーマット: {"predictions": ["答え"]}
OUTPUT_REQUEST_JSON_PATH = "predictions"

# JSON セレクタによって返されるスキーマと一致します (predictions は文字列の配列です)
OUPUT_JSON_PATH_TYPE = "array<string>"

# COMMAND ----------

# MAGIC %md
# MAGIC 次に、バッチモードでサンプルでアンパックロジックをテストしましょう。

# COMMAND ----------

# 提供されているヘルパー関数を使用して展開する
payloads_sample_df = spark.table(inference_table_name).where('status_code == 200').limit(10)
payloads_unpacked_sample_df = unpack_requests(
    payloads_sample_df,
    INPUT_REQUEST_JSON_PATH,
    INPUT_JSON_PATH_TYPE,
    OUTPUT_REQUEST_JSON_PATH,
    OUPUT_JSON_PATH_TYPE,
    KEEP_LAST_QUESTION_ONLY
)

display(payloads_unpacked_sample_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2: [プロンプト補完] 評価メトリクスを計算
# MAGIC
# MAGIC 毒性、パープレキシティ、可読性などのテキスト評価メトリクスを計算してみましょう。
# MAGIC
# MAGIC これらはLakehouse Monitoringによって分析され、これらのメトリクスが時間の経過とともにどのように変化するかを理解できます。
# MAGIC
# MAGIC *注: これはすべてを網羅したリストではなく、これらの計算は製品内ですぐに自動的に実行されます。今のところ、このタスクを簡略化するためにこのノートブックを提供しています。*

# COMMAND ----------

import tiktoken, textstat, evaluate
import pandas as pd
from pyspark.sql.functions import pandas_udf


@pandas_udf("int")
def compute_num_tokens(texts: pd.Series) -> pd.Series:
  encoding = tiktoken.get_encoding("cl100k_base")
  return pd.Series(map(len, encoding.encode_batch(texts)))

@pandas_udf("double")
def flesch_kincaid_grade(texts: pd.Series) -> pd.Series:
  return pd.Series([textstat.flesch_kincaid_grade(text) for text in texts])
 
@pandas_udf("double")
def automated_readability_index(texts: pd.Series) -> pd.Series:
  return pd.Series([textstat.automated_readability_index(text) for text in texts])

@pandas_udf("double")
def compute_toxicity(texts: pd.Series) -> pd.Series:
  # 評価から入力がnullのエントリを除外する
  toxicity = evaluate.load("toxicity", module_type="measurement", cache_dir="/tmp/hf_cache/")
  return pd.Series(toxicity.compute(predictions=texts.fillna(""))["toxicity"]).where(texts.notna(), None)

@pandas_udf("double")
def compute_perplexity(texts: pd.Series) -> pd.Series:
  # 評価から入力がnullのエントリを除外する
  perplexity = evaluate.load("perplexity", module_type="measurement", cache_dir="/tmp/hf_cache/")
  return pd.Series(perplexity.compute(data=texts.fillna(""), model_id="gpt2")["perplexities"]).where(texts.notna(), None)

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql.functions import col

def compute_metrics(requests_df: DataFrame, column_to_measure = ["input", "output"]) -> DataFrame:
  for column_name in column_to_measure:
    requests_df = (
      requests_df.withColumn(f"toxicity({column_name})", compute_toxicity(col(column_name)))
                 .withColumn(f"perplexity({column_name})", compute_perplexity(col(column_name)))
                 .withColumn(f"token_count({column_name})", compute_num_tokens(col(column_name)))
                 .withColumn(f"flesch_kincaid_grade({column_name})", flesch_kincaid_grade(col(column_name)))
                 .withColumn(f"automated_readability_index({column_name})", automated_readability_index(col(column_name)))
    )
  return requests_df

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.3: ペイロードからメトリクスを段階的にアンパックして計算し、final `_processed` table に保存
# MAGIC
# MAGIC 1. 読み込み `inference_table_name` delta テーブルをストリームとして実行し、ペイロードをアンパックします
# MAGIC 2. ストリーミングデータフレームから不要な列を削除する
# MAGIC 3. LLM 関連の評価メトリクスを(一部)計算する
# MAGIC 4. 初期化する `processed_table` (ストリーミングデータフレームからスキーマを使用してテーブルを作成)
# MAGIC     1. Delta の [Change-Data-Feed](https://docs.delta.io/delta-change-data-feed/) を有効にして、ペイロードの増分処理を確実に行う
# MAGIC     2. 列名での特殊文字のサポートを有効にする ([column mapping](https://docs.delta.io/latest/delta-column-mapping.html)) を有効にする
# MAGIC 5. 処理された新しいペイロードとメトリックを  `processed_table_name` Delta Tableに追加/書き込みする

# COMMAND ----------

import os

# チェックポイントのリセット [デモ目的のみ]
checkpoint_location = os.path.join(DA.paths.working_dir, "checkpoint")
dbutils.fs.rm(checkpoint_location, True)

# リクエストをストリームとして展開します。
requests_raw_df = spark.readStream.table(inference_table_name)
requests_processed_df = unpack_requests(
    requests_raw_df,
    INPUT_REQUEST_JSON_PATH,
    INPUT_JSON_PATH_TYPE,
    OUTPUT_REQUEST_JSON_PATH,
    OUPUT_JSON_PATH_TYPE,
    KEEP_LAST_QUESTION_ONLY
)

# ジョブの監視に不要なカラムを削除する
requests_processed_df = requests_processed_df.drop("date", "status_code", "sampling_fraction", "client_request_id", "databricks_request_id")

# テキスト評価メトリクスの計算
requests_with_metrics_df = compute_metrics(requests_processed_df)

# COMMAND ----------

def create_processed_table_if_not_exists(table_name, requests_with_metrics):
    """
    Helper method to create processed table using schema
    """
    (
      DeltaTable.createOrReplace(spark) # 毎回ドロップしないようにするため .createIfNotExists(spark)
        .tableName(table_name)
        .addColumns(requests_with_metrics.schema)
        .property("delta.enableChangeDataFeed", "true")
        .property("delta.columnMapping.mode", "name")
        .execute()
    )

# COMMAND ----------

# このテーブルに対して定義されたチェックポイントパスを使用して、リクエストストリームを永続化します
processed_table_name = f"{DA.catalog_name}.{DA.schema_name}.rag_app_processed_inferences"
create_processed_table_if_not_exists(processed_table_name, requests_with_metrics_df)

# 展開された新しいペイロードとメトリクスを追加
(requests_with_metrics_df.writeStream
                      .trigger(availableNow=True)
                      .format("delta")
                      .outputMode("append")
                      .option("checkpointLocation", checkpoint_location)
                      .toTable(processed_table_name).awaitTermination())

# 監視対象のテーブル(リクエストとテキスト評価メトリクスを含む)を表示します。
display(spark.table(processed_table_name))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ 3: Lakehouse監視の基本を説明する
# MAGIC
# MAGIC 組み込みのModel Serving推論テーブルは、アプリケーションに関する情報を収集するためのシンプルで効果的な方法ですが、Lakehouse Monitoringを使用すると、さらに多くのことができます。
# MAGIC
# MAGIC Databricks Lakehouse Monitoringでは、すべてのデータの *統計的特性* と *品質* をモニタリングできます。 これには、従来の ML モデルと GenAI モデル、およびモデルを提供するエンドポイントに関連するデータが含まれます。
# MAGIC
# MAGIC ここでは、GenAI向けLakehouse Monitoringのアプリケーションをいくつかご紹介します。
# MAGIC
# MAGIC * Vector searchインデックスに関連付けられたテーブルで使用されるデータの統計的特性を監視します
# MAGIC * 時間の経過とともにさまざまなエンティティの相対的なパフォーマンスを監視します(つまり、モデルバージョンAがバージョンBと比較してどのようにパフォーマンスしているか)
# MAGIC * Model servingエンドポイントのプロンプト/完了に関する非構造化/テキスト関連のメトリクスをモニタリングする
# MAGIC
# MAGIC ### Lakehouse Monitoringの仕組み
# MAGIC
# MAGIC Lakehouse Monitoringは、アプリケーションに関連付けられている**データ**、つまり Unity Catalog の Delta テーブルに焦点を当てています。
# MAGIC
# MAGIC テーブルを監視するには、テーブルにアタッチされた **モニター** を作成します。 機械学習モデルのパフォーマンスを監視するには、モデルの入力と対応する予測を保持する推論テーブルに **モニター** をアタッチします。
# MAGIC
# MAGIC 機械学習のためのLakehouse Monitoringを以下に視覚化します。
# MAGIC
# MAGIC <img src="https://docs.databricks.com/en/_images/lakehouse-monitoring-overview.png" style="float: right" width="800px">
# MAGIC
# MAGIC 上の図では、データのフローがいくつかのステップに分かれています。
# MAGIC
# MAGIC 1. データは **入力テーブル** で始まります
# MAGIC 2. データは ML パイプラインを通じて処理されます
# MAGIC 3. データは **推論テーブル** に書き込まれます
# MAGIC
# MAGIC Lakehouse Monitoringは、**入力テーブル**と**推論テーブル**を監視するように設計されています
# MAGIC
# MAGIC **注:** 上の図は従来の機械学習用ですが、GenAI にも同様の原則が適用されます。
# MAGIC
# MAGIC ### モニタリングの種類
# MAGIC
# MAGIC Lakehouse Monitoringには、以下に詳述する3つの異なるタイプのモニターがあります。
# MAGIC
# MAGIC |**タイプ** |**説明** |
# MAGIC |------| ------------|
# MAGIC |時系列 |タイムスタンプ列に基づく時系列データセットを含むテーブルに使用します。 モニタリングでは、時系列の時間ベースのウィンドウにわたってデータ品質メトリクスが計算されます。|
# MAGIC |推論ログ |モデルの要求ログを含むテーブルに使用します。 各行は要求であり、タイムスタンプ、モデル入力、対応する予測、および (省略可能な) グラウンド トゥルース ラベルの列があります。 モニタリングでは、モデルのパフォーマンスとデータ品質のメトリクスを、リクエストログファイルの時間ベースのウィンドウ全体で比較します。
# MAGIC |スナップショット |他のすべてのタイプのテーブルに使用します。 モニタリングでは、テーブル内のすべてのデータに対するデータ品質メトリックが計算されます。 完全なテーブルは、更新のたびに処理されます。|
# MAGIC
# MAGIC ### Lakehouse Monitoringの出力
# MAGIC
# MAGIC モニターが設定されると、Lakehouse Monitoringは以下を自動的に生成します。
# MAGIC
# MAGIC 1. 2 つの **メトリクステーブル** は、上記のプロファイリングとドリフトの測定値を含む差分テーブルです。
# MAGIC 2. 上記の表に保存されている計算メトリクスを視覚化するための**ダッシュボード**
# MAGIC 一連の **SQL アラート** [AWS](https://docs.databricks.com/aws/en/sql/user/alerts) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/sql/user/alerts/) は、ユーザーが手動で作成して、関係者 (または **destinations** [AWS](https://docs.databricks.com/aws/en/sql/user/alerts) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/sql/user/alerts/) などのSlack/Teams Webhook、Pagerduty、メール通知)に特定のデータ特性を通知するために使用できます。
# MAGIC
# MAGIC 例から始めましょう。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ 4: 処理された推論テーブルにモニターを作成する
# MAGIC <img src="https://github.com/databricks-demos/dbdemos-resources/blob/main/images/product/chatbot-rag/llm-eval-online-2.png?raw=true" style="float: right" width="900px">
# MAGIC
# MAGIC このコースでは、Databricks を使用して、以前にデプロイされたアプリケーション/エンドポイントをサポートする `_processed` 推論テーブルにモニターを作成します。
# MAGIC
# MAGIC Lakehouse Monitoringのドキュメント([AWS](https://docs.databricks.com/lakehouse-monitoring/index.html) |[Azure](https://learn.microsoft.com/azure/databricks/lakehouse-monitoring/index))パラメーターと予想される使用法の詳細については参照してください。
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1: UIを使用する（オプション） 
# MAGIC このモニターを設定するには、以下の手順に従います。
# MAGIC
# MAGIC 1. **Catalog** に移動します
# MAGIC 2. 監視対象のテーブルを探します
# MAGIC 3. **Quality** タブをクリックします
# MAGIC 4. **Enable** ボタンをクリックします
# MAGIC 5. 次に、**Data profiling** の下にある **Configure** をクリックします
# MAGIC 6. モニター作成で、モニター設定に必要なオプションを選択します（*下記参照*）。
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC ![genai-as-04-online-monitoring-config](../Includes/images/genai-as-04-online-monitoring-config.png)
# MAGIC
# MAGIC **注:** ここでは、**時系列**プロファイルを設定します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2: databricks-sdk の使用
# MAGIC
# MAGIC [Databricks Lakehouse Monitoring API](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/catalog/quality_monitors.html#)のリファレンス資料を参照してください。

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import MonitorTimeSeries

# databricks-sdk の `quality_monitors` clientを使用してモニターを作成
w = WorkspaceClient()

try:
  lhm_monitor = w.quality_monitors.create(
    table_name=processed_table_name, # 常に 3 レベルの名前空間を使用
    time_series = MonitorTimeSeries(
      timestamp_col = "timestamp",
      granularities = ["5 minutes"],
    ),
    assets_dir = os.getcwd(),
    slicing_exprs = ["model_id"],
    output_schema_name=f"{DA.catalog_name}.{DA.schema_name}"
  )

except Exception as lhm_exception:
  print(lhm_exception)

# COMMAND ----------

from databricks.sdk.service.catalog import MonitorInfoStatus

monitor_info = w.quality_monitors.get(processed_table_name)
print(monitor_info.status)

if monitor_info.status == MonitorInfoStatus.MONITOR_STATUS_PENDING:
    print("Wait until monitor creation is completed...")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC モニターアセットは、このディレクトリーに作成されます。 
# MAGIC
# MAGIC ⏰ 予想されるモニターの作成と更新時間: **~7分**

# COMMAND ----------

monitor_info = w.quality_monitors.get(processed_table_name)
assert monitor_info.status == MonitorInfoStatus.MONITOR_STATUS_ACTIVE, "Monitoring is not ready yet. Check back in a few minutes or view the monitoring creation process for any errors."

# COMMAND ----------

# MAGIC %md
# MAGIC **注1:** モニタリングの作成後、更新時間は約 5 分かかります。
# MAGIC
# MAGIC **注2:** ダッシュボードを確実に作成するために、アクセス可能な DBSQL クラスターが起動して稼働していることを確認する

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3: メトリクスの手動更新
# MAGIC
# MAGIC 「メトリックの更新」を実行して、メトリックとダッシュボードを手動で更新できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.4: カタログエクスプローラでのモニターとデータの確認
# MAGIC
# MAGIC モニターが作成されたら、元のテーブルのカタログ ビューで **品質** タブを確認できます。
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC  ![genai-as-04-online-monitoring-quality](../Includes/images/genai-as-04-online-monitoring-quality.png)
# MAGIC
# MAGIC **質問:** どのような情報が表示されますか?
# MAGIC
# MAGIC また、モニターによって生成されたテーブルを確認することもできます。 **時系列**の例では、これらには次のものが含まれます。
# MAGIC
# MAGIC * `*_processed_profile_metrics`
# MAGIC * `*_processed_drift_metrics`
# MAGIC
# MAGIC **質問:** このデータのレコード レベルは何ですか?
# MAGIC
# MAGIC **注:** 更新プロセスが完了し、メトリック テーブルの準備ができていることを確認してください。

# COMMAND ----------

# MAGIC %md
# MAGIC **質問:** ドリフトメトリクステーブルについて何に気づきましたか?

# COMMAND ----------

display(spark.sql(f"SELECT * FROM {monitor_info.drift_metrics_table_name}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Databricks SQL でダッシュボードを調べる
# MAGIC
# MAGIC 前述したように、Lakehouse monitoringは、モニタリングソリューションのデータを確認するためのDatabricks SQLダッシュボードを生成します。
# MAGIC
# MAGIC ダッシュボードへのリンクは、プライマリ テーブルの **品質** タブで直接確認できます。
# MAGIC
# MAGIC このダッシュボードには、モニターに関する次の情報が含まれています。
# MAGIC
# MAGIC * プライマリ名
# MAGIC * 全体的な要約統計量
# MAGIC * 時間範囲フィルター
# MAGIC * 時間ベースの指標:
# MAGIC   * テーブルサイズ
# MAGIC   * 数値/カテゴリプロファイル
# MAGIC   * データ完全性
# MAGIC   * ドリフト
# MAGIC
# MAGIC 以下のダッシュボードをご覧ください。
# MAGIC
# MAGIC <br>
# MAGIC
# MAGIC ![dashboard](../Includes/images/dashboard.png)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## まとめ
# MAGIC
# MAGIC このデモでは、推論テーブルの更新を観察することで、デプロイされた AI モデルのオンライン モニターを作成する方法を示しました。 まず、サンプル推論テーブルをインポートし、データ変換を実行して、メトリック計算用のデータセットを準備しました。 次に、メトリクスを計算します。 デモの第 2 部では、処理された推論テーブルにモニターを作成し、メトリックを更新してクエリを実行し、自動作成されたダッシュボードでメトリックを表示する方法を示しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>