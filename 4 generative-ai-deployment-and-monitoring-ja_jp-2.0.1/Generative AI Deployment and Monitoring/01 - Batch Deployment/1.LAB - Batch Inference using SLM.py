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
# MAGIC # ラボ: SLM を使用したバッチ推論
# MAGIC
# MAGIC このラボでは、本番環境で Small Language Model (SLM) を使用して Batch 推論パイプラインを実装する方法を学習します。 目的は、構造化されたアプローチに従って、MLflow や Unity Catalog などのツールを使用して、言語モデルベースのパイプラインを開発、テスト、デプロイすることです。 このプロセスでは、効果的なモデル管理と運用戦略、Spark DataFrames を使用した Batch 推論の促進、モデルの登録とクエリーによるモデルのライフサイクルの管理に重点が置かれています。
# MAGIC
# MAGIC
# MAGIC **ラボの概要:**
# MAGIC
# MAGIC このラボでは、次のタスクを完了する必要があります。
# MAGIC
# MAGIC 1. **タスク 1:** Hugging Face 質問応答パイプラインを作成し、テストします。
# MAGIC 2. **タスク 2:** MLflow と Unity Catalog を使用してモデルを追跡し、登録する。
# MAGIC 3. **タスク 3:** 登録されたモデルの状態を管理します。
# MAGIC 4. **タスク 4:** シングルノードおよびマルチノードのバッチ推論を実行します。
# MAGIC 5. **タスク 5:** SQL`ai_query`を使用してバッチ推論を実行します 。

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

# MAGIC %pip install -qq -U "huggingface-hub<1.0" datasets

# COMMAND ----------

# MAGIC %pip install mlflow>=3.0 databricks-feature-engineering --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ラボを開始する前に、用意されているクラスルーム設定スクリプトを実行しましょう。 このスクリプトでは、ラボに必要な構成変数を定義します。 次のセルを実行しましょう。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-01

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の慣例:**
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
# MAGIC ## データセットの概要
# MAGIC
# MAGIC このラボでは、HuggingFace でホストされている SQuAD データセットを使用します。 これは、提供されたコンテキストに基づく質問と回答で構成される読解データセットです。 SQuAD データセットの構造を読み込んで調べてみましょう。

# COMMAND ----------

import pandas as pd
import requests
import io
from delta.tables import DeltaTable

prod_data_table_name = f"{DA.catalog_name}.{DA.schema_name}.m4_1_lab_prod_data"

# SQuAD検証用データセットの分割ファイルの直接HTTPダウンロード
url = "https://huggingface.co/datasets/rajpurkar/squad/resolve/refs%2Fconvert%2Fparquet/plain_text/validation/0000.parquet"

print("Downloading SQuAD validation set...")
response = requests.get(url, timeout=120, allow_redirects=True)
print(f"Status: {response.status_code}, Size: {len(response.content)/1024/1024:.1f} MB")

df = pd.read_parquet(io.BytesIO(response.content))
print(f"Loaded {df.shape[0]} rows, columns: {list(df.columns)}")

# デルタテーブルに保存
test_spark_df = spark.createDataFrame(df)
test_spark_df.write.mode("overwrite").saveAsTable(prod_data_table_name)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## タスク 1: LLM パイプラインを開発する
# MAGIC
# MAGIC 事前トレーニング済みモデルを活用して質問に効率的に回答する言語モデル パイプラインを作成しましょう。

# COMMAND ----------

# MAGIC %md
# MAGIC ###1.1: Hugging Face Q&A パイプラインを作成する
# MAGIC 質問応答用に調整された指定モデルを使用して QA パイプラインを初期化しましょう。 このステップでは、「`question-answering`」タスクに最適化されたモデルを選択します。

# COMMAND ----------

##
## transformers ライブラリからパイプライン関数をインポートする
from transformers import pipeline
## モデル名、デバイスマッピング、およびキャッシュディレクトリ用の変数を定義します
hf_model_name = "distilbert-base-cased-distilled-squad"
device_map = "auto"  ## 利用可能な最適なデバイス（CPUまたはGPU）を自動的に使用する
cache_dir = DA.paths.working_dir + "/hf_cache" # /hf_cache ではなく、DA パスを使用してください

