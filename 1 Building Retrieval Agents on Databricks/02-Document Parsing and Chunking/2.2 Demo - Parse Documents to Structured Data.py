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
# MAGIC # デモ - ドキュメントを構造化データに解析
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このデモでは、Databricksの **AI-powered document parsing** 機能を使用して、非構造化ドキュメントを構造化データに解析する方法を探ります。このプロセスにより、ボリュームに保存されたファイルからテーブル、画像、テキストを抽出し、分析、検索、および下流のworkflowsの構築を容易にできます。
# MAGIC
# MAGIC ほとんどの実世界の検索エージェントのユースケースでは、構造化された知識ベースを作成するために解析が必要なドキュメントに遭遇します。この知識ベースは、言語モデルに追加のコンテキストを提供するために使用できます。
# MAGIC
# MAGIC ## 学習目標
# MAGIC このデモの終了時には、以下のことができるようになります：
# MAGIC - SQLとPythonの両方で `ai_parse_document()` 関数を使用してマルチフォーマットドキュメント（PDF、DOCX）を **解析** する。
# MAGIC - 解析された出力スキーマを **検査** し、理解する。
# MAGIC - 解析された出力の主要なメタデータフィールドを **特定** し、解釈する。
# MAGIC - 解析されたドキュメントコンテンツを **可視化** し、デバッグする。
# MAGIC
# MAGIC ## 要件：
# MAGIC - サンプルドキュメントを含むボリューム。**これはセットアップコードで作成されます**
# MAGIC - **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC - 必要なライブラリがサーバーレスコンピュート設定の **Dependencies** に追加されています。
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のセルを実行して、クラスルーム環境を設定します。サンプルドキュメントを含み、このデモで使用されるボリューム名が以下に出力されます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-02

# COMMAND ----------

# MAGIC %md
# MAGIC ボリュームに保存されているPDFファイルの1つを表示するために、以下の手順を完了してください。上記に出力されたボリューム名を使用して、これらの手順に従ってください。
# MAGIC
# MAGIC 1. ワークスペースサイドバーで、*Catalog* をクリックしてデータエクスプローラを開きます。
# MAGIC 1. 環境に適した **Catalog** を選択します。
# MAGIC 1. カタログ内の関連する **Schema（`datasets`）** を展開します。
# MAGIC 1. **orion-docs** ボリュームを見つけて展開します。
# MAGIC 1. **01_Orion_A1_Product_Overview.pdf** ファイルをローカルマシンにダウンロードします。
# MAGIC 1. ファイルを開き、解析前にドキュメントを理解するためにその内容を確認します。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. AIによるドキュメント解析
# MAGIC
# MAGIC このセクションでは、`ai_parse_document` 関数を使用して非構造化ドキュメントから構造化データを抽出する方法を学びます。この関数はDatabricks Mosaic AIを活用して、PDFや画像などのファイルからテキスト、テーブル、画像を自動的に識別・抽出します。SQLとPythonの両方のアプローチを実演し、パーサーによって生成される主要なメタデータフィールドについて説明します。この機能は、ドキュメント処理の自動化と高度な分析の実現に価値があります。
# MAGIC
# MAGIC **🚨 注意：** このデモでカバーされる解析フォーマットを取得するには、`ai_parse_document` の **Version 2** を使用する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. Pythonでのドキュメント解析
# MAGIC
# MAGIC **Python** は、柔軟でインタラクティブなworkflowsと機械学習やカスタムロジックとの統合に理想的です。ここでは、Spark DataFrame APIと `expr` 関数を使用して、各ファイルで `ai_parse_document` を呼び出します。これにより、結果を検査し、さらなる変換を適用したり、MLパイプラインを構築したりできます。
# MAGIC
# MAGIC コードの実行後、DataFrameの出力を確認して、各ドキュメントがどのように解析されるかを確認してください。ボリュームが空の場合は、パスと権限を確認してください。
# MAGIC
# MAGIC `ai_parse_document` 関数は以下のようなオプションを受け入れます：
# MAGIC - **`version`**: 使用するパーサーバージョン（例：`'2.0'`）。
# MAGIC - **`imageOutputPath`**: 抽出された画像を保存する場所。
# MAGIC - **`descriptionElementTypes`**: 抽出する要素（例：`*`、`table`、`image`、`text`）。
# MAGIC
# MAGIC
# MAGIC **注意：** `display`関数が結果を表示しないため、バイナリコンテンツフィールドを削除しています。バイナリフィールドは表示するには長すぎます。

