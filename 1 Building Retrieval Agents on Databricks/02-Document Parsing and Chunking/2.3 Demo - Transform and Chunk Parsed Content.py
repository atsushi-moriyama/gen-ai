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
# MAGIC # デモ - 解析されたテキストのクリーニング、変換、チャンク化
# MAGIC
# MAGIC ## 概要
# MAGIC このデモでは、解析されたドキュメントテキストを言語モデルで効果的に使用するための **Clean** と **transform** の方法、そして検索workflowsのためのテキストの **chunk** について学習します。解析されたテキストは現在JSON形式になっており、これをプレーンで清潔なテキストに変換する2つの方法をデモンストレーションします：
# MAGIC
# MAGIC ## 学習目標
# MAGIC このデモの終了時には、以下のことができるようになります：
# MAGIC 1. 解析されたJSONテキストをLLMに適したクリーンなマークダウン形式またはプレーンテキストに **変換** する。
# MAGIC 2. 2つの変換方法を **比較** する：LLMを活用したセマンティッククリーニングと高速連結。
# MAGIC 3. LangChainを使用して、コンテキスト用のオーバーラップを含むページ単位でクリーンなテキストを **チャンク化** する。
# MAGIC 4. 最終的なチャンク化されたテーブルを下流の埋め込みとベクトル検索のために **保存** する。
# MAGIC
# MAGIC ## 要件
# MAGIC * JSON形式の **parsed document table**。このテーブルは前のデモで作成されます。まだ完了していない場合は、**最初にこのデモを完了する必要があります（`2.2 Demo - Parse Documents to Structured Data`）**。
# MAGIC * **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC * 必要なライブラリがサーバーレスコンピュート設定の **Dependencies** に追加されている。

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、教室環境を設定します。このステップにより、すべての依存関係が利用可能になり、ワークスペースがデモの準備完了状態になります。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-02

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 解析されたJSONをクリーンなテキストに変換
# MAGIC
# MAGIC このセクションでは、解析されたJSONテキストを言語モデルで使用する準備ができたクリーンなプレーンテキストに変換します。2つの方法をデモンストレーションします：
# MAGIC
# MAGIC 1. **LLM-powered semantic cleaning** - `ai_query` を使用してバッチ処理し、JSONをマークダウンテキストに変換します。この方法はより多くのドキュメントセマンティクスを保持しますが、コストが高くなる可能性があります。
# MAGIC 2. **Fast concatenation** - すべてのテキスト要素を単一のプレーンテキスト文字列に結合します。この方法は高速でコスト効率的ですが、一部のセマンティック構造（例：ページヘッダー）が失われます。
# MAGIC
# MAGIC *両方の方法で、後のチャンク化と検索workflowsのためにページを分離する`== page ==`トークンを使用します。*

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. 解析されたドキュメントの読み込み
# MAGIC
# MAGIC まず、前のデモで生成された解析済みドキュメントを読み込みましょう。このステップにより、クリーニングと変換に必要な構造化データが確保されます。
# MAGIC
# MAGIC *注意：続行する前に、解析されたテーブルが存在し、最新であることを確認してください。*

# COMMAND ----------

parsed_table = f"{catalog}.{schema}.docs_parsed"
chunked_table = f"{catalog}.{schema}.docs_chunked"

parsed_df = spark.read.table(parsed_table)

