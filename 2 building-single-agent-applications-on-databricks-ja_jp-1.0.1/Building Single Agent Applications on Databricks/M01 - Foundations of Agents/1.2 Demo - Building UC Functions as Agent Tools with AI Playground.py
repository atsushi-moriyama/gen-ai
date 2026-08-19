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
# MAGIC # デモ - AI Playgroundを使ったUC関数のエージェントツール構築
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このデモンストレーションでは、AIエージェントのユースケース向けにSQLとPythonの両方を使用してUnity Catalog (UC) 関数を作成し、AI Playgroundを使用してテストする方法に焦点を当てます。
# MAGIC
# MAGIC 現代のAIアプリケーションでは、データと相互作用し、分析タスクを実行できるエージェントが必要です。Unity CatalogのSQLとPython関数の両方を使った関数レジストリを活用することで、UCのガバナンスとセキュリティを、SQLの分析能力とPythonの計算柔軟性を組み合わせた、AIエージェント向けの堅牢でスケーラブルなソリューションを作成できます。
# MAGIC
# MAGIC このデモでは、SQLとPython関数作成の両方の概念を組み合わせ、単一のエージェントワークフロー内で各アプローチの強みを活用する包括的なツールキットの構築方法を実演します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC _このデモの終了時に、以下ができるようになります：_
# MAGIC - エージェントのユースケース向けにUnity CatalogでSQLとPython関数の両方を作成・登録する
# MAGIC - 複数のアプローチを使用してUC関数の初期テストを実行する
# MAGIC - AIエージェントのユースケース向けに適切なコンテキストで関数を装備する方法を理解する
# MAGIC - 複数のツールを使用してAI PlaygroundでUC関数をテストする
# MAGIC - 異なるツールがいつ使用されたかを識別し、エージェントが各ツールタイプをどのように活用したかを理解する
# MAGIC - エージェントworkflowsにおけるSQLツールとPythonツールの強みを比較する
# MAGIC
# MAGIC **注記:** このデモンストレーションでは、UC関数の構築とAI Playgroundを使用してテスト・デプロイできるエージェントツールのベストプラクティスの実装に焦点を当てます。_DSPyやLangChainなどのより高度なframeworksについては扱いません。_

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. クラスルーム設定
# MAGIC
# MAGIC このノートブックの作業環境を設定するために、以下のセルを実行してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバーレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバーレスを使用していることを確認するために、[ノートブックのサーバーレスバージョンの表示と変更に関するドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご参照ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC ワークスペース設定の一部として、いくつかのPythonライブラリがインストールされています。ノートブックスコープライブラリのリストについては、[このドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies#configure-environment-for-job-tasks)をお読みください。特に、以下をインストールしました：
# MAGIC
# MAGIC 1. `unitycatalog-ai[databricks]`: このパッケージは、エージェントがツールとして使用できるUC関数（SQLとPython UDFの両方）を作成・管理するためのインフラストラクチャとツールを提供します。
# MAGIC
# MAGIC このデモンストレーションでは、関数をテストするためにAI Playgroundを使用します。これは、ツール呼び出しエージェントのプロトタイピング用のノーコードインターフェースを提供します。高度なframework統合の詳細については、[Unity Catalogツール統合ドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unity-catalog-tool-integration)をご覧ください。

# COMMAND ----------

!pip install unitycatalog-ai[databricks]==0.3.2
%restart_python

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-1.2

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. Airbnbデータセットの検査
# MAGIC クラスルーム設定の一部として、AirbnbデータセットがUnity Catalog内のDeltaテーブルとして処理・保存されています。次のセルを実行して、データセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('sf_airbnb_listings')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. Databricks Function Clientの初期化
# MAGIC
# MAGIC DatabricksでUC関数を作成、管理、実行するための専用インターフェースである[Databricks Function Client](https://github.com/unitycatalog/unitycatalog/tree/b2d072e56661aedb84cce9be60292b2c54e12224/ai/core#databricks-managed-uc)を初期化します。
# MAGIC
# MAGIC オープンソースUCライブラリを使用したエージェントツールの構築については、[このドキュメント](https://docs.unitycatalog.io/ai/client/#databricks-function-client)をご覧ください。このデモンストレーションでは、SQLとPythonエージェントツールの両方を構築するためのDatabricks管理UCの活用に焦点を当てます。

# COMMAND ----------

from unitycatalog.ai.core.databricks import DatabricksFunctionClient