# COMMAND ----------

# DBTITLE 1,ai_parse_document Python例（コード）
from pyspark.sql.functions import expr

# ドキュメントボリュームからすべてのファイルを読み取る
docs_df = spark.read.format("binaryFile").load(user_docs_path)

# ai_parse_documentを使用して各ドキュメントを解析（SQL関数には 'expr' を使用）
parsed_df = docs_df.withColumn("parsed_content", 
                               expr(f"""ai_parse_document(content, map(
                                    "version", "2.0",
                                    "imageOutputPath", "{user_docs_path}/parsed_images/"
                                   ))""")
                              )
# バイナリコンテンツを削除
parsed_df = parsed_df.drop("content")

# 解析結果のサンプルを表示
display(parsed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ボリュームパス内のファイルをリストします。
# MAGIC
# MAGIC   デモに使用された元のPDFファイルと、解析中に生成されたすべての出力画像を保持する新しい `/parsed_images/` ディレクトリの両方が含まれていることに注意してください。

# COMMAND ----------

spark.sql(f"LIST '{user_docs_path}'").display()

# COMMAND ----------

# MAGIC %md
# MAGIC 以下のセルを実行し、ボリューム内の `/parsed_images/` ディレクトリに一連の出力画像が含まれていることを確認してください。

# COMMAND ----------

spark.sql(f"LIST '{user_docs_path}/parsed_images'").display()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. SQLでの解析
# MAGIC
# MAGIC **SQL** は、バッチ処理とLakehouseテーブルとの簡単な統合に適しています。以下の例では、指定されたボリューム内のすべてのドキュメントを解析し、構造化された結果を返します。
# MAGIC
# MAGIC このアプローチは、スケジュールされたジョブや結果をテーブルに永続化したい場合に理想的です。
# MAGIC
# MAGIC **注意：** 画像出力パスが定義されていない場合、前回の解析中に抽出された画像も解析されます。

# COMMAND ----------

# DBTITLE 1,ai_parse_document SQL例（コード）
parsed_df_sql = spark.sql(f"""
SELECT
  path,
  ai_parse_document(
    content,
    map(
      'version', '2.0'
    )
  ) as parsed_doc
FROM read_files('{user_docs_path}', format => 'binaryFile')""")

display(parsed_df_sql)

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. 解析されたドキュメントメタデータの理解
# MAGIC
# MAGIC `ai_parse_document` の出力には、`parsed_content` フィールドに豊富なメタデータ構造が含まれています。**主要なフィールドには以下が含まれます：**
# MAGIC
# MAGIC - **`parsed:document:pages`**: ページオブジェクトのリスト、それぞれに以下が含まれます：
# MAGIC   - **`page_number`**: ドキュメント内のページのインデックス。
# MAGIC   - **`text`**: 抽出されたテキストコンテンツ。
# MAGIC   - **`tables`**: 検出された場合の構造化テーブルデータ。
# MAGIC   - **`images`**: 抽出された画像、多くの場合base64またはファイル参照として。
# MAGIC - **`parsed:document:metadata`**: 一般的なドキュメント情報（ファイル名、サイズ、フォーマット）。
# MAGIC
# MAGIC *これらのフィールドを使用して、検索インデックスの構築、レポートの自動化、または下流のMLモデルへの供給を行うことができます。大きなドキュメントの場合は、結果のページ分割やフィルタリングを検討してください。一部のフィールドが欠落している場合は、ドキュメントタイプとパーサーオプションを確認してください。*

# COMMAND ----------

# DBTITLE 1,Python: 解析されたドキュメントメタデータを表示
# ドキュメントパスと主要なメタデータフィールドを表示
from pyspark.sql.functions import expr

# ネストされたフィールドにexprを使用して主要なメタデータフィールドを選択
meta_df = parsed_df.select(
    "path",
    expr("parsed_content:document:pages"),
    expr("parsed_content:document:elements"),
    expr("parsed_content:error_status"),
    expr("parsed_content:corrupted_data"),
    expr("parsed_content:metadata")
)

display(meta_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 解析されたドキュメントコンテンツの表示とデバッグ
# MAGIC
# MAGIC 解析後は、構造化された出力を検査し、デバッグして品質と完全性を確保することが重要です。**Visualization** は、抽出精度を検証し、パーサーが混合コンテンツをどのように処理するかを理解するのに役立ちます。解析結果をレンダリングするヘルパークラスを使用して、各ページからのテキスト、テーブル、画像を確認しやすくします。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 'DocumentRenderer' ヘルパークラスのインポート
# MAGIC
# MAGIC `DocumentRenderer` クラスは、Databricks Notebooks内で解析済みドキュメントコンテンツを可視化するユーティリティです。各ページからのテキスト、表、画像のレンダリングをサポートしており、ドキュメントの品質保証やワークフロー検証において極めて重要です。
# MAGIC
# MAGIC ヘルパークラスは **Includes** フォルダにあるか、インストラクターから提供されます。ここではその実装については説明しません—ワークフローを合理化し、結果の解釈に集中するために使用するだけです。

# COMMAND ----------

# DBTITLE 1,DocumentRendererヘルパークラスをインポート
# DocumentRendererヘルパークラスをインポート
import sys, os
sys.path.append(os.path.abspath('..'))
from Includes.document_renderer import render_ai_parse_output, render_ai_parse_output_interactive

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 解析結果の表示
# MAGIC
# MAGIC 以下のコードは、画像とテーブルの両方を含むドキュメント（利用可能な場合）を選択し、`DocumentRenderer` ヘルパークラスを使用してその解析されたコンテンツを可視化します。抽出されたテキスト、テーブル、画像を含むドキュメントのページの視覚的表現が表示されるはずです。これにより、AIパーサーが下流分析のためにコンテンツをどのように構造化したかをデバッグし、理解することがはるかに容易になります。
# MAGIC
# MAGIC *適切なドキュメントが見つからない場合は、混合コンテンツを含むファイルのボリュームを確認するか、フィルターロジックを調整してください。*

# COMMAND ----------

# DBTITLE 1,1つのドキュメントの解析結果を表示
# サンプルドキュメントを選択し、render_ai_parse_outputを使用してその解析されたコンテンツをレンダリング
sample = parsed_df.select("parsed_content").limit(1).collect()

if sample:
    doc = sample[0]["parsed_content"]
    render_ai_parse_output(doc)
else:
    print("No parsed documents found. Please check your input volume and parsing step.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 解析結果をDeltaテーブルに保存
# MAGIC
# MAGIC 文書を解析・探索したところで、結果を保存して後続の処理に備えましょう。解析された内容は現在JSON形式であるため、検索タスクに効果的に活用するには、**クリーンアップと変換が必要** です。

# COMMAND ----------

# DBTITLE 1,parsed_dfをDeltaテーブルに保存
# 簡単なクエリと共有のために解析結果をDeltaテーブルとして保存
output_table = f"{catalog}.{schema}.docs_parsed"

# テーブルが既に存在する場合は上書き
parsed_df.write.format("delta").mode("overwrite").saveAsTable(output_table)

print(f"✅ Parsed results saved to Delta table: {output_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめと次のステップ
# MAGIC
# MAGIC PythonとSQLの両方でDatabricksのAI搭載 `ai_parse_document` 関数を使用して非構造化ドキュメントを解析する方法を学びました。ファイルのバッチ処理、構造化コンテンツとメタデータの抽出、品質保証のための結果の可視化を実演しました。これらの技術を統合することで、ドキュメント抽出workflowsを自動化し、下流の分析や機械学習タスクのためのデータを準備できます。
# MAGIC
# MAGIC **主要なポイント：**
# MAGIC - PythonとSQLの両方で`ai_parse_document`関数を使用してドキュメント解析を **自動化** する。
# MAGIC - `pages`、`elements`、`metadata`などの主要なメタデータフィールドを含む解析出力スキーマを **検査** し、理解する。
# MAGIC - 品質保証とワークフロー検証のためにDocumentRendererヘルパークラスを使用して解析結果を **可視化** し、デバッグする。
# MAGIC
# MAGIC `ai_parse_document` の詳細については、[公式Databricksドキュメント](https://docs.databricks.com/sql/language-manual/functions/ai_parse_document.html)をご確認ください。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>