## 指定したモデルを使用して、質問応答パイプラインを初期化する
qa_pipeline = pipeline(
    task=<FILL_IN>,  ## タスクの種類を「質問応答」に指定してください
    model=<FILL_IN>,  ## 読み込むモデル
    model_kwargs={"cache_dir": <FILL_IN>},
)

## 例
result = qa_pipeline(
    question="What is Hugging Face?",
    context="Hugging Face is a company that develops tools for machine learning."
)

print(result)

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from transformers import pipeline
# MAGIC
# MAGIC hf_model_name = "distilbert-base-cased-distilled-squad"
# MAGIC device_map = "auto"
# MAGIC cache_dir = DA.paths.working_dir + "/hf_cache"  # /hf_cache ではなく、DA パスを使用してください
# MAGIC
# MAGIC print("Loading QA pipeline...")
# MAGIC qa_pipeline = pipeline(
# MAGIC     task="question-answering",
# MAGIC     model=hf_model_name,
# MAGIC     model_kwargs={"cache_dir": cache_dir},
# MAGIC )
# MAGIC print("✅ Pipeline loaded")
# MAGIC
# MAGIC ## 例
# MAGIC result = qa_pipeline(
# MAGIC     question="What is Hugging Face?",
# MAGIC     context="Hugging Face is a company that develops tools for machine learning."
# MAGIC )
# MAGIC
# MAGIC print(result)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ###1.2: 質問応答パイプラインのテスト
# MAGIC 定義済みの質問とコンテキストを実行してパイプラインの機能を検証し、モデルがどのように解釈して応答するかを観察します。

# COMMAND ----------

##
## モデルが回答を検索するコンテキスト文字列を定義する
context = """Marie Curie was a Polish and naturalized-French physicist and chemist who conducted pioneering research on radioactivity. She was the first woman to win a Nobel Prize and the first person and only woman to win the Nobel prize twice in different scientific fields."""

## 与えられたコンテキストに基づいて回答する質問を定義します
question = "Why is Marie Curie famous?"

## 質問応答用パイプラインを使用して、コンテキストから質問に対する回答を見つける
answer = qa_pipeline(<FILL_IN>)

## 質問と回答を出力する
print(f"Question: <FILL_IN>")

print(f"Answer: <FILL_IN>")
print("===============================================")

## コンテキストを出力して、モデルが答えを見つけるのに使用したコンテンツを表示します
<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC ## モデルが回答を検索するコンテキスト文字列を定義する
# MAGIC context = """Marie Curie was a Polish and naturalized-French physicist and chemist who conducted pioneering research on radioactivity. She was the first woman to win a Nobel Prize and the first person and only woman to win the Nobel prize twice in different scientific fields."""
# MAGIC
# MAGIC ## 与えられたコンテキストに基づいて回答する質問を定義します
# MAGIC question = "Why is Marie Curie famous?"
# MAGIC
# MAGIC ## 質問応答用パイプラインを使用して、コンテキストから質問に対する回答を見つける
# MAGIC answer = qa_pipeline(question=question, context=context, token_type_ids=None)
# MAGIC
# MAGIC ## 質問と回答を出力する
# MAGIC print(f"Question: {question}")
# MAGIC
# MAGIC print(f"Answer: {answer['answer']}")
# MAGIC print("===============================================")
# MAGIC
# MAGIC ## コンテキストを出力して、モデルが答えを見つけるのに使用したコンテンツを表示します
# MAGIC print(f"Context: {context}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 2: モデルの開発と登録
# MAGIC MLflow を使用して開発したモデルを記録し、ライフサイクル管理のために Unity Catalog に登録します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1: MLflow を使用して LLM 開発を追跡する
# MAGIC
# MAGIC モデルのパラメーター、構成、出力を MLflow に記録して、実験、バージョン管理、再現性を追跡します。

# COMMAND ----------

