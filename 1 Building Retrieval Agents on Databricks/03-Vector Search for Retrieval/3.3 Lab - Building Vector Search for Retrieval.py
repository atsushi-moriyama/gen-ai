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

# DBTITLE 1,はじめにとタスク
# MAGIC %md
# MAGIC # ラボ - 検索用Vector Searchの構築
# MAGIC
# MAGIC ラボへようこそ！以下の手順に従って、Databricksを使用したドキュメント検索用のVector Searchソリューションの構築方法を学習します。
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このラボでは、parquetファイルに保存されたドキュメントチャンクを使用して、完全なVector Searchソリューションを構築します。**データの準備**、**Vector Searchインデックスの作成**、**Databricks Vector Search機能を使用した様々な種類の検索の実行** 方法を学習します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このラボの終了時には、以下ができるようになります：
# MAGIC 1. parquetデータを **読み込み**、チェンジデータフィードを有効にしたDeltaテーブルとして保存する。
# MAGIC 1. Databricks UIを使用してVector searchインデックスを **作成** する。
# MAGIC 1. 検索実行用のVector searchインデックスを **取得** する。
# MAGIC 1. 精度向上のためのリランキングを使った類似度検索を **実装** する。
# MAGIC 1. 特定のドキュメントをターゲットにするフィルタリング付きハイブリッド検索を **実行** する。
# MAGIC
# MAGIC ## 要件
# MAGIC - 事前作成された **vector search endpoint**。これは事前に作成されています。
# MAGIC - **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC - 必要なライブラリがサーバレスコンピュート設定の **Dependencies** に追加されている。
# MAGIC - Vector searchインデックスの作成と管理に適切な権限。
# MAGIC - 埋め込み生成用のFoundation Model APIへのアクセス。
# MAGIC
# MAGIC
# MAGIC **📌 あなたのタスク: このラボでは、`<FILL_IN>`セクションを適切なコードに置き換えることがあなたのタスクです。**

# COMMAND ----------

# DBTITLE 1,セットアップセクション
# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、教室環境を設定します。この手順により、すべての依存関係が利用可能になり、デモ用のワークスペースが準備されます。

# COMMAND ----------

# DBTITLE 1,教室セットアップ
# MAGIC %run ../Includes/Classroom-Setup-03

# COMMAND ----------

# DBTITLE 1,タスク1: ParquetファイルからDeltaテーブルの作成
# MAGIC %md
# MAGIC ## タスク1: ParquetデータからCDF付きDeltaテーブルの作成
# MAGIC
# MAGIC このセクションでは、**parquetファイルからドキュメントチャンクを読み込み**、チェンジデータフィード (CDF)を有効にしたDeltaテーブルとして保存します。CDFはVector searchの同期に必要です。
# MAGIC
# MAGIC **手順:**
# MAGIC 1. pandasを使用してドキュメントチャンクを含むparquetファイルを読み込む。
# MAGIC 2. Spark DataFrameに変換してDeltaテーブルとして保存する。
# MAGIC 3. テーブルでチェンジデータフィードを有効にする。
# MAGIC 4. サンプルデータを表示してテーブル構造を確認する。
# MAGIC
# MAGIC 以下のコードを完成させて、このタスクを実行してください。

# COMMAND ----------

docs_chunked_lab_3 = f"{catalog}.{schema}.docs_chunked_lab_3"

# COMMAND ----------

## CDFを有効にしたparquetファイルの読み込みとDeltaテーブルの作成
import os
import pandas as pd

## parquetファイルパスの定義
parquet_path = f"/Volumes/{catalog}/{schema}/orion_text/docs_chunked.parquet"

## pandasを使用してParquetファイルを読み込み
pdf = <FILL_IN>

## 競合を避けるため、既存のテーブルがあれば削除
spark.sql(f"DROP TABLE IF EXISTS {docs_chunked_lab_3}")

## pandas DataFrameをSpark DataFrameに変換してUnity Catalogに書き込み
df = spark.createDataFrame(pdf)
df.write.<FILL_IN>

## Vector search同期用のチェンジデータフィードを有効化
spark.sql(f"<FILL_IN>")

print(f"👍 Table '{docs_chunked_lab_3}' created with Change Data Feed enabled.")

