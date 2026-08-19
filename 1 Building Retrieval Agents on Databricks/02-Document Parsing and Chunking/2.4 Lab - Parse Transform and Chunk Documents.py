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
# MAGIC # ラボ - ドキュメントの解析、変換、チャンク化
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このラボでは、指定されたボリュームに保存されている一連のドキュメントを操作します。Pythonと Databricks ツールを使用して、これらのドキュメントを **解析**、**変換**、**チャンク化** する方法を学習します。最終結果は、さらなる分析のためにDeltaテーブルに保存されます。
# MAGIC
# MAGIC ## 学習目標
# MAGIC このラボの終了時には、以下のことができるようになります：
# MAGIC 1. Pythonを使用してドキュメントを **解析** する。
# MAGIC 2. JSON形式から解析されたドキュメントを **平坦化** する。
# MAGIC 3. **AI Query** を使用してJSONをマークダウンに変換する。
# MAGIC 4. 一定のサイズでマークダウンを **チャンク化** する。
# MAGIC 5. 結果をDeltaテーブルに **保存** する。
# MAGIC
# MAGIC ## 要件
# MAGIC - サンプルドキュメントを含むボリューム。これはセットアップコードで作成されます。これはワークスペース設定で行われます。
# MAGIC - **Serverless Compute(environment version 5)**
# MAGIC - 必要なライブラリがサーバーレスコンピュート設定の **Dependencies** に追加されています。
# MAGIC
# MAGIC **📌 あなたのタスク：このラボでは、適切なコードで`<FILL_IN>`セクションを置き換えることがあなたのタスクです。**

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、クラスルーム環境を設定します。
# MAGIC
# MAGIC このステップにより、すべての依存関係が利用可能になり、デモ用にワークスペースが準備されます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-02

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク1：Pythonを使用したドキュメントの解析
# MAGIC
# MAGIC このセクションでは、指定されたボリュームから一連のドキュメントを **ロードして解析** します。Pythonを使用してファイルを読み取り、さらなる処理のためにその内容を解析します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC 1. ボリュームパス用に提供された変数を使用します（例：`docs_path`）。
# MAGIC 2. AIドキュメント解析関数を使用して各ドキュメントを解析します。
# MAGIC 3. 解析結果を `df_raw` という名前のDataFrameに格納します。
# MAGIC
# MAGIC このタスクを実行するために、以下のコードを完成させてください。

# COMMAND ----------

## 指定されたボリューム内のすべてのドキュメントをai_parse_documentを使用して解析
## 解析結果をdf_rawという名前のDataFrameに格納

from pyspark.sql.functions import expr

## ドキュメントボリュームからすべてのファイルをバイナリとして読み取り
files_df = <FILL_IN>

## ai_parse_document（バージョン2.0）を使用して各ドキュメントを解析
df_raw = files_df.<FILL_IN>

## 表示を簡単にするためにバイナリコンテンツ列を削除
result_df = df_raw.drop("content")
display(result_df)

# COMMAND ----------

# MAGIC %skip
# MAGIC # 指定されたボリューム内のすべてのドキュメントをai_parse_documentを使用して解析
# MAGIC # 解析結果をdf_rawという名前のDataFrameに格納
# MAGIC from pyspark.sql.functions import expr
# MAGIC
# MAGIC # ドキュメントボリュームからすべてのファイルをバイナリとして読み取り
# MAGIC files_df = spark.read.format("binaryFile").load(user_docs_path)
# MAGIC
# MAGIC # ai_parse_document（バージョン2.0）を使用して各ドキュメントを解析
# MAGIC df_raw = files_df.withColumn(
# MAGIC    "parsed_content",
# MAGIC    expr(f"ai_parse_document(content, map('version', '2.0', 'imageOutputPath', '{user_docs_path}/parsed_images/'))")
# MAGIC )
# MAGIC
# MAGIC # 表示を簡単にするためにバイナリコンテンツ列を削除
# MAGIC result_df = df_raw.drop("content")
# MAGIC display(result_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク2：解析されたJSONドキュメントの平坦化
# MAGIC
# MAGIC このセクションでは、**解析されたJSONコンテンツを変換** して、より簡単な分析と下流処理のための平坦な表形式構造にします。
# MAGIC
# MAGIC **ステップ：**
# MAGIC 1. `df_raw` の `parsed_content` 列から関連フィールドを抽出します。
# MAGIC 2. `df_flat` という名前の新しいDataFrameを作成します。
# MAGIC 3. 主要なメタデータとページレベル情報の抽出に焦点を当てます。
# MAGIC
# MAGIC このタスクを実行するために、以下のコードを完成させてください。