##
## Model trackingに必要な MLflow と関連ライブラリモジュールをインポートする
import mlflow
from mlflow.models import infer_signature
from mlflow.transformers import generate_signature_output

## QAパイプラインを使用して、モデルシグネチャで使用する特定の入力に対してモデル出力を生成する
output = generate_signature_output(<FILL_IN>)

## モデルの入力スキーマと出力スキーマを定義するモデルシグネチャを推論する
signature = infer_signature(<FILL_IN>)

## MLflow で実験の名前を設定する
experiment_name = f"/Users/{DA.username}/GenAI-As-04-Batch-Demo"
mlflow.set_experiment(<FILL_IN>)

## MLflow Artifacts リポジトリ内でモデルを保存するパスを定義する
model_artifact_path = "qa_pipeline"

## MLflow の実行を開始してパラメーター、アーティファクト、モデルをログする
with mlflow.start_run():
    ## モデルで使用されるパラメータをログする。ここで、モデル名
    <FILL_IN>,
    })

    ## ロギングの目的で推論構成を定義し、他の構成を含めることができます
    <FILL_IN>,
    }

    ## モデルを、その構成、シグネチャ、および使用例とともにログする
    model_info = mlflow.transformers.log_model(
        transformers_model=<FILL_IN>,
        artifact_path=<FILL_IN>h,
        task=<FILL_IN>",  # Type of task for the model
        inference_config=<FILL_IN>, # 推論に使用される構成
        signature=<FILL_IN>, # モデルの入力と出力を定義するシグネチャ
        input_example={"question": "Why is Marie Curie famous?", "context": context},  # Example of input
    )

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC
# MAGIC ## モデル追跡に必要な MLflow と関連ライブラリモジュールをインポートする
# MAGIC import mlflow
# MAGIC from mlflow.models import infer_signature
# MAGIC from mlflow.transformers import generate_signature_output
# MAGIC
# MAGIC ## QAパイプラインを使用して、モデルシグネチャで使用する特定の入力に対してモデル出力を生成する
# MAGIC output = generate_signature_output(qa_pipeline, {"question": question, "context": context})
# MAGIC
# MAGIC ## モデルの入力スキーマと出力スキーマを定義するモデルシグネチャを推論する
# MAGIC signature = infer_signature({"question": question, "context": context}, output)
# MAGIC
# MAGIC ## MLflow で実験の名前を設定する
# MAGIC experiment_name = f"/Users/{DA.username}/GenAI-As-04-Batch-Demo"
# MAGIC mlflow.set_experiment(experiment_name)
# MAGIC
# MAGIC ## MLflow アーティファクト リポジトリ内でモデルを保存するパスを定義する
# MAGIC model_artifact_path = "qa_pipeline"
# MAGIC
# MAGIC ## MLflow の実行を開始してパラメーター、アーティファクト、モデルをログする
# MAGIC with mlflow.start_run():
# MAGIC     ## モデルで使用されるパラメータをログする。ここで、モデル名
# MAGIC     mlflow.log_params({
# MAGIC         "hf_model_name": hf_model_name,
# MAGIC     })
# MAGIC
# MAGIC     ## ロギングの目的で推論構成を定義し、他の構成を含めることができます
# MAGIC     inference_config = {
# MAGIC         "hf_model_name": hf_model_name,
# MAGIC     }
# MAGIC
# MAGIC     ## モデルを、その構成、シグネチャ、および使用例とともにログする
# MAGIC     model_info = mlflow.transformers.log_model(
# MAGIC         transformers_model=qa_pipeline,
# MAGIC         artifact_path=model_artifact_path,
# MAGIC         task="question-answering", # モデルのタスクのタイプ
# MAGIC         inference_config=inference_config, # 推論に用いる設定
# MAGIC         signature=signature, # モデルの入力と出力を定義するシグネチャ
# MAGIC         input_example={"question": "Why is Marie Curie famous?", "context": context},  # 入力例
# MAGIC     )

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2: MLflow Tracking サーバー へのクエリー
# MAGIC モデルのパフォーマンスとその他のメトリクスに関する情報を MLflow Tracking サーバーから取得する。

