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
# MAGIC # ラボ - Unity Catalog関数を使用したAIエージェントツールの構築
# MAGIC
# MAGIC ## 概要 
# MAGIC このハンズオンラボでは、Unity Catalog関数を使用してAIエージェントツールを構築します。PythonとSQL関数の両方を実装し、不適切な関数記述を特定して修正する方法を学び、AI Playgroundを使用してツールをテストします。
# MAGIC
# MAGIC ## 学習目標
# MAGIC _このラボの終了時点で、以下ができるようになります:_
# MAGIC - 適切なドキュメントを含むSQL構文を使用してSQL関数を作成・登録する
# MAGIC - `DatabricksFunctionClient()` を使用してUnity CatalogでPython関数を構築・登録する
# MAGIC - AIエージェントの使用例において不適切な関数記述を特定して修正する
# MAGIC - 複数の方法を使用して両方の関数を独立してテストする
# MAGIC - AI Playgroundを使用してエージェントツールとして両方の関数を検証する
# MAGIC
# MAGIC ### ビジネスコンテキスト
# MAGIC あなたは、NYCタクシートリップに関するAIを活用した洞察を提供したい交通分析会社で働いています。あなたのチームは、エージェントがトリップ分析と料金計算を実行するために使用できる、信頼性があり、ガバナンスの効いたツールを構築する必要があります。これらのツールは正確で、よく文書化されており、ガバナンスとセキュリティのためにUnity Catalogを通じてアクセス可能である必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境設定

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバーレスコンピュートを選択**
# MAGIC
# MAGIC このコースはサーバーレスコンピュート上で実行するように構成されています。従来のコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバーレスを使用していることを確認するため、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC ワークスペースの設定の一環として、いくつかのPythonライブラリがインストールされています。ノートブックスコープのライブラリのリストを見るには、[このドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies#configure-environment-for-job-tasks)をお読みください。特に、以下をインストールしました:
# MAGIC
# MAGIC 1. `unitycatalog-ai[databricks]`: このパッケージは、エージェントがツールとして使用できるUC関数（SQLとPython UDFの両方）を作成・管理するためのインフラストラクチャとツールを提供します。
# MAGIC
# MAGIC このデモンストレーションでは、関数をテストするためにAI Playgroundを使用します。これは、ツール呼び出しエージェントのプロトタイピング用のノーコードインターフェースを提供します。高度なframework統合の詳細については、[Unity Catalogツール統合ドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unity-catalog-tool-integration)をご覧ください。

# COMMAND ----------

!pip install unitycatalog-ai[databricks]==0.3.2 reportlab
%restart_python

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-1.3

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. NYCタクシーデータセットの検査
# MAGIC
# MAGIC このラボで使用されるデータセットは、テーブル `samples.nyctaxi.trips` から取得されます。これは[UC対応workspacesでデフォルトで利用可能](https://docs.databricks.com/aws/en/discover/databricks-datasets)なサンプルデータセットです。次のセルを実行して、データセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('samples.nyctaxi.trips')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. Databricks Function Clientの初期化
# MAGIC
# MAGIC **TODO:** Unity Catalog関数の作成、管理、実行のためのプログラマティックインターフェースを提供するDatabricksFunctionClientを初期化してください。

# COMMAND ----------

## サーバーレスコンピュート用のDatabricksFunctionClientをインポートして初期化
from unitycatalog.ai.core.databricks import <FILL_IN>

client = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクA4: Databricks Function Clientの初期化 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC from unitycatalog.ai.core.databricks import DatabricksFunctionClient
# MAGIC
# MAGIC client = DatabricksFunctionClient(execution_mode="serverless")
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 平均トリップ距離のSQL関数の構築
# MAGIC
# MAGIC まず、以下で作成される関数と同じ名前の既存の関数を削除しましょう。

# COMMAND ----------

