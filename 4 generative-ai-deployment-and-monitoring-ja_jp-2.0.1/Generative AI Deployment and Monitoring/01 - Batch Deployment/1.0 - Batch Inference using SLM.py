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
# MAGIC # SLMを使用したバッチ推論
# MAGIC
# MAGIC この例では、本番環境でバッチ推論用に **Small Language Model (SLM)** を使用してベースのパイプラインを実装するためのいくつかの重要な手順について説明します。
# MAGIC
# MAGIC **このワークフローに関する注意事項:**
# MAGIC
# MAGIC ** このノートブックとモジュラースクリプトの比較**: このデモは 1 つのノートブックに含まれているため、開発から運用までのワークフローをノートブック セクションに分割します。 より現実的な LLM運用 の設定では、これらのセクションは別々のノートブックやスクリプトに分割される可能性が高いです。
# MAGIC
# MAGIC ** モデルとコードのプロモート**: 開発から本番運用までの道のりは、Model Registry で追跡します。 つまり、コードをプロモートするのではなく、本番運用に向けてモデルをプロモートしているのです。
# MAGIC
# MAGIC ## 学習の目標
# MAGIC
# MAGIC このデモを完了すると、次のことができるようになります。
# MAGIC
# MAGIC 1. Model registryからモデルをバッチ推論のために読み込む。
# MAGIC
# MAGIC 1. モデル エイリアスを管理し、モデルの最新バージョンを取得することができます。
# MAGIC
# MAGIC 1. 単一ノードのバッチ推論を使用して、Spark DataFrame にバッチ推論を適用することができます。
# MAGIC
# MAGIC 1. `spark_udf`を使用してマルチノードのバッチ推論を適用することができます。
# MAGIC
# MAGIC 1. バッチ推論の他の方法を説明する。

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
# MAGIC 必要なライブラリをインストールします。

# COMMAND ----------

# MAGIC %pip install -qq -U "huggingface-hub<1.0" datasets

# COMMAND ----------

# MAGIC %md
# MAGIC デモを開始する前に、提供されているクラスルーム セットアップ スクリプトを実行します。

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-01

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の慣習:**
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
# MAGIC 1. データセットを準備します。
# MAGIC 1. Huggingface/Transformer LLM パイプラインを開発する。
# MAGIC 1. パイプラインをデータに適用/テストし、結果を MLflow Tracking に記録する。
# MAGIC 1. パイプラインを MLflow モデルとして MLflow Tracking サーバーに記録します。
# MAGIC 1. レジストリから LLM パイプラインをロードし、バッチ推論を実行する
# MAGIC 1. SQL `ai_query()` を使用して、既存/サポートされている ファウンデションモデルAPI_モデルに対するバッチ推論を行う

# COMMAND ----------

# MAGIC %md
# MAGIC ## データとモデルの準備 
# MAGIC
# MAGIC このセクションでは、デモの残りの部分で使用するデータセットとモデルを作成します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### データセットの準備
# MAGIC
# MAGIC バッチ推論の実行に使用する [Extreme Summarization (XSum) Dataset](https://huggingface.co/datasets/EdinburghNLP/xsum) から要約するテキストを含む Delta テーブルを準備します。

# COMMAND ----------

import pandas as pd
import requests
import io

prod_data_table_name = f"{DA.catalog_name}.{DA.schema_name}.m4_1_prod_data"

# 解決されたCDN URLを直接使用してください
url = "https://huggingface.co/datasets/EdinburghNLP/xsum/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet"

print("Downloading...")
response = requests.get(url, timeout=120, allow_redirects=True)
print(f"Status: {response.status_code}, Size: {len(response.content)/1024/1024:.1f} MB")

df = pd.read_parquet(io.BytesIO(response.content))
print(f"Loaded {df.shape[0]} rows, columns: {list(df.columns)}")

# デルタテーブルに保存
test_spark_df = spark.createDataFrame(df)
test_spark_df.write.mode("overwrite").saveAsTable(prod_data_table_name)