# COMMAND ----------

# MAGIC %skip
# MAGIC # CDFを有効にしたparquetファイルの読み込みとDeltaテーブルの作成
# MAGIC import os
# MAGIC import pandas as pd
# MAGIC
# MAGIC # parquetファイルパスの定義
# MAGIC parquet_path = f"/Volumes/{catalog}/{schema}/orion_text/docs_chunked.parquet"
# MAGIC
# MAGIC # pandasを使用してParquetファイルを読み込み
# MAGIC pdf = pd.read_parquet(parquet_path)
# MAGIC
# MAGIC # 競合を避けるため、既存のテーブルがあれば削除
# MAGIC spark.sql(f"DROP TABLE IF EXISTS {docs_chunked_lab_3}")
# MAGIC
# MAGIC # pandas DataFrameをSpark DataFrameに変換してUnity Catalogに書き込み
# MAGIC df = spark.createDataFrame(pdf)
# MAGIC df.write.mode("overwrite").option("mergeSchema", "true").saveAsTable(docs_chunked_lab_3)
# MAGIC
# MAGIC # ベクトル検索同期用のChange Data Feedを有効化
# MAGIC spark.sql(f"ALTER TABLE {docs_chunked_lab_3} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
# MAGIC
# MAGIC print(f"👍 テーブル '{docs_chunked_lab_3}' がChange Data Feedを有効にして作成されました。")

# COMMAND ----------

# テーブル構造を理解するためのサンプルデータ表示
display(spark.sql(f"SELECT * FROM {docs_chunked_lab_3} LIMIT 5"))

# COMMAND ----------

# DBTITLE 1,タスク2: UI経由でのベクトル検索インデックス作成
# MAGIC %md
# MAGIC ## タスク2: UIを使用したVector Searchインデックスの作成
# MAGIC
# MAGIC このセクションでは、**Databricks UIを使用してVector Searchインデックスを作成** します。このアプローチは、管理された埋め込みでインデックスを設定するためのユーザーフレンドリーなインターフェースを提供します。
# MAGIC
# MAGIC **UI経由でのインデックス作成手順:**
# MAGIC
# MAGIC 1. 左サイドバーで **Catalog** をクリックしてCatalog Explorerを開く。
# MAGIC 2. カタログとスキーマに移動する。
# MAGIC 3. Deltaテーブル（`docs_chunked_lab_3`）を見つけて選択する。
# MAGIC 4. **Create**（右上）をクリックし、**Vector search index** を選択する。
# MAGIC 5. ダイアログで以下の設定を構成する：
# MAGIC    * **Name:** インデックス名として `docs_chunked_lab_index` を入力
# MAGIC    * **Primary key:** `id`（一意識別子カラム）を選択
# MAGIC    * **Columns to sync:** すべてのカラムを同期するため空白のままにする
# MAGIC    * **Embedding source:** **Compute embeddings** を選択
# MAGIC      - **Embedding source column:** `chunk` を選択
# MAGIC      - **Embedding model:** `databricks-gte-large-en` を選択
# MAGIC    * **Sync computed embeddings:** 埋め込みをテーブルに保存するため **OFF** にする
# MAGIC    * **Vector search endpoint:** endpointを選択する。このendpointが準備されている必要があります。
# MAGIC    * **Sync mode:** **Triggered**（手動同期）を選択
# MAGIC 6. **Create** をクリックしてインデックス作成の進行状況を監視する。
# MAGIC
# MAGIC **⏱️ 待機時間:** インデックス作成は通常2-3分かかります。UIで進行状況を監視できます。
# MAGIC
# MAGIC インデックスが作成されたら、次のタスクに進んでください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク3: Vector searchインデックス詳細の取得
# MAGIC
# MAGIC 作成したVector searchインデックスを取得し、詳細を表示します。

# COMMAND ----------

# DBTITLE 1,タスク3: Vector searchインデックスの取得 # TODO
## 検索実行用のVector searchインデックスを取得

from databricks.vector_search.client import VectorSearchClient

## UI経由で作成したインデックス名を定義
index_name = f"{catalog}.{schema}.docs_chunked_lab_index"