# COMMAND ----------

## df_rawのparsed_content列を平坦化
## 'elements'フィールドのみをdf_flatに抽出

from pyspark.sql.functions import expr

df_flat = df_raw.<FILL_IN>
display(df_flat)

# COMMAND ----------

# MAGIC %skip
# MAGIC # df_rawのparsed_content列を平坦化
# MAGIC # 'elements'フィールドのみをdf_flatに抽出
# MAGIC from pyspark.sql.functions import expr
# MAGIC
# MAGIC df_flat = df_raw.select(
# MAGIC    "path",
# MAGIC    expr("parsed_content:document:elements").alias("elements")
# MAGIC )
# MAGIC display(df_flat)

# COMMAND ----------

# DBTITLE 1,タスク2：解析されたドキュメントの平坦化 # TODO
# MAGIC %md
# MAGIC ## タスク3：AI Queryを使用したJSONからマークダウンへの変換
# MAGIC
# MAGIC このセクションでは、**ai_query** 関数を使用してJSON要素をクリーンで読みやすいマークダウン形式に変換します。このアプローチでは、大規模言語モデルを活用してヘッダー、テーブル、構造などのドキュメントセマンティクスを保持し、下流のLLMタスクに対してより有用な出力を作成します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC 1. LLMにJSONをマークダウンに変換するよう指示するプロンプトを使用します。
# MAGIC 2. マークダウンの結果をDataFrame `df_markdown` の `markdown` という名前の新しい列に格納します。
# MAGIC
# MAGIC このタスクを実行するために、以下のコードを完成させてください。

# COMMAND ----------

## AI Queryを使用してJSON 'elements'をマークダウンに変換

from pyspark.sql.functions import expr, concat, lit, col

## Databricks基盤モデルendpointを選択
ENDPOINT = <FILL_IN>

## LLM用のプロンプト
prompt_prefix = <FILL_IN>

## ai_queryを適用してエレメントをマークダウンに変換
## プロンプトとエレメントを文字列として連結
## テキスト出力用にresponseFormatを指定
df_markdown = df_flat.<FILL_IN>
display(df_markdown)

# COMMAND ----------

# MAGIC %skip
# MAGIC ## AI Queryを使用してJSON 'elements'をMarkdownに変換
# MAGIC from pyspark.sql.functions import expr, concat, lit, col
# MAGIC
# MAGIC ## Databricks基盤モデルエンドポイントを選択
# MAGIC ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
# MAGIC
# MAGIC ## LLM用のプロンプト
# MAGIC prompt_prefix = '''
# MAGIC You are a helpful assistant. Given a JSON object representing document elements, convert the content into clean, readable markdown. Preserve important structure such as headers, tables, and captions. Do not include any JSON or code blocks in the output—just the clean markdown text.
# MAGIC
# MAGIC JSON:
# MAGIC '''
# MAGIC
# MAGIC ## ai_queryを適用してelementsをMarkdownに変換
# MAGIC ## プロンプトとelementsを文字列として連結
# MAGIC ## テキスト出力用にresponseFormatを指定
# MAGIC df_markdown = df_flat.withColumn(
# MAGIC     "markdown",
# MAGIC     expr(f"ai_query('{ENDPOINT}', CONCAT('{prompt_prefix}', CAST(elements AS STRING)), responseFormat => '{{\"type\":\"text\"}}')")
# MAGIC )
# MAGIC display(df_markdown)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク4：一定サイズでのマークダウンのチャンク化
# MAGIC
# MAGIC このセクションでは、効率的な検索と下流処理のために **マークダウンテキストを固定サイズのチャンクに分割** します。langchain-text-splittersライブラリを使用してチャンク化を実行します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC 1. 一定のチャンクサイズ（例：1000文字）とオーバーラップ（例：200文字）を設定します。
# MAGIC 2. チャンク化された結果を`df_chunks`という名前の新しいDataFrameに格納します。
# MAGIC
# MAGIC このタスクを実行するために、以下のコードを完成させてください。

# COMMAND ----------

## langchain-text-splittersを使用して一定サイズでMarkdownテキストをチャンク化
from pyspark.sql.functions import udf, col, explode
from pyspark.sql.types import ArrayType, StringType
from langchain_text_splitters import RecursiveCharacterTextSplitter