print(f"Loaded parsed documents from: {parsed_table}")
parsed_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. ai_queryを使用したLLMを活用したセマンティッククリーニング
# MAGIC
# MAGIC この方法では、`ai_query`関数を使用して解析されたJSONテキストをバッチ処理し、クリーンなマークダウン形式のテキストに変換します。このアプローチは大規模言語モデル（LLM）を活用してドキュメントのセマンティクス（ヘッダー、テーブル、構造など）を保持し、下流のLLMタスクにより有用な出力を生成します。
# MAGIC
# MAGIC - **長所：** より多くの構造と意味を保持し、高品質なマークダウンを生成します。
# MAGIC - **短所：** LLM使用によりコストが高くなる可能性があります。
# MAGIC
# MAGIC **⚠️ 警告**：LLMを活用したクリーニングは、多くのドキュメントを処理する際に高いコストが発生する可能性があります。迅速で低コストな処理には高速連結を使用してください。
# MAGIC
# MAGIC **注意：** `ai_query` 関数はOpenAI、Anthropic、Databricksなど多くの基盤モデルをサポートしています。このデモでは、OpenAIのGPT-5 オープンソースモデルを使用します。
# MAGIC
# MAGIC LLMにJSONを解析してクリーンなマークダウンを出力するよう指示し、ページ間の区切り文字として `== page ==` を使用します。

# COMMAND ----------

# DBTITLE 1,Python: ai_queryで解析されたテキストをバッチ処理
from pyspark.sql.functions import expr

# Databricks基盤モデルを選択（または独自のサービングエンドポイント名）
ENDPOINT = "databricks-gpt-oss-20b"

# LLM用のサンプルプロンプト
prompt_prefix = '''
You are a helpful assistant. Given a JSON object representing a parsed document (with pages, elements, and metadata), convert the content into clean, readable markdown. Use "== page ==" to separate each page. Preserve important structure such as headers, tables, and captions. Do not include any JSON or code blocks in the output—just the clean markdown text.

JSON:

'''

# ai_queryを適用して解析されたJSONテキストをバッチ処理
transformed_df = (
    parsed_df.withColumn(
        "clean_markdown_text",
        expr(f"""
          ai_query(
            '{ENDPOINT}',
            CONCAT('{prompt_prefix}', CAST(parsed_content AS STRING)),
            responseFormat => '{{"type":"text"}}'
          )
        """)
    )
)