## 後で使用するためのVector Searchクライアントを初期化
vsc = VectorSearchClient(disable_notice=True)

## Vector searchクライアントを使用してインデックスを取得
index = vsc.<FILL_IN>

## インデックス情報を表示
print(index.describe())

# COMMAND ----------

# DBTITLE 1,タスク3: Vector searchインデックスの取得 # ANSWER
# MAGIC %skip
# MAGIC # 検索実行用のベクトル検索インデックスを取得
# MAGIC from databricks.vector_search.client import VectorSearchClient
# MAGIC
# MAGIC # UI経由で作成したインデックス名を定義
# MAGIC index_name = f"{catalog}.{schema}.docs_chunked_lab_index"
# MAGIC
# MAGIC # 後で使用するためのVector Searchクライアントを初期化
# MAGIC vsc = VectorSearchClient(disable_notice=True)
# MAGIC
# MAGIC # ベクトル検索クライアントを使用してインデックスを取得
# MAGIC index = vsc.get_index(index_name=index_name)
# MAGIC
# MAGIC # インデックス情報を表示
# MAGIC print(index.describe())

# COMMAND ----------

# DBTITLE 1,タスク3: リランキング付き類似度検索
# MAGIC %md
# MAGIC ## タスク4: リランキング付き類似度検索
# MAGIC
# MAGIC このセクションでは、**リランキング付き類似度検索を実行** して検索精度を向上させます。リランキングは、最も文脈的に関連性の高い結果を優先するための二次スコアリングステップを適用します。
# MAGIC
# MAGIC **手順:**
# MAGIC 1. 精度向上のためのリランキング付き類似度検索を実行する。
# MAGIC 1. この質問をする：`"How does the motion controller maintain balance during rapid movement?"`
# MAGIC 1. 3つの結果を返す。
# MAGIC 1. 結果を分析してリランキングの影響を理解する。
# MAGIC
# MAGIC 以下のコードを完成させて、このタスクを実行してください。

# COMMAND ----------

# DBTITLE 1,タスク3: 基本的な類似度検索 # TODO
## 精度向上のためのリランキング付き類似度検索を実行

from databricks.vector_search.reranker import DatabricksReranker

query_text = "How does the motion controller maintain balance during rapid movement?"

## リランキング付き類似度検索を実行
reranked_results = index.<FILL_IN>

print("=== Similarity Search with Reranking Results ===")
display(reranked_results)

# COMMAND ----------

# DBTITLE 1,タスク3: 基本的な類似度検索 # ANSWER
# MAGIC %skip
# MAGIC # 精度向上のためのリランキング付き類似度検索を実行
# MAGIC
# MAGIC from databricks.vector_search.reranker import DatabricksReranker
# MAGIC
# MAGIC query_text = "How does the motion controller maintain balance during rapid movement?"
# MAGIC
# MAGIC # リランキング付き類似度検索を実行
# MAGIC reranked_results = index.similarity_search(
# MAGIC     query_text=query_text,
# MAGIC     columns=["path", "chunk"],
# MAGIC     num_results=3,
# MAGIC     reranker=DatabricksReranker(columns_to_rerank=["chunk"])
# MAGIC )
# MAGIC
# MAGIC print("=== リランキング付き類似度検索結果 ===")
# MAGIC display(reranked_results)

# COMMAND ----------

# DBTITLE 1,タスク4: ハイブリッド検索
# MAGIC %md
# MAGIC ## タスク5: フィルター付きハイブリッド検索 – ターゲットドキュメント検索
# MAGIC
# MAGIC このセクションでは、**フィルタリング付きハイブリッド検索を実装** して、セマンティック類似性、キーワードマッチング、ドキュメントターゲティングを組み合わせます。このアプローチは、複数の検索戦略を組み合わせることで、非常に精度の高い結果を提供します。
# MAGIC
# MAGIC 次の質問に答えたいとします：**"A1モデルのバッテリー交換手順を記載した手順書を探してください。"**
# MAGIC
# MAGIC - *純粋なセマンティック（類似度）検索*では、セマンティックに関連しているため、バッテリー充電や熱管理に関する文章が返される可能性があります。
# MAGIC - *"Battery" や "A1" のキーワードフィルターを追加*することで、関連するドキュメントセクションに結果を絞り込みます。
# MAGIC - *ファイル名によるフィルタリング* により、正しいドキュメントからの手順のみを確実に取得できます。
# MAGIC
# MAGIC **手順:**
# MAGIC 1. クエリに対して **ハイブリッド検索** を実行する。
# MAGIC 1. `05_Orion_Maintenance_and_Servicing_Guide_v3.pdf` からの結果のみに **フィルター** する。
# MAGIC 1. **すべてのカラム** で **2つのレコード** を返す。
# MAGIC 1. ハイブリッド検索とフィルターの組み合わせが検索精度をどのように向上させるかを分析する。
# MAGIC
# MAGIC 以下のコードを完成させて、このタスクを実行してください。