# COMMAND ----------

## 実験名を使用してエクスペリメント ID を取得する
experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
## エクスペリメント ID を使用してエクスペリメントのすべての実行を検索する
runs = mlflow.search_runs([experiment_id])
## 実行を開始時刻の降順で並べ替え、最新の実行の実行 ID を取得
last_run_id = runs.sort_values('start_time', ascending=False).iloc[0].run_id
## 最後の実行 ID と指定されたアーティファクトパスを使用してモデル URI を構築します
model_uri = f"runs:/{last_run_id}/{model_artifact_path}"

# COMMAND ----------

# MAGIC %md
# MAGIC ###2.3: モデルを再度パイプラインとして読み込む
# MAGIC 登録済みモデルを MLflow から読み込み、レジストレーション後にそのパフォーマンスと統合機能を確認します。
# MAGIC

# COMMAND ----------

##
loaded_qa_pipeline = <FILL_IN>
loaded_qa_pipeline.predict(<FILL_IN>)

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC loaded_qa_pipeline = mlflow.pyfunc.load_model(model_uri=model_uri)
# MAGIC loaded_qa_pipeline.predict({"question": question, "context": context})

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.4: Unity Catalog へのモデルの登録
# MAGIC モデルを Unity Catalog に登録すると、バージョン管理が向上し、デプロイ プロセスが容易になります。

# COMMAND ----------

##
from mlflow import MlflowClient
## モデル名の定義
model_name = f"{DA.catalog_name}.{DA.schema_name}.qa_pipeline"
## MLflow レジストリ URI の設定
mlflow.set_registry_uri("databricks-uc")
## MLflow モデルレジストリに、指定した名前とモデル URI でモデルを登録する
mlflow.<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from mlflow import MlflowClient
# MAGIC ## モデル名の定義
# MAGIC model_name = f"{DA.catalog_name}.{DA.schema_name}.qa_pipeline"
# MAGIC ## MLflow レジストリ URI の設定
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC ## MLflow モデルレジストリに、指定した名前とモデル URI でモデルを登録する
# MAGIC mlflow.register_model(model_uri=model_uri, name=model_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 3: LLM モデルの状態管理
# MAGIC このタスクでは、MLflow と Unity Catalog を使用して、さまざまなステージにわたるモデルのライフサイクルを管理します。 MLflow の モデルレジストリ を活用することで、モデルの状態を更新および維持し、追跡、バージョン管理、デプロイの効率を高めることができます。

# COMMAND ----------

# MAGIC %md
# MAGIC ###3.1: 登録済みモデルの検索と点検
# MAGIC 登録済みモデルの最新バージョンを特定して検査し、最新かつ関連するイテレーションを管理していることを確認します。 このステップは、モデルステージまたはエイリアスを設定するためのベースラインを決定するため、非常に重要です。
# MAGIC
# MAGIC - 最新のモデルバージョンを取得する
# MAGIC - モデルエイリアスの設定

# COMMAND ----------

##
def get_latest_model_version(model_name_in):
    ## MLflow クライアントを初期化して MLflow サーバーとやり取りする
    client = MlflowClient()
    
    ## モデルレジストリ で指定したモデルのすべてのバージョンを検索
    model_version_infos = <FILL_IN>
    
    ## バージョン番号を抽出し、最も高い(最新の)バージョンを返す
    return max([model_version_info.version for model_version_info in model_version_infos])

## さらなる操作のためにMLflowクライアントを初期化する
client = mlflow.tracking.MlflowClient()

## 指定したモデルの最新バージョンを取得する
current_model_version = get_latest_model_version(model_name)