display(transformed_df.select("path", "clean_markdown_text"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. 高速プレーンテキスト変換
# MAGIC
# MAGIC この方法では、解析されたJSONからすべてのテキスト要素を単一のプレーンテキスト文字列に迅速に連結します。このアプローチは高速でコスト効率的ですが、ヘッダー、テーブル、キャプションなどのドキュメント構造を犠牲にします。
# MAGIC
# MAGIC - **長所：** 高速、低コスト、実装が簡単。
# MAGIC - **短所：** 重要な構造とセマンティクスが失われます。
# MAGIC
# MAGIC **注意：** Sparkを使用して各ページからテキストを抽出して結合し、後のチャンク化のためにページ間に `== page ==` トークンを挿入します。
# MAGIC
# MAGIC コンテンツ抽出ロジックは `Includes/content_extractor` ファイルに提供されています。

# COMMAND ----------

from pyspark.sql import functions as F

# VARIANT/struct/mapを最初にJSON文字列に変換（VariantVal問題を回避）
safe_json_col = F.coalesce(
    F.to_json(F.col("parsed_content")),
    F.col("parsed_content").cast("string")
)

# UDFを適用
plain_text_df = parsed_df.withColumn(
    "plain_text",
    extract_contents_udf()(safe_json_col)
)

display(plain_text_df.select("path", "plain_text"))


# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 検索のためのクリーンなテキストのチャンク化
# MAGIC
# MAGIC クリーンなページ区切りテキストが得られたので、検索workflowsのためにチャンク化します。チャンク化により、言語モデルとベクトル検索システムが関連情報を効率的に処理・検索できるようになります。
# MAGIC
# MAGIC LangChainの `RecursiveCharacterTextSplitter` を使用して、`== page ==` トークンでテキストを分割します。このユーティリティはチャンク化とオーバーラップを自動的に処理し、埋め込みと検索のためのテキスト準備を簡単にします。
# MAGIC
# MAGIC **注意：** オーバーラップは、単一の入力が複数のチャンクに分割される場合にのみ導入されます。この例では、`chunk_size=2000` で各ページが通常1つのチャンクを形成するため、一部の行ではオーバーラップが表示されない場合があります。オーバーラップするチャンクをより明確に観察するには、チャンクサイズを小さくしてみてください。

# COMMAND ----------

# DBTITLE 1,Python: LangChainを使用してページ単位でプレーンテキストをオーバーラップ付きでチャンク化
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pyspark.sql.types import StructType, StructField, StringType
import pandas as pd

# チャンク化パラメータを設定：chunk_sizeは各チャンクの最大長を制御し、chunk_overlapはチャンク間でのテキストのオーバーラップを許可して検索品質を向上させます。
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

# 推奨される区切り文字でテキストスプリッターを構築。
# このスプリッターは、可能な限りドキュメント構造を保持しながら、ページマーカーまたは他の自然な境界でテキストを分割します。
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n== page ==\n", "== page ==", "\n\n", "\n", " ", ""]
)

# チャンク化されたDataFrameの出力スキーマを定義。
# 各行にはドキュメントパスと単一のテキストチャンクが含まれます。
schema = StructType([
    StructField("path", StringType(), True),
    StructField("chunk", StringType(), True),
])

def split_rows(iterator):
    """
    mapInPandas function: input pdfs with columns [path, plain_text],
    output rows [path, chunk].
    This function splits each document's text into chunks and yields them for DataFrame construction.
    """
    for pdf in iterator:
        out = []
        for _, row in pdf.iterrows():
            path = row["path"]
            text = row["plain_text"]
            if isinstance(text, str) and text.strip():
                for c in splitter.split_text(text):
                    if c and c.strip():
                        out.append((path, c))
        yield pd.DataFrame(out, columns=["path", "chunk"])

# プレーンテキストDataFrameにスプリッターを適用。
# このステップは各ドキュメントを効率的な下流検索と埋め込みのための複数のチャンク化された行に変換します。
df_chunks = (
    plain_text_df
    .select("path", "plain_text")
    .mapInPandas(split_rows, schema=schema)
)

# 検査のためにチャンク化されたDataFrameを表示。
display(df_chunks)

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. チャンク化されたデータをDeltaテーブルに保存
# MAGIC
# MAGIC チャンク化されたテキストデータを下流の埋め込みと検索workflowsのためにDeltaテーブルに保存しましょう。
# MAGIC
# MAGIC **タスク：** チャンク化されたDataFrameをセットアップセクションで **`chunked_table`** として定義されたテーブルに書き込みます。

# COMMAND ----------

# DBTITLE 1,Python: チャンク化されたDataFrameをDeltaテーブルに保存
from pyspark.sql import functions as F

# 保存前に一意の増分ID列を追加
df_chunks = df_chunks.withColumn("id", F.monotonically_increasing_id())

# IDを含むチャンク化されたデータを検索と埋め込み用のDeltaテーブルに保存
df_chunks.write.format("delta").mode("overwrite").option("mergeSchema", "true").saveAsTable(chunked_table)

display(spark.read.table(chunked_table))

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめと次のステップ
# MAGIC
# MAGIC このデモでは、解析されたドキュメントを読み込み、**LLMを活用したセマンティッククリーニング** と **高速プレーンテキスト抽出** の両方を適用し、結果を検索workflows用に **チャンク化** しました。その後、チャンク化されたデータをDeltaテーブルに保存し、埋め込みとvector searchおよびLLMを活用したアプリケーションとの統合の準備を行いました。
# MAGIC
# MAGIC **重要なポイント：**
# MAGIC - LLMを活用したセマンティッククリーニングまたは高速連結を使用してチャンク化のためのテキストを準備する。
# MAGIC - ページ単位でテキストをチャンク化する。
# MAGIC - Vector searchと埋め込みパイプラインとの簡単な統合のために、チャンク化されたデータをDeltaテーブルに保存する。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>