# COMMAND ----------

# DBTITLE 1,タスク4: ハイブリッド検索 # TODO
## 特定のドキュメントをターゲットにするフィルタリング付きハイブリッド検索を実行

query_text = "Find procedures that describe battery replacement for the A1 model."

## ドキュメントパスフィルター付きハイブリッド検索を実行
filtered_hybrid_results = index.<FILL_IN>

print("=== Hybrid Search with Filters Results ===")
display(filtered_hybrid_results)

# COMMAND ----------

# DBTITLE 1,タスク4: ハイブリッド検索 # ANSWER
# MAGIC %skip
# MAGIC # 特定のドキュメントをターゲットにするフィルタリング付きハイブリッド検索を実行
# MAGIC
# MAGIC query_text = "Find procedures that describe battery replacement for the A1 model."
# MAGIC
# MAGIC # ドキュメントパスフィルター付きハイブリッド検索を実行
# MAGIC filtered_hybrid_results = index.similarity_search(
# MAGIC     query_text=query_text,
# MAGIC     columns=["id","path", "chunk"],
# MAGIC     query_type="hybrid",
# MAGIC     filters={"path LIKE": "05_Orion_Maintenance_and_Servicing_Guide_v3.pdf"},  # 安全関連ドキュメントを含むパスでフィルタリング
# MAGIC     num_results=5
# MAGIC )
# MAGIC
# MAGIC print("=== フィルター付きハイブリッド検索結果 ===")
# MAGIC display(filtered_hybrid_results)

# COMMAND ----------

# DBTITLE 1,ハイブリッド検索分析
# MAGIC %md
# MAGIC **💡 分析と考察:**
# MAGIC
# MAGIC **以下の用途にはどの検索方法を選択しますか:**
# MAGIC - ユーザーが特定の手順を検索する技術文書システム？
# MAGIC - 精度が重要な法的リポジトリ？
# MAGIC - 様々なクエリタイプがある顧客サポートナレッジベース？
# MAGIC
# MAGIC **考えてみてください:** 結果に基づいて、本番環境のRAGシステムにはどのアプローチを推奨しますか、そしてその理由は？

# COMMAND ----------

# DBTITLE 1,まとめと次のステップ
# MAGIC %md
# MAGIC ## まとめと次のステップ
# MAGIC
# MAGIC Databricksを使用したドキュメント検索用のvector search索ソリューション構築のラボを完了しました。以下のことを学習しました：
# MAGIC
# MAGIC * parquetからの読み込みとチェンジデータフィードを有効にしたDeltaテーブルの作成によるドキュメントデータの **準備**。
# MAGIC * 管理された埋め込みを使用したDatabricks UIでのvector searchインデックスの **作成**。
# MAGIC * 検索精度を向上させるリランキング付き類似度検索の **実装**。
# MAGIC * セマンティック類似性とキーワードマッチングを組み合わせたハイブリッド検索の **実行**。
# MAGIC * 特定のドキュメントをターゲットにして検索範囲を絞り込むフィルターの **適用**。
# MAGIC
# MAGIC **次のステップ（オプション）:**
# MAGIC * 異なる埋め込みモデルを探索し、**多言語およびドメイン固有** の埋め込みモデルを実験する。
# MAGIC * エンドポイント設定、埋め込み次元、更新モードがレイテンシとコストにどのように影響するかを調査する。
# MAGIC * ユーザーの認証情報に基づいて行を取得する方法を調査する。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>