## パラメータ
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

splitter = <FILL_IN>

@udf(ArrayType(StringType()))
def split_md(s: str):
     if not s or not s.strip():
         return []
     return [c for c in splitter.split_text(s) if c and c.strip()]

## 分割されたマークダウンをチャンクに展開
df_chunks = df_markdown.<FILL_IN>

display(df_chunks)

# COMMAND ----------

# MAGIC %skip
# MAGIC ## langchain-text-splittersを使用して一定サイズでMarkdownテキストをチャンク化
# MAGIC from pyspark.sql.functions import udf, col, explode
# MAGIC from pyspark.sql.types import ArrayType, StringType
# MAGIC from langchain_text_splitters import RecursiveCharacterTextSplitter
# MAGIC
# MAGIC
# MAGIC ## パラメータ
# MAGIC CHUNK_SIZE = 1000
# MAGIC CHUNK_OVERLAP = 200
# MAGIC
# MAGIC
# MAGIC splitter = RecursiveCharacterTextSplitter(
# MAGIC     chunk_size=CHUNK_SIZE,
# MAGIC     chunk_overlap=CHUNK_OVERLAP
# MAGIC )
# MAGIC
# MAGIC
# MAGIC @udf(ArrayType(StringType()))
# MAGIC def split_md(s: str):
# MAGIC     if not s or not s.strip():
# MAGIC         return []
# MAGIC     return [c for c in splitter.split_text(s) if c and c.strip()]
# MAGIC
# MAGIC
# MAGIC df_chunks = df_markdown.select("path", explode(split_md("markdown")).alias("chunk"))
# MAGIC display(df_chunks)

# COMMAND ----------

# MAGIC %md
# MAGIC ## タスク5：結果をDeltaテーブルに保存
# MAGIC
# MAGIC このセクションでは、下流の分析と検索workflowsのために **チャンク化されたマークダウン結果** をDeltaテーブルに保存します。
# MAGIC
# MAGIC **ステップ：**
# MAGIC 1. 提供されたカタログとスキーマ変数を使用して出力テーブル名を定義します。
# MAGIC 2. 上書きモードを使用してDataFrame `df_chunks` をDeltaテーブルに書き込みます。
# MAGIC
# MAGIC このタスクを実行するために、以下のコードを完成させてください。

# COMMAND ----------

## 下流分析のためにチャンク化された結果をDeltaテーブルに保存

## カタログとスキーマ変数を使用して出力テーブル名を定義
output_table = f"{catalog}.{schema}.lab_chunked_docs"

## DataFrameをDeltaテーブルに書き込み
## テーブルが既に存在する場合は上書き
df_chunks.<FILL_IN>

print(f"✅ Chunked results saved to Delta table: {output_table}")

# COMMAND ----------

# MAGIC %skip
# MAGIC ## 下流分析のためにチャンク化された結果をDeltaテーブルに保存
# MAGIC ## カタログとスキーマ変数を使用して出力テーブル名を定義
# MAGIC output_table = f"{catalog}.{schema}.lab_chunked_docs"
# MAGIC
# MAGIC ## DataFrameをDeltaテーブルに書き込み
# MAGIC ## テーブルが既に存在する場合は上書き
# MAGIC df_chunks.write.format("delta").mode("overwrite").saveAsTable(output_table)
# MAGIC
# MAGIC print(f"✅ チャンク化された結果がDeltaテーブルに保存されました：{output_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめと次のステップ
# MAGIC
# MAGIC PythonとDatabricksツールを使用してドキュメントの解析、変換、チャンク化を行うラボを完了しました。以下のことを学習しました：
# MAGIC
# MAGIC * ボリュームからドキュメントを **解析** し、構造化されたコンテンツを抽出する。
# MAGIC * 解析されたJSONを **平坦化** して関連要素を選択する。
# MAGIC * **AI Query** を使用してJSON要素をマークダウンに変換する。
# MAGIC * 効率的な検索のために一定サイズでマークダウンテキストを **チャンク化** する。
# MAGIC * 下流分析のために最終結果をDeltaテーブルに **保存** する。
# MAGIC
# MAGIC **次のステップ（オプション）：**
# MAGIC * Vector searchやLLMベースの検索を使用してチャンク化されたデータを埋め込み、検索する方法を探索する。
# MAGIC * ワークフローを最適化するために、さまざまなチャンクサイズとプロンプトを試す。
# MAGIC * Deltaテーブルをレビューし、ユースケースの結果を検証する。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>