# client = DatabricksFunctionClient() # クラシックコンピュート用
client = DatabricksFunctionClient(execution_mode="serverless") # サーバーレスコンピュート用

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. UC SQL関数の定義と登録
# MAGIC
# MAGIC コードに入る前に、いくつかの用語を理解することが重要です。
# MAGIC - `SUM` や `AVG` のような組み込み関数はSQL関数ですが、これらは特に **system functions** と呼ばれます。しかし、**SQL function** は、ユーザーによって定義されたものも含め、SQL文で呼び出すことができる任意の再利用可能な計算です。
# MAGIC - Unity Catalogを介して登録された関数は、SQLまたはPythonで記述されているかに関係なく、**user-defined function (UDF)** と見なされます。
# MAGIC
# MAGIC このノートブックでは、UCに登録されている、または登録される関数を意味する **SQL function** または **function** という用語を使用します。つまり、SQL UDFです。
# MAGIC
# MAGIC > Unity CatalogのUDFの詳細については、[このドキュメント](https://docs.databricks.com/aws/en/udf/unity-catalog)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 既存関数の削除
# MAGIC
# MAGIC まず、以下で作成される関数と同じ名前の既存の関数を削除しましょう。

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP FUNCTION IF EXISTS avg_neigh_price;
# MAGIC DROP FUNCTION IF EXISTS airbnb_posting_info;

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. SQLツール1: Airbnbデータ分析
# MAGIC
# MAGIC サンフランシスコのAirbnbリスティングデータを分析するためのエージェントツールとして機能するSQL関数を作成することから始めます。これらの関数には、エージェントがそれらの使用方法を理解するのに役立つ適切なドキュメントが含まれています。このツールは **SQLのみ** で作成されます。
# MAGIC
# MAGIC #### SQL関数の推奨事項
# MAGIC 以下のSQL関数は推奨されるプラクティスに従っています：
# MAGIC 1. **Clear parameter names and types**: 適切なSQLデータ型を使用した説明的なパラメータ名を使用する
# MAGIC 2. **Comprehensive comments**: 関数と各パラメータの両方に `COMMENT` 句を使用して明確な説明を提供する
# MAGIC 3. **Deterministic behavior**: 同じ入力に対して常に同じ結果を返す場合は、関数を `DETERMINISTIC` としてマークする
# MAGIC 4. **Proper return type**: 戻り値のデータ型を明示的に指定する
# MAGIC 5. **Error handling**: 関数ロジックでNULL値などのエッジケースを考慮する

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE FUNCTION avg_neigh_price(
# MAGIC   neighborhood_name STRING COMMENT "The neighborhood name to filter by (e.g., 'Mission', 'Upper Market')"
# MAGIC )
# MAGIC RETURNS DOUBLE
# MAGIC LANGUAGE SQL
# MAGIC DETERMINISTIC
# MAGIC COMMENT 'Calculates the average listing price for a specific neighborhood in San Francisco. Returns the average price as a numeric value. Price strings are cleaned and converted to numeric values before averaging.'
# MAGIC RETURN 
# MAGIC SELECT AVG(CAST(REGEXP_REPLACE(price, '[^0-9.]', '') AS DOUBLE))
# MAGIC FROM sf_airbnb_listings
# MAGIC WHERE neighbourhood_cleansed = neighborhood_name
# MAGIC   AND price IS NOT NULL
# MAGIC   AND REGEXP_REPLACE(price, '[^0-9.]', '') != ''

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. SQL構文を使用したSQLツールのテスト
# MAGIC
# MAGIC AI Playgroundと統合する前に、SQL関数がさまざまな入力で正しく動作することを確認するために、SQLで直接テストしましょう。これにより、関数が期待どおりに動作することを確認できます。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 平均価格関数のテスト
# MAGIC SELECT avg_neigh_price('Mission') AS mission_avg_price

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. UC Python関数の定義と登録
# MAGIC
# MAGIC 次に、SQLだけでは困難または不可能な機能を提供することで、SQL ツールを補完するPython関数を作成します。Python関数により、高度なデータ処理、外部API統合、複雑なビジネスロジックが可能になります。PythonロジックをSQL構文でラップするか、`DatabricksFunctionClient()` を使用するかを選択できます。すでにSQLを使用して関数を作成する方法を実演したため、後者を活用することを選択します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. Pythonエージェントツールのベストプラクティス
# MAGIC
# MAGIC #### 必須プラクティス
# MAGIC
# MAGIC 1. **Explicit type hints**: すべての引数と戻り値に対して常に有効なPython型ヒントを提供します。これはUC関数モデルで必要であり、自動化とLLMの両方が入出力の期待を正しく推論するのに役立ちます
# MAGIC 2. **No variable arguments**: `*args` や `**kwargs` は使用しないでください。すべてのパラメータは明示的に名前付けし、型付けする必要があります
# MAGIC 3. **Supported data types**: 入出力型がPythonとDatabricks SQL/Sparkタイプシステムの両方でサポートされていることを確認します。非互換性を避けるために、Sparkサポートデータ型ドキュメント（[Databricksドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)と[Sparkドキュメント](https://spark.apache.org/docs/latest/sql-ref-datatypes.html)）を参照してください
# MAGIC 4. **Write comprehensive docstrings**: [Google形式のフォーマット](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods)を使用し、関数が何をするか、各引数、戻り値を明確に定義します。関数のdocstringは、LLMとエージェントがルーティングに使用するツールメタデータを生成するために解析されます
# MAGIC     - LLMがツールをいつ使用するかを理解するのに役立つ、意味のある正確な説明を作成する
# MAGIC 5. **Import libraries inside the function**: 関数が外部ライブラリを必要とする場合は、関数本体_内で_それらをインポートします。関数外のインポートは、関数がツールとして呼び出される際のランタイムで解決されません

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. Pythonツール: Airbnbリスティング情報の抽出
# MAGIC
# MAGIC SQLの範囲を超える機能を実演するPython関数を作成します - 外部APIへのHTTPリクエストの実行とHTMLコンテンツの解析。この関数は以下を行います：
# MAGIC
# MAGIC 1. リスティングIDを使用してAirbnb投稿からHTMLコンテンツを取得する
# MAGIC 2. 説明、レビュー数、評価を含む主要情報を抽出・解析する
# MAGIC 3. AIエージェントが簡単に利用できるフォーマットされたテキストを返す

# COMMAND ----------

def airbnb_posting_info(id: int) -> str:
    """
    Fetches Airbnb posting information as formatted text.

    Args:
        id (int): Airbnb listing ID (e.g., 958)

    Returns:
        str: Formatted listing information (description, reviews, and rating) or error message
    """
    import requests
    import re

    api_url = f"https://www.airbnb.com/rooms/{id}"
    
    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # 説明の抽出
            desc = re.search(r'"metaDescription":"([^"]+)"', html)
            if desc:
                description = desc.group(1).replace('\\n', ' ')
                parts = description.split(' · ')
                description = ' · '.join(parts[2:]) if len(parts) > 2 else description
            else:
                description = "Description not found"
            
            # レビュー数と評価の抽出
            reviews = re.search(r'"reviewCount":(\d+)', html)
            rating = re.search(r'"starRating":([\d.]+)', html)
            
            reviews = reviews.group(1) if reviews else "N/A"
            rating = rating.group(1) if rating else "N/A"
            
            return f"""Description: {description}

Reviews: {reviews}
Rating: {rating} stars"""
        else:
            return f'Request failed with status code: {response.status_code}'
    
    except requests.exceptions.RequestException as e:
        return f'Request error: {str(e)}'

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. ノートブックレベルでのPython関数のテスト
# MAGIC
# MAGIC Unity Catalogに関数を登録する前に、ノートブックレベルで期待どおりに動作することを確認するためにテストすることが重要です。これにより、エラーを早期に発見し、出力形式を検証できます。

# COMMAND ----------

info = airbnb_posting_info(958)
print(info)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C4. `DatabricksFunctionClient()`を使用したPythonツールの登録
# MAGIC
# MAGIC 関数が正しく動作することを検証したので、`DatabricksFunctionClient` を使用してUnity Catalogに登録できます。
# MAGIC
# MAGIC `client.create_python_function()` を使用し、以下のパラメータを渡します：
# MAGIC
# MAGIC - **`func`**: 作成したPython関数オブジェクト（`airbnb_posting_info`）
# MAGIC - **`catalog`**: 先ほど `catalog_name` として保存したカタログ名
# MAGIC - **`schema`**: 先ほど `schema_name` として保存したスキーマ名
# MAGIC - **`replace`**: 保存されたPython関数が既に存在する場合に上書きするために `True` に設定

# COMMAND ----------

function_info = client.create_python_function(
  func=airbnb_posting_info,
  catalog=catalog_name,
  schema=schema_name,
  replace=True
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C5. `DatabricksFunctionClient()` を使用したPythonツールのテスト
# MAGIC
# MAGIC `execute_function()` APIを使用してPythonベースの関数をテストし、Unity Catalogを通じて呼び出されたときに正しく動作することを確認しましょう。現在のPythonインタープリターセッション内で定義された関数に対してクエリを実行したときと同じレスポンスを受け取ることに注意してください。

# COMMAND ----------

result = client.execute_function(
    function_name=f"{catalog_name}.{schema_name}.airbnb_posting_info",
    parameters={
        "id": 958
    }
)

print(result.value)

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. AI PlaygroundでのSQLとPythonツールの組み合わせテスト
# MAGIC
# MAGIC SQLとPython関数の両方を作成・テストしたので、AI Playgroundで包括的なツールキットとして一緒に使用し、データ分析と外部情報取得の両方を処理できるインタラクティブなエージェントを作成できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. AI Playground: LLMセットアップ
# MAGIC
# MAGIC 組み合わせたSQLとPython関数をAI Playgroundでエージェントツールとしてテストするには：
# MAGIC
# MAGIC 1. Databricks workspaceから **Playground** に移動します
# MAGIC 2. **Playground** の上部にあるモデル選択ドロップダウンメニューから **Tools enabled** ラベルの付いたモデル（例：`GPT OSS 20B`）を選択します
# MAGIC 3. **Use endpoint** をクリックします

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. エージェントツール装着前後の比較
# MAGIC
# MAGIC ツールを装着する前に、データ分析と外部情報の両方を必要とする複雑な質問をしてみましょう：
# MAGIC > ミッションとリスティングID 958の詳細情報の平均価格を比較してください。どちらがより良い価値を提供しますか？
# MAGIC
# MAGIC ツールなしのレスポンスは限定的で、質問に答えるために必要な追加情報やステップを概説する場合もあります。次に、包括的なツールキットを追加しましょう：
# MAGIC
# MAGIC 1. **Tools > + Add tool** をクリックします
# MAGIC 2. **UC Function** の下で、ツールタイプとして **Hosted Function** をクリックし、`avg_neigh_price` を選択します
# MAGIC 3. 右下の **Save** をクリックします
# MAGIC 5. `airbnb_posting_info` を追加します
# MAGIC 6. すべてのツールが装備されていることを検証します。**Tools** ドロップダウンメニューに **Tools (2)** と表示されるはずです
# MAGIC
# MAGIC 包括的なツールキットが装着されたので、エージェントがどのように異なるツールタイプを知的に選択・組み合わせるかを調べましょう。再度質問してください：
# MAGIC
# MAGIC > ミッションとリスティングID 958の詳細情報の平均価格を比較してください。どちらがより良い価値を提供しますか？
# MAGIC
# MAGIC エージェントが以下のように動作することを観察できます：
# MAGIC 1. **SQLツールを使用** してデータベースから平均価格データを取得
# MAGIC 2. **Pythonツールを使用** して特定のリスティングに関する外部情報を取得
# MAGIC 3. **結果を組み合わせて** 包括的な分析を提供
# MAGIC
# MAGIC エージェントの推論は以下のようなものを示します：
# MAGIC - 最初のツール呼び出し：ミッション平均価格を取得するSQL関数
# MAGIC - 2番目のツール呼び出し：リスティング958の詳細を取得するPython関数
# MAGIC - 両方のデータソースを組み合わせた分析

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC Unity CatalogでSQLとPython関数の両方を組み合わせることで、包括的なAIエージェントツールキットを作成する方法を学習しました。このデモンストレーションを通じて、以下の実践的な経験を得ました：
# MAGIC
# MAGIC - **複数の登録アプローチを使用したSQLとPython UC関数の構築** - AIエージェント向け
# MAGIC - **各アプローチの強みの理解** - データ分析のためのSQLと外部統合・複雑なロジックのためのPython
# MAGIC - **関数を個別に、またまとめてテストする** 直接実行、`DatabricksFunctionClient()`、AI Playgroundなど複数の方法を通じて
# MAGIC - **包括的なエージェントツールキットの作成** データ分析と外部情報の両方を必要とする多様なユーザークエリに対応可能な
# MAGIC - **マルチツールエージェントの動作監視** - エージェントが異なるツールタイプを知的に選択・組み合わせる方法の理解
# MAGIC
# MAGIC Unity Catalogのガバナンスframeworkと、SQLの分析能力、Pythonの計算柔軟性を組み合わせることで、内部データと外部システムの両方とインテリジェントに連携できる、安全でスケーラブルなAIエージェントソリューションを構築できるようになります。この包括的なアプローチにより、エンタープライズガバナンスとセキュリティ基準を維持しつつ、両方の長所を活かした本番環境対応のエージェントツールを作成できます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>