# MAGIC %sql
# MAGIC     
# MAGIC DROP FUNCTION IF EXISTS avg_distance_by_zip;
# MAGIC DROP FUNCTION IF EXISTS est_taxi_fare;

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ### B1. SQL関数の作成
# MAGIC
# MAGIC **TODO:** `samples.nyctaxi.trips` テーブルを使用して、特定の乗車郵便番号から出発するトリップの平均トリップ距離を計算するSQL関数を作成してください。
# MAGIC
# MAGIC **要件:**
# MAGIC - 関数名: `avg_distance_by_zip`
# MAGIC - パラメータ: `pickup_zip_code` (INT)
# MAGIC - 戻り値の型: DOUBLE
# MAGIC - 関数とパラメータの両方に適切なCOMMENT句を含める
# MAGIC - DETERMINISTICとしてマークする
# MAGIC - NULL値を適切に処理する
# MAGIC - `samples.nyctaxi.trips` テーブルをクエリする

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC -- -- CREATE OR REPLACE FUNCTIONを使用してSQL関数を作成
# MAGIC CREATE OR REPLACE FUNCTION <FILL_IN>(
# MAGIC   pickup_zip_code <FILL_IN> COMMENT "<FILL_IN>"
# MAGIC )
# MAGIC RETURNS <FILL_IN>
# MAGIC LANGUAGE <FILL_IN>
# MAGIC DETERMINISTIC
# MAGIC COMMENT '<FILL_IN>'
# MAGIC RETURN 
# MAGIC   SELECT <FILL_IN>
# MAGIC   FROM samples.nyctaxi.trips
# MAGIC   WHERE <FILL_IN>
# MAGIC     AND <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC            
# MAGIC ##### タスクB1: SQL関数の作成 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC CREATE OR REPLACE FUNCTION avg_distance_by_zip(
# MAGIC   pickup_zip_code INT COMMENT "The pickup zip code to filter trips by (e.g., 10001 for Midtown Manhattan)"
# MAGIC )
# MAGIC RETURNS DOUBLE
# MAGIC LANGUAGE SQL
# MAGIC DETERMINISTIC
# MAGIC COMMENT 'Calculates the average trip distance in miles for all NYC taxi trips originating from a specific pickup zip code. Returns the average distance as a numeric value.'
# MAGIC RETURN 
# MAGIC   SELECT AVG(trip_distance)
# MAGIC   FROM samples.nyctaxi.trips
# MAGIC   WHERE pickup_zip = pickup_zip_code
# MAGIC     AND trip_distance IS NOT NULL
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. SQL関数のテスト
# MAGIC
# MAGIC **TODO:** 直接SQLクエリを使用してSQL関数をテストし、正しく動作することを確認してください。郵便番号10001（ミッドタウン・マンハッタン）でテストしてください。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC -- -- 郵便番号10001で関数をテスト
# MAGIC SELECT <FILL_IN>(<FILL_IN>) AS avg_distance

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC            
# MAGIC ##### タスクB2: SQL関数のテスト 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC SELECT avg_distance_by_zip(10001) AS avg_distance
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 料金推定のためのPython関数の構築

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. 悪いPythonの例
# MAGIC
# MAGIC **TODO:** AI Playgroundで以下のPython関数をテストしてください。この関数の本来の目的は、距離と時間に基づいてタクシートリップの総料金を推定することです。次のセルを実行してベストプラクティスをバイパスし、コードをUCツールとして即座にプッシュし、テスト用にAI Playgroundを開いてください。
# MAGIC
# MAGIC 関数の定義から分かるように、料金計算式は以下の通りです:
# MAGIC - 基本料金: $3.00
# MAGIC - マイルあたり: $2.50
# MAGIC - 分あたり: $0.50
# MAGIC - 合計 = base_fare + (distance * per_mile_rate) + (time_minutes * per_minute_rate)

# COMMAND ----------

def est_taxi_fare(
    my_param: float, 
    param2: float
) -> float:
    """
    This is my calculation function.
    
    Args:
        my_param: parameter_1
        param2: my second parameter for my function
    
    Returns:
        the answer
    """
    base_fare = 3.00
    per_mile_rate = 2.50
    per_minute_rate = 0.50
    
    total_fare = base_fare + (my_param * per_mile_rate) + (param2 * per_minute_rate)
    return total_fare

function_info = client.create_python_function(
    func=est_taxi_fare,
    catalog=catalog_name,
    schema=schema_name,
    replace=True
)