## モデルの最新バージョンにエイリアス 'champion' を設定する
client.<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC def get_latest_model_version(model_name_in):
# MAGIC     ## MLflow クライアントを初期化して MLflow サーバーとやり取りする
# MAGIC     client = MlflowClient()
# MAGIC     
# MAGIC     ## モデルレジストリ で指定したモデルのすべてのバージョンを検索
# MAGIC     model_version_infos = client.search_model_versions("name = '%s'" % model_name_in)
# MAGIC     
# MAGIC     ## バージョン番号を抽出し、最も高い(最新の)バージョンを返す
# MAGIC     return max([model_version_info.version for model_version_info in model_version_infos])
# MAGIC
# MAGIC ## さらなる操作のためにMLflowクライアントを初期化する
# MAGIC client = mlflow.tracking.MlflowClient()
# MAGIC
# MAGIC ## 指定したモデルの最新バージョンを取得する
# MAGIC current_model_version = get_latest_model_version(model_name)
# MAGIC
# MAGIC ## モデルの最新バージョンにエイリアス 'champion' を設定する
# MAGIC client.set_registered_model_alias(
# MAGIC     name=model_name, 
# MAGIC     alias="champion", 
# MAGIC     version=current_model_version
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク 4: バッチ推論
# MAGIC 新しいデータに対して登録済みモデルを使用し、シングルノード環境とマルチノード環境の両方で推論を実行してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ###4.1: バッチ推論用にモデルを読み込む
# MAGIC 環境を準備し、バッチ処理のために Unity Catalog からモデルを読み込んでください。

# COMMAND ----------