print(f":white_check_mark: Saved to {prod_data_table_name}")
display(test_spark_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Hugging Face パイプラインを作成する
# MAGIC
# MAGIC このノートブックでは、Hugging Face の <a href="https://huggingface.co/t5-small" target="_blank">T5 Text-to-Text Transfer Transformer </a> を使用します。

# COMMAND ----------

from transformers import pipeline

# Define pipeline inference parameters - to be logged in mlflow as part of model _metadata
hf_model_name = "t5-small"
min_length = 20
max_length = 40
truncation = True
do_sample = True
device_map = "auto" # 'cuda', 'cpu'

cache_dir = "/hf_cache" 

summarizer = pipeline(
    task="summarization",
    model=hf_model_name,
    min_length=min_length,
    max_length=max_length,
    truncation=truncation,
    do_sample=do_sample,
    device_map=device_map,
    model_kwargs={"cache_dir": cache_dir},
)  # Note: We specify cache_dir to use pre-cached models.

# COMMAND ----------

# MAGIC %md
# MAGIC テキストを要約した `summarizer` パイプラインを調べることができます

# COMMAND ----------

text_to_summarize= """ Barrington DeVaughn Hendricks (born October 22, 1989), known professionally as JPEGMafia (stylized in all caps), is an American rapper, singer, and record producer born in New York City and based in Baltimore, Maryland. His 2018 album Veteran, released through Deathbomb Arc, received widespread critical acclaim and was featured on many year-end lists. It was followed by 2019's All My Heroes Are Cornballs and 2021's LP!, released to further critical acclaim. """

summarized_text = summarizer(text_to_summarize)[0]["summary_text"]
print(f"Summary:\n {summarized_text}")
print("===============================================")
print(f"Original Document: {text_to_summarize}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## モデル開発と登録

# COMMAND ----------

# MAGIC %md
# MAGIC ### MLflow を使用して LLM 開発を追跡する
# MAGIC
# MAGIC モデル開発を始める前に、MLflow トラッキングについて簡単に復習しておきます。
# MAGIC
# MAGIC [MLflow](https://mlflow.org/) トラッキングは、開発中にモデルまたはパイプラインの開発を追跡するのに役立ちます。 モデルをフィッティングしなくても、LLM パイプラインに対するクエリーやレスポンスの例を追跡し、そのモデルを [MLflow Model flavor](https://mlflow.org/docs/latest/models.html#built-in-model-flavors) として保存することで、デプロイを簡略化することができます。 
# MAGIC
# MAGIC MLflow Tracking は階層構造になっています。 [experiment](https://mlflow.org/docs/latest/tracking.html#organizing-runs-in-experiments) は、複数の [実行](https://mlflow.org/docs/latest/tracking.html#organizing-runs-in-experiments) を含むプライマリ モデルまたはパイプラインの作成に対応します。 各実行では、パラメーター、メトリック、タグ、モデル、アーティファクト、その他のメタデータがログに記録されます。 パラメーターは `max_length`のような入力であり、メトリックは精度などの評価出力であり、アーティファクトはシリアル化されたモデルのようなファイルです。 [flavor](https://mlflow.org/docs/latest/models.html#storage-format) は、基になる ML ライブラリの形式とメタデータを使用してモデルをシリアル化するための MLflow フォーマットです。 詳細については、[LLM Tracking page](https://mlflow.org/docs/latest/llms/llm-tracking/index.html)を参照してください。 ヒント： 本番コードのベストプラクティスに従い、MLflowの実行を明示的に開始および終了するために、モデル開発ワークフローを `with mlflow.start_run():` でラップします。 詳細は[API doc](https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.start_run)を参照してください。

# COMMAND ----------

import mlflow
from mlflow.models import infer_signature
from mlflow.transformers import generate_signature_output


# It is valuable to log a "signature" with the model telling MLflow the input and output schema for the model.
output = generate_signature_output(summarizer, text_to_summarize)
signature = infer_signature(text_to_summarize, output)
print(f"Signature:\n{signature}\n")


# Set experiment path
# (located on the left hand sidebar under Machine Learning -> Experiments)
model_artifact_path = "summarizer"
experiment_name = f"/Users/{DA.username}/GenAI-As-04-Batch-Demo"
mlflow.set_experiment(experiment_name)
model_artifact_path = "summarizer" # Name of folder containing serialized model

with mlflow.start_run():
    # LOG PARAMS
    mlflow.log_params(
        {
            "hf_model_name": hf_model_name,
            "min_length": min_length,
            "max_length": max_length,
            "truncation": truncation,
            "do_sample": do_sample,
        }
    )

    # ---------
    # LOG MODEL
    # We next log our LLM pipeline as an MLflow model.
    # This packages the model with useful metadata, such as the library versions used to create it.
    # This metadata makes it much easier to deploy the model downstream.
    # Under the hood, the model format is simply the ML library's native format (Hugging Face for us), plus metadata.

    # For mlflow.transformers, if there are inference-time configurations,
    # those need to be saved specially in the log_model call (below).
    # This ensures that the pipeline will use these same configurations when re-loaded.
    inference_config = {
        "min_length": min_length,
        "max_length": max_length,
        "truncation": truncation,
        "do_sample": do_sample,
    }

    # Logging a model returns a handle `model_info` to the model metadata in the tracking server.
    # This `model_info` will be useful later in the notebook to retrieve the logged model.
    model_info = mlflow.transformers.log_model(
        transformers_model=summarizer,
        artifact_path=model_artifact_path,
        task="summarization",
        inference_config=inference_config,
        signature=signature,
        input_example="This is an example of a long news article which this pipeline can summarize for you.",
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### MLflow Tracking サーバーにクエリを実行する
# MAGIC
# MAGIC **MLflow トラッキング API**: ログに記録されたモデルを読み込んで、MLflow Tracking サーバーでログに記録されたモデルとメタデータをクエリする方法を簡単に説明します。  プログラムによるアクセスの詳細については、[MLflow API](https://mlflow.org/docs/latest/python_api/mlflow.html) を参照してください。
# MAGIC
# MAGIC **MLflow トラッキング UI**: UI を使用することもできます。  右側のサイドバーで [MLflow experiments](/ml/experiments) をクリックして実行リストを表示するし、進んで Tracking Server UI にアクセスします。  そこでは、ログに記録されたメタデータとモデルを確認できます。  特に、LLMの入力と出力は、モデルアーティファクトの下にCSVファイルとして記録されていることに注意してください。
# MAGIC
# MAGIC MLflow UI の GIF:
# MAGIC ![llmops](../Includes/images/llmops.gif)

# COMMAND ----------

# 実験 ID を使用して最新の実行 (モデルをログに記録した) を取得する
experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
runs = mlflow.search_runs([experiment_id])
last_run_id = runs.sort_values("start_time", ascending=False).iloc[0].run_id

# run_idに基づいてモデルURIを構築
model_uri = f"runs:/{last_run_id}/{model_artifact_path}"

# COMMAND ----------

model_uri

# COMMAND ----------

# MAGIC %md
# MAGIC ### モデルをパイプラインとしてロードし直す
# MAGIC
# MAGIC これで、MLflow からパイプラインを [pyfunc](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html) として読み込み、 `.predict()` の方法を使用してサンプルドキュメントを要約できます。

# COMMAND ----------

loaded_summarizer = mlflow.pyfunc.load_model(model_uri=model_uri)
loaded_summarizer.predict(text_to_summarize)

# COMMAND ----------

# MAGIC %md
# MAGIC **注 :** 方法は `.predict()` 一度に複数のドキュメントを処理できます ( `pd.Series()` または `list()` など)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Unity Catalog へのモデルの登録
# MAGIC
# MAGIC パイプラインを Unity-Catalog の Model Registry に登録し、モデルエイリアスを設定して、モデル に ステージング/QAの準備ができている などのラベルを付けます。
# MAGIC
# MAGIC ここでは、**Unity Catalog の Model Registry** を使用して進行状況を追跡します [AWS](https://docs.databricks.com/en/machine-learning/manage-model-lifecycle/index.html) |[Azure](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/manage-model-lifecycle/) |[GCP](https://docs.gcp.databricks.com/en/machine-learning/manage-model-lifecycle/index.html) 
# MAGIC このメタデータとモデル ストアは、モデルを次のように整理します。
# MAGIC * **登録済みモデル** は、レジストリ内の名前付きモデル (3 階層の名前空間規約 ***`catalog.schema.model_name`*** を尊重) であり、この例では要約モデルに対応します。  複数の*バージョン*を持つことができます。
# MAGIC    * **モデル バージョン** は、特定のモデルのインスタンスです。  モデルを更新すると、新しいバージョンが作成されます。  各バージョンは、デプロイの特定の段階にあるように指定できます。
# MAGIC       * `@alias`は、デプロイのどの段階 (例:  `challenger` (開発), `champion` (本番), `baseline` または `archived`)を記述する一意の - フリーテキスト - エイリアスです。
# MAGIC
# MAGIC 上記で登録したモデルは、1つのバージョンから始まり、@エイリアスはありません。
# MAGIC
# MAGIC 以下のワークフローでは、ステージをマークするために、特定のモデルバージョンの `@alias` をプログラムで変更/設定します。  Model Registry APIの詳細については、[Model Registry docs](https://mlflow.org/docs/latest/model-registry.html)を参照してください。  または、レジストリを編集し、UI を使用してモデル@エイリアスを設定することもできます。

# COMMAND ----------

from mlflow import MlflowClient

# Model registryでモデル名を定義
model_name = f"{DA.catalog_name}.{DA.schema_name}.summarizer"

# Unity-Catalog レジストリをポイントし、アーティファクトをログ/プッシュします
mlflow.set_registry_uri("databricks-uc")
mlflow.register_model(
    model_uri=model_uri,
    name=model_name,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## モデルステージの管理
# MAGIC
# MAGIC 最新のモデルバージョンを`@champion`として設定する

# COMMAND ----------

def get_latest_model_version(model_name_in):
    """
    Helper method to programmatically get latest model's version from the registry
    """
    client = MlflowClient()
    model_version_infos = client.search_model_versions("name = '%s'" % model_name_in)
    return max([model_version_info.version for model_version_info in model_version_infos])

# COMMAND ----------

# @aliasを設定
client = mlflow.tracking.MlflowClient()
current_model_version = get_latest_model_version(model_name)

client.set_registered_model_alias(
  name=model_name, alias="champion",
  version=current_model_version
  )

# COMMAND ----------

# MAGIC %md
# MAGIC ## バッチ推論用の本番運用ワークフローの作成
# MAGIC
# MAGIC 本番環境での目標は、(a)将来のスケーリング需要を満たすことができるスケールアウトコードを記述すること、および(b)MLflow を使用してモデルに依存しないデプロイコードを記述することでデプロイを簡素化することです。  ステップバイステップで、以下の手順を踏みます。
# MAGIC * Model Registry から最新の本番運用 LLM パイプラインを読み込む。
# MAGIC * パイプラインを Apache Spark DataFrame に適用する。
# MAGIC * Delta Lake テーブルに結果を追加する。
# MAGIC
# MAGIC ここでは、Apache Spark DataFrames と Delta Lake フォーマットを使用したバッチ推論を示します。  Spark では、高スループットで低コストのジョブのシンプルなスケールアウト推論が可能で、Delta では ACID トランザクションを使用して推論結果テーブルに追加したり、変更したりできます。  これらのテクノロジの詳細については、[Apache Spark ページ](https://spark.apache.org/) と [Delta Lake ページ](https://delta.io/) を参照して、更なる情報を得てください。
# MAGIC
# MAGIC *モデル URI*: 以下では、モデル URI を使用して、参照しているモデルとバージョンを MLflow に伝えます。  MLflow Model Registry の一般的な URI パターンは、次の 2 つです。
# MAGIC * `f"models:/{model_name}/{model_version}"` 特定のモデルバージョンを番号で参照する場合
# MAGIC * `f"models:/{model_name}@{alias}"` 一意の @alias を使用してモデルバージョンを参照する場合

# COMMAND ----------

# MAGIC %md
# MAGIC 始める前に、要約する入力テキストをSpark Dataframeにロードしましょう

# COMMAND ----------

prod_data_table = f"{DA.catalog_name}.{DA.schema_name}.m4_1_prod_data"
prod_data_df = spark.read.table(prod_data_table).limit(10)
display(prod_data_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### シングルノードのバッチ処理推論
# MAGIC
# MAGIC 単一ノードのバッチ推論では、ネイティブ `.predict()` 方法を使用できます

# COMMAND ----------

latest_model = mlflow.pyfunc.load_model(
  model_uri=f"models:/{model_name}/{current_model_version}"
)
latest_model

# COMMAND ----------

from pprint import pprint


prod_data_sample_pdf = prod_data_df.limit(2).toPandas()
summaries_sample = latest_model.predict(prod_data_sample_pdf["document"])
[pprint(s+"\n") for s in summaries_sample]

# COMMAND ----------

# MAGIC %md
# MAGIC ### マルチノードバッチ推論
# MAGIC 以下では、 `mlflow.pyfunc.spark_udf`を使用してモデルを読み込みます。  これにより、ビッグデータに効率的に適用できるSparkユーザー定義関数としてモデルが返されます。  デプロイコードはライブラリに依存しないことに注意してください。 モデルが Hugging Face パイプラインであることは一切参照されません。このシンプルなデプロイが可能になるのは、MLflow が環境メタデータをログに記録し、モデルを読み込んで実行する方法を「認識」しているためです。

# COMMAND ----------

# Grab `Champion` モデル (最新の本番運用版と思われる)
prod_model_udf = mlflow.pyfunc.spark_udf(
    spark,
    model_uri=f"models:/{model_name}@champion",
    env_manager="local",
    result_type="string",
)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC 上記の MLflow を使用してモデルを読み込むと、Python 環境に関する警告が表示される場合があります。  開発、ステージング、および本番運用の環境が一致していることを確認することは非常に重要です。
# MAGIC * 今回のデモノートでは、全て同じノートブック環境内で行うため、ライブラリやバージョンを気にする必要はありません。  ただし、本番環境では、保存された MLflow モデルの読み込み中に  `env_manager` 引数 を方法に渡して、環境を再作成するために使用するツールを示す必要があります。
# MAGIC * 本物の本番運用タスクを作成するには、必要なライブラリを必ずインストールしてください。  MLflow は、これらのライブラリとバージョンをログに記録されたモデルと共に保存します。詳細については、[MLflow docs on model storage](https://mlflow.org/docs/latest/models.html#storage-format) を参照してください。  このコースで Databricks を使用しているときに、環境を設定するためのコードを含むサンプル推論ノートを生成することもできます。詳細については、バッチまたはストリーミング推論の [モデル推論ドキュメント](https://docs.databricks.com/machine-learning/manage-model-lifecycle/index.html#use-model-for-inference) を参照してください。

# COMMAND ----------

# DataFrame に新しい列を追加して推論を実行する

batch_inference_results_df = prod_data_df.withColumn("generated_summary", prod_model_udf("document"))
display(batch_inference_results_df)

# COMMAND ----------

prod_data_summaries_table_name = f"{DA.catalog_name}.{DA.schema_name}.m4_1_batch_inference"
batch_inference_results_df.write.mode("append").saveAsTable(prod_data_summaries_table_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## バッチ推論を使用して `ai_query()`
# MAGIC
# MAGIC Databricks FoundationモデルAPIを通じて提供されるLLMを使用して「バッチ風」のジョブを実行する別の一般的な方法は、`ai_query()` **SQL**関数を使用することです [AWS](https://docs.databricks.com/en/sql/language-manual/functions/ai_query.html) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/ai_query)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ai_query_inference AS (
# MAGIC   SELECT
# MAGIC   id
# MAGIC   ,ai_query(
# MAGIC     "databricks-meta-llama-3-3-70b-instruct",
# MAGIC     CONCAT("Based on the following document, provide a summary in less than 100 words. Document: ", document)
# MAGIC   ) as generated_summary
# MAGIC  FROM m4_1_prod_data LIMIT 10
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM ai_query_inference

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## まとめ
# MAGIC
# MAGIC このデモでは、小さな言語モデルを使用してバッチ推論ワークフローを開発しました。 まず、テキストを要約するパイプラインを作成しました。 その後、モデルを開発し、Unity Catalogに登録しました。 モデル開発プロセスを追跡し、追跡サーバーからモデルをクエリし、モデルをパイプラインとしてロードする方法を示しました。 また、@エイリアスを使用してモデルのライフサイクルを管理する方法も示し、バッチ推論の 2 つの方法を紹介して締めくくりました。 シングルノードおよびマルチノードのバッチ推論。 最後に、バッチ推論に`ai_query`を使用する方法を示しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>