print("Python function registered successfully!")
print(f"Function name: {function_info.full_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 関数のテスト
# MAGIC **AI Playground** に移動して、ツール `est_taxi_fare()` をアタッチしてください:
# MAGIC
# MAGIC AI PlaygroundでPython関数をエージェントツールとしてテストするには:
# MAGIC
# MAGIC 1. Databricks workspaceから **Playground** に移動します
# MAGIC 1. プレイグラウンドの上部のモデル選択ドロップダウンメニューから **Tools enabled** ラベル付きのモデル（例：`GPT OSS 120B`または他のツール対応モデル）を選択します
# MAGIC 1. **Use endpoint** をクリックしてセッションを開始します
# MAGIC 1. **Tools > + Add tool** をクリックします
# MAGIC 1. **UC Function** の下で、ツールタイプとして **Hosted Function** を選択します
# MAGIC 1. 作成した関数を選択します: `est_taxi_fare`
# MAGIC 1. 右下の **Save** をクリックします
# MAGIC 1. ツールが装備されていることを確認します。**Tools** ドロップダウンメニューに **Tools (1)** が表示されるはずです
# MAGIC 1. 以下の質問を入力し、モデルが意図した通りにツールを使用_しない_ことを観察してください。代わりに、モデルがツール呼び出し_なしで_答えを推論しようとする様子が見えるでしょう。
# MAGIC
# MAGIC > 来週旅行予定で、約20分で7マイルだと思います。いくらかかりますか？
# MAGIC
# MAGIC 答えは以下のように計算されるべきです:
# MAGIC - 基本料金: $3.00
# MAGIC - マイルあたり: $2.50
# MAGIC - 分あたり: $0.50
# MAGIC 合計 = 3 + (7 * 2.5) + (20 * 0.5) = **30.5ドル**
# MAGIC しかし、LLMは（docstringによる不完全な文脈不足のため）最初の入力を2番目の入力と混同し、**56.50ドル** の値を返します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. 不適切な関数記述の特定と修正

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 問題の理解
# MAGIC
# MAGIC 作成したPython関数には不適切な記述があります。例えば、現在のdocstringに基づいて、エージェントは関数が実際に何をするのか、パラメータが何を表すのか、戻り値が何を意味するのかを判断できません。これを修正しましょう。
# MAGIC
# MAGIC **TODO:** 上記の関数のdocstringを確認してください。何が欠けているか、不明確かを特定してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. Python関数記述の修正
# MAGIC
# MAGIC **TODO:** AIエージェントツールのベストプラクティスに従った包括的で詳細なdocstringでPython関数を再定義してください。
# MAGIC
# MAGIC **関数記述のベストプラクティス:**
# MAGIC 1. 関数が何をするかの明確で簡潔な要約
# MAGIC 2. 単位と例を含む詳細なパラメータ記述
# MAGIC 3. 戻り値の説明
# MAGIC 4. この関数をいつ使用するかについてのコンテキスト
# MAGIC 5. 重要な注意事項や制限事項

# COMMAND ----------

## 改良されたdocstringで関数を再定義
def est_taxi_fare(
    distance_miles: float, 
    time_minutes: float
) -> float:
    """
    TODO: Write a comprehensive docstring that includes:
    - Clear description of what the function does
    - Detailed parameter descriptions with units and examples
    - Clear return value description
    - Context about the fare calculation method
    
    Args:
        distance_miles: <FILL_IN>
        time_minutes: <FILL_IN>
    
    Returns:
        <FILL_IN>
    """
    base_fare = 3.00
    per_mile_rate = 2.50
    per_minute_rate = 0.50
    
    total_fare = base_fare + (distance_miles * per_mile_rate) + (time_minutes * per_minute_rate)
    return total_fare

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD2: Python関数記述の修正 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC def est_taxi_fare(
# MAGIC     distance_miles: float, 
# MAGIC     time_minutes: float
# MAGIC ) -> float:
# MAGIC     """
# MAGIC     Estimates the total fare for a NYC taxi trip based on distance and duration.
# MAGIC     
# MAGIC     This function calculates the estimated fare using NYC taxi rate structure:
# MAGIC     - Base fare: $3.00
# MAGIC     - Distance rate: $2.50 per mile
# MAGIC     - Time rate: $0.50 per minute
# MAGIC     
# MAGIC     Use this function to provide fare estimates before a trip or to validate fare calculations.
# MAGIC     
# MAGIC     Args:
# MAGIC         distance_miles (float): The trip distance in miles (e.g., 5.5 for a 5.5-mile trip). Must be non-negative.
# MAGIC         time_minutes (float): The trip duration in minutes (e.g., 15.0 for a 15-minute trip). Must be non-negative.
# MAGIC     
# MAGIC     Returns:
# MAGIC         float: The estimated total fare in US dollars. For example, a 5-mile trip taking 15 minutes 
# MAGIC                would return 18.50 (3.00 + 12.50 + 7.50).
# MAGIC     """
# MAGIC     base_fare = 3.00
# MAGIC     per_mile_rate = 2.50
# MAGIC     per_minute_rate = 0.50
# MAGIC     
# MAGIC     total_fare = base_fare + (distance_miles * per_mile_rate) + (time_minutes * per_minute_rate)
# MAGIC     return total_fare
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 関数のテスト
# MAGIC ベストプラクティスに従って、Unity Catalogに登録する前に、ここでノートブック内で新しい関数をテストしましょう。
# MAGIC **TODO**: 次のセルを実行して、**7マイル** の距離と **20分** の時間をテストし、先ほど計算した **30.5** の合計を確認してください。

# COMMAND ----------

est_taxi_fare(
        distance_miles= 7.0,
        time_minutes= 20.0
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. 改良された記述でPython関数を再登録
# MAGIC 今度は、悪いPythonの例を再登録する必要があります。これは `create_python_function()` APIで実現できます。
# MAGIC > Python関数をSQLコードでラップして `CREATE OR REPLACE FUNCTION` を使用することもできます。
# MAGIC
# MAGIC **TODO:** 改良された記述でPython関数を再登録してください。元のバージョンの関数を上書きするために `replace=True` を設定してください。

# COMMAND ----------

## 改良されたdocstringで関数を再登録
function_info_improved = client.<FILL_IN>(
    func=<FILL_IN>,
    catalog=<FILL_IN>,
    schema=<FILL_IN>,
    replace=<FILL_IN>
)

print("Python function re-registered with improved description!")
print(f"Function name: {function_info_improved.full_name}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD4: 改良された記述でPython関数を再登録 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC function_info_improved = client.create_python_function(
# MAGIC     func=est_taxi_fare,
# MAGIC     catalog=catalog_name,
# MAGIC     schema=schema_name,
# MAGIC     replace=True
# MAGIC )
# MAGIC
# MAGIC print("Python function re-registered with improved description!")
# MAGIC print(f"Function name: {function_info_improved.full_name}")
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### D5. 改良された関数がまだ動作することを確認
# MAGIC 次に、新しいバージョンの関数をテストしましょう。
# MAGIC
# MAGIC **TODO:** 再登録された関数をテストして、まだ正しく動作することを確認してください。上記の関数定義から直接関数をテストした場合と同じ結果が得られるはずです。

# COMMAND ----------

## 改良された関数をテスト
result_improved = client.<FILL_IN>(
    function_name=f"{<FILL_IN>}.{<FILL_IN>}.est_taxi_fare",
    parameters={
        "<FILL_IN>": <FILL_IN>,
        "<FILL_IN>": <FILL_IN>
    }
)

print(f"Estimated Fare (Improved Function): ${result_improved.value}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD5: 改良された関数がまだ動作することを確認 回答
# MAGIC <details>
# MAGIC   <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC result_improved = client.execute_function(
# MAGIC     function_name=f"{catalog_name}.{schema_name}.est_taxi_fare",
# MAGIC     parameters={
# MAGIC         "distance_miles": 7.0,
# MAGIC         "time_minutes": 20.0
# MAGIC     }
# MAGIC )
# MAGIC
# MAGIC print(f"Estimated Fare (Improved Function): ${result_improved.value}")
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // Preferred modern API
# MAGIC   if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC     navigator.clipboard.writeText(text)
# MAGIC       .then(() => alert("Copied to clipboard"))
# MAGIC       .catch(err => {
# MAGIC         console.error("Clipboard write failed:", err);
# MAGIC         fallbackCopy(text);
# MAGIC       });
# MAGIC   } else {
# MAGIC     fallbackCopy(text);
# MAGIC   }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC   const textarea = document.createElement("textarea");
# MAGIC   textarea.value = text;
# MAGIC   textarea.style.position = "fixed";
# MAGIC   textarea.style.left = "-9999px";
# MAGIC   document.body.appendChild(textarea);
# MAGIC   textarea.select();
# MAGIC   try {
# MAGIC     document.execCommand("copy");
# MAGIC     alert("Copied to clipboard");
# MAGIC   } catch (err) {
# MAGIC     console.error("Fallback copy failed:", err);
# MAGIC     alert("Could not copy to clipboard. Please copy manually.");
# MAGIC   } finally {
# MAGIC     document.body.removeChild(textarea);
# MAGIC   }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. AI Playgroundでのツールのテスト

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ### E1. ツールのアタッチ
# MAGIC
# MAGIC AI Playgroundで関数をエージェントツールとしてテストするには:
# MAGIC
# MAGIC 1. Databricks workspaceから **Playground** に移動します
# MAGIC 1. **Playground** の上部のモデル選択ドロップダウンメニューから **Tools enabled** ラベル付きのモデル（例：`GPT OSS 120B`）を選択します
# MAGIC 1. **Use endpoint** をクリックします
# MAGIC
# MAGIC
# MAGIC 次に、作成した両方の関数をAIエージェントのツールとしてアタッチしましょう:
# MAGIC
# MAGIC 1. **Tools > + Add tool** をクリックします
# MAGIC 2. **UC Function** の下で、ツールタイプとして **Hosted Function** をクリックします
# MAGIC 3. カタログとスキーマから `avg_distance_by_zip` を選択します
# MAGIC 4. 右下の **Save** をクリックします
# MAGIC 5. ステップ1-4を繰り返して `est_taxi_fare` 関数を追加します
# MAGIC 6. 両方のツールが装備されていることを確認します。**Tools** ドロップダウンメニューに **Tools (2)** が表示されるはずです

# COMMAND ----------

# MAGIC %md
# MAGIC ### E3. ツールのテスト
# MAGIC
# MAGIC #### エージェントがアクセスできるものの確認
# MAGIC ユースケースの実際のクエリを送信する前に、エージェントがアクセスできるものを確認できます。以下のような質問をしてください:
# MAGIC > どのようなツールを使用できますか？
# MAGIC または 
# MAGIC > どのようなツールにアクセスできますか？
# MAGIC
# MAGIC 利用可能なすべてのツールをリストした応答が表示されます（アタッチした2つがリストされるはずです）。
# MAGIC
# MAGIC #### 質問の送信開始
# MAGIC
# MAGIC これで、サンプル質問を送信して関数のテストを開始する準備ができました。開始に役立つサンプル質問をいくつか紹介します:
# MAGIC
# MAGIC > サンプル質問1: 来週旅行予定で、約20分で7マイルだと思います。いくらかかりますか？
# MAGIC - これは **C2** セクションで使用したのと同じ質問です。
# MAGIC
# MAGIC > サンプル質問2: 郵便番号10001からの乗車の平均トリップ距離は何ですか？
# MAGIC - これはSQL関数をテストします
# MAGIC
# MAGIC > 郵便番号10001の平均トリップ距離をマイル単位で取得できますか？その郵便番号で20分間の移動にどのくらいかかるか知りたいです。
# MAGIC - これは（うまくいけば）両方の関数を呼び出します。出力は使用されるLLMのタイプによって異なることに留意してください。以下は **GPT OSS 20B** を使用した出力例のスクリーンショットです。一方（または両方）の関数が呼び出されない場合は、プレイグラウンドで **Add system prompt** をクリックしてシステムプロンプトを明示的に追加し、_「答えを導き出す前にすべてのツールオプションを使い尽くしてください」_のようなメッセージを送信して、LLMに利用可能な関数を呼び出すよう明示的に指示できます。
# MAGIC
# MAGIC <!-- 出力画像 -->
# MAGIC
# MAGIC ![optional alt text](../Includes/images/llm_output.png)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC 習得したスキルにより、Unity CatalogのガバナンスframeworkとSQLとPythonの両方の力を組み合わせた本番環境対応のエージェントツールを作成できるようになりました。関数記述のベストプラクティスに従うことで、AIエージェントがツールを効果的に理解し、活用して正確で信頼性の高い洞察を提供できるようになります。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>