prod_data_table = f"{DA.catalog_name}.{DA.schema_name}.m4_1_lab_prod_data"
## 指定した Spark テーブルからデータを読み取り、結果を最初の 100 行に制限する
prod_data_df = spark.read.table(prod_data_table).limit(100)
## DataFrame を表示して、データセットの上位 100 行を視覚化します
display(prod_data_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ###4.2: シングルノードのバッチ推論
# MAGIC 限られたデータセットで推論テストを実施し、シングルノード設定でモデルの応答精度と速度を検証します。
# MAGIC

# COMMAND ----------

display(prod_data_df)

# COMMAND ----------

##
## 指定されたモデル URI を使用して、MLflow から最新バージョンのモデルを読み込む
latest_model = mlflow.pyfunc.<FILL_IN>

## DataFrame の最初の 2 行を Pandas DataFrame に変換して操作しやすくする
prod_data_sample_pdf = prod_data_df.limit(2).toPandas()

## モデルが回答する質問のリストを定義する
questions = [<FILL_IN>]

## DataFrameで提供されたコンテキストに各質問に対する回答を生成するためにロードされたモデルを適用する
qa_results = [latest_model.predict({"question": q, "context": doc}) for q, doc in zip(questions, prod_data_sample_pdf["context"])]

## オブジェクトの書式付き表示のためにpprint関数をインポートする
from pprint import pprint

## pprint を使用して読みやすくするために、各結果をフォーマットされた方法で出力します
<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC ## 指定されたモデル URI を使用して、MLflow から最新バージョンのモデルを読み込む
# MAGIC latest_model = mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{current_model_version}")
# MAGIC
# MAGIC ## DataFrame の最初の 2 行を Pandas DataFrame に変換して操作しやすくする
# MAGIC prod_data_sample_pdf = prod_data_df.limit(2).toPandas()
# MAGIC
# MAGIC ## モデルが回答する質問のリストを定義する
# MAGIC questions = ["Which NFL team represented the AFC at Super Bowl 50?", "What is the AFC short for?"]
# MAGIC
# MAGIC ## DataFrameで提供されたコンテキストに各質問に対する回答を生成するためにロードされたモデルを適用する
# MAGIC qa_results = [latest_model.predict({"question": q, "context": doc}) for q, doc in zip(questions, prod_data_sample_pdf["context"])]
# MAGIC
# MAGIC ## オブジェクトの書式付き表示のためにpprint関数をインポートします
# MAGIC from pprint import pprint
# MAGIC
# MAGIC ## pprint を使用して読みやすくするために、各結果をフォーマットされた方法で出力します
# MAGIC print(qa_results)

# COMMAND ----------

# MAGIC %md
# MAGIC ###4.3: マルチノードバッチ推論
# MAGIC Spark を使用して推論プロセスをスケーリングし、実際の大規模なデータ処理シナリオをシミュレートします。
# MAGIC

# COMMAND ----------

##
from pyspark.sql.functions import col

## 入力 DataFrame に 'question' 列と 'context' 列が含まれていることを確認します
prod_data_df = <FILL_IN>
prod_data_df = <FILL_IN>

prod_model_udf = mlflow.pyfunc.spark_udf(
    spark
    model_uri=f"models:/{model_name}@champion",
    env_manager="local",
    result_type="string",
)
batch_inference_results_df = <FILL_IN>
## バッチ推論の結果と生成された回答を含む DataFrame を表示する
<FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC ##
# MAGIC from pyspark.sql.functions import col
# MAGIC
# MAGIC ## 入力 DataFrame に 'question' 列と 'context' 列が含まれていることを確認します
# MAGIC prod_data_df = prod_data_df.withColumn("question", col("question"))
# MAGIC prod_data_df = prod_data_df.withColumn("context", col("context"))
# MAGIC
# MAGIC prod_model_udf = mlflow.pyfunc.spark_udf(
# MAGIC     spark,
# MAGIC     model_uri=f"models:/{model_name}@champion",
# MAGIC     env_manager="local",
# MAGIC     result_type="string",
# MAGIC )
# MAGIC batch_inference_results_df = prod_data_df.withColumn("generated_answer", prod_model_udf("question", "context"))
# MAGIC ## バッチ推論の結果と生成された回答を含む DataFrame を表示する
# MAGIC display(batch_inference_results_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ###4.4: 推論結果を Delta テーブルに書き込む
# MAGIC 推論結果を Delta テーブルに格納して、データの整合性を確保し、さらなる分析を可能にします。
# MAGIC
# MAGIC

# COMMAND ----------

prod_data_summaries_table_name = f"{DA.catalog_name}.{DA.schema_name}.m4_1_lab_batch_inference"
batch_inference_results_df.write.mode("append").saveAsTable(prod_data_summaries_table_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ##タスク 5: `ai_query()`を使用してバッチ推論する
# MAGIC
# MAGIC SQL機能を利用して、SQLクエリを使用してバッチ推論を直接実行し、AI機能を統合して、より広範なアクセシビリティと効率を実現します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.1: SQL バッチ推論の実行
# MAGIC
# MAGIC AI モデルの推論を SQL 内で直接実行する SQL クエリを作成します。 このアプローチでは、SQL の  `ai_query()` 関数を使用して、データセットに対するバッチクエリを処理します。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ###ステップ 1: SQL バッチ推論の実行

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ai_query_inference AS (
# MAGIC   SELECT
# MAGIC     id,
# MAGIC     -- generated_answerとして<FILL_IN>
# MAGIC    FROM m4_1_lab_prod_data LIMIT 100
# MAGIC );

# COMMAND ----------

# MAGIC %skip
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ai_query_inference AS (
# MAGIC   SELECT
# MAGIC     id,
# MAGIC     ai_query(
# MAGIC       "databricks-meta-llama-3-3-70b-instruct",
# MAGIC       CONCAT("Asking question: ", question, " Answer: ", CAST(answers AS STRING))
# MAGIC     ) as generated_answer
# MAGIC   FROM m4_1_lab_prod_data LIMIT 100
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ###5.2: クエリー推論結果
# MAGIC 生成されたテーブルをクエリして、推論結果を表示します。

# COMMAND ----------

# MAGIC %sql
# MAGIC ---- 「ai_query_inference」テーブルからすべてのレコードを取得して結果を表示します
# MAGIC <FILL_IN>

# COMMAND ----------

# MAGIC %skip
# MAGIC %sql
# MAGIC ---- 「ai_query_inference」テーブルからすべてのレコードを取得して結果を表示します
# MAGIC SELECT * FROM ai_query_inference;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC このラボでは、小規模言語モデルを使用したバッチ推論ワークフローの実装に成功しました。 質問応答パイプラインを作成し、MLflow を使用してモデルを追跡して登録し、Unity Catalog でモデルのバージョンとステージを管理し、シングルノードとマルチノードの両方のバッチ推論を実行しました。 最後に、 `ai_query` SQL 関数を使用したバッチ推論の代替方法を探索しました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>