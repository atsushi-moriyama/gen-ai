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
# MAGIC # ラボ - LangChainを使ったシングルエージェントの構築
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このハンズオンラボでは、Unity Catalog（UC）関数をLangChain framework内のツールとして活用するAIエージェントを構築します。NYC タクシー乗車データを分析するためのUC関数を作成し、LangChainツールキットと統合し、Mosaic AI Model Servingでホストされている基盤モデルを使用して推論と行動を行うことができるエージェントを構築します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このラボの終了時には、以下のことができるようになります：
# MAGIC - エージェント統合前に事前構築されたUnity Catalog関数を独立してテストする
# MAGIC - `UCFunctionToolkit` を使用してUnity Catalog関数をLangChainと設定・統合する
# MAGIC - ツール呼び出し機能を持つLangChainエージェントを構築・実行する
# MAGIC - デバッグと最適化のためにMLflowを使用してエージェント実行トレースを分析する
# MAGIC
# MAGIC **注意**: このラボを開始する前に、まず前のデモンストレーションを完了することを強く推奨します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境設定と前提条件

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバーレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5 を使用してテストされました。** 正しいバージョンのサーバーレスを使用していることを確認するため、[ノートブックのサーバーレスバージョンの確認と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC
# MAGIC ワークスペース設定の一環として、いくつかのPythonライブラリがインストールされています。ノートブックスコープのライブラリのリストを確認するには、[このドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies#configure-environment-for-job-tasks)をお読みください。
# MAGIC
# MAGIC **注意:** `langchain-databricks` に精通している場合は、`databricks-langchain` がそれに代わることに注意してください。このラボではLangChainを使用していますが、同様のアプローチを他のライブラリにも適用できます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-2.2

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. NYC タクシーデータセットの確認
# MAGIC
# MAGIC このラボで使用するデータセットは、[UC対応workspacesでデフォルトで利用可能](https://docs.databricks.com/aws/en/discover/databricks-datasets)なサンプルデータセットである `samples.nyctaxi.trips` テーブルから取得されます。次のセルを実行して、データセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('samples.nyctaxi.trips')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. Databricks Function Clientの初期化
# MAGIC
# MAGIC `DatabricksFunctionClient` は、Unity Catalog関数を実行するためのプログラマティックインターフェースを提供します。コンピュート要件に合わせてサーバーレス実行モード用に設定します。
# MAGIC
# MAGIC **TODO**: サーバーレスコンピュート用にクライアントを初期化してください。

# COMMAND ----------

from unitycatalog.ai.core.databricks import DatabricksFunctionClient

## サーバーレスコンピュート用にクライアントを初期化
client = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクB: Databricks Function Clientの初期化 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC from unitycatalog.ai.core.databricks import DatabricksFunctionClient
# MAGIC
# MAGIC # サーバーレスコンピュート用にクライアントを初期化
# MAGIC client = DatabricksFunctionClient(execution_mode="serverless")
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. エージェント統合前の関数の確認
# MAGIC クラスルーム設定の一環として、2つのエージェントツールが作成されています：
# MAGIC 1. `avg_fare_by_zip`: 特定のピックアップZIPコードからの乗車の平均運賃金額を計算します。平均運賃を数値として返します。
# MAGIC 1. `cnt_lng_dist_trip`: 指定されたピックアップZIPコードから指定された距離より長い乗車の数をカウントします。カウントを整数として返します。
# MAGIC
# MAGIC ### UI確認手順
# MAGIC 1. **Navigate to the Catalog**
# MAGIC    - 左サイドバーで **catalog** をクリックします。
# MAGIC
# MAGIC 2. **Locate Your Workspace Catalog and Schema**
# MAGIC    - **dbacademy** カタログを開きます。
# MAGIC    - **labuser** で始まるスキーマを選択します（これは作業していたスキーマです）。
# MAGIC
# MAGIC 3. **View Functions**
# MAGIC    - スキーマサイドバーの **functions** をクリックします。
# MAGIC    - 関数 `avg_fare_by_zip` と `cnt_lng_dist_trip` を見つけます
# MAGIC
# MAGIC 4. **Inspect Function Details**
# MAGIC    - 関数名をクリックして詳細を開きます。
# MAGIC    - 以下を確認します：
# MAGIC    - **Comments on input parameters**
# MAGIC    - **The referenced table or data source**
# MAGIC    - 関数に関連付けられた **追加のメタデータ**

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. エージェント統合前の関数テスト
# MAGIC
# MAGIC これらの関数をエージェントに統合する前に、SQLクエリで直接テストして正しく動作することを確認しましょう。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC -- -- ZIPコード10001で平均運賃関数をテスト
# MAGIC SELECT <FILL_IN> AS manhattan_avg_fare;

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクC1.1: 平均運賃関数のテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC -- ZIPコード10001で平均運賃関数をテスト
# MAGIC SELECT avg_fare_by_zip(10001) AS manhattan_avg_fare;
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC -- -- ZIPコード10001と最小距離10マイルで長距離乗車関数をテスト
# MAGIC SELECT <FILL_IN> AS long_trips_count;

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクC1.2: 長距離乗車関数のテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC -- ZIPコード10001と最小距離10マイルで長距離乗車関数をテスト
# MAGIC SELECT cnt_lng_dist_trip(10001, 10.0) AS long_trips_count;
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. Unity Catalog関数とLangChainの統合
# MAGIC
# MAGIC 関数が基本的なSQLで動作することが確認できたので、`databricks_langchain` を活用してUC関数をLangChainに直接統合できるツールとしてラップします。最初のステップはツールリストを定義することです。次に行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. ツールリストの定義
# MAGIC
# MAGIC **TODO:** 使用したい関数のリストを作成し、カタログとスキーマ名でフォーマットしてください（これはエージェントframeworkの要件です）。

# COMMAND ----------

tool_list_raw = [
    <FILL_IN>,
    <FILL_IN>
]

function_names = []
for tool in tool_list_raw:
    tool = <FILL_IN> + '.' + <FILL_IN> + '.' + tool
    function_names.append(tool)

print(f"Tool list: {function_names}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD1: ツールリストの定義 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC tool_list_raw = [
# MAGIC 'avg_fare_by_zip',
# MAGIC 'cnt_lng_dist_trip'
# MAGIC ]
# MAGIC
# MAGIC function_names = []
# MAGIC for tool in tool_list_raw:
# MAGIC   tool = catalog_name + '.' + schema_name + '.' + tool
# MAGIC   function_names.append(tool)
# MAGIC
# MAGIC print(f"Tool list: {function_names}")
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. UCFunctionToolkitの作成
# MAGIC
# MAGIC **TODO:** Unity Catalog関数をラップし、`UCFunctionToolkit` を使用してLangChainツールとして利用可能にするツールキットを作成してください。

# COMMAND ----------

from databricks_langchain import UCFunctionToolkit

## Unity Catalog関数でツールキットを作成
toolkit = <FILL_IN>
tools = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD2: UCFunctionToolkitの作成 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC from databricks_langchain import UCFunctionToolkit
# MAGIC
# MAGIC # Unity Catalog関数でツールキットを作成
# MAGIC toolkit = UCFunctionToolkit(function_names=function_names)
# MAGIC tools = toolkit.tools
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. ツールキットのテスト
# MAGIC 最後にツールキットをテストする準備ができました。以下のクエリの出力は、クエリの構文がSQLから `client.execute_function()` の使用に変更されただけなので、上記と全く同じになることに注意してください。
# MAGIC > `client` は上記の作業で `client = DatabricksFunctionClient(execution_mode="serverless")` として定義されていることを思い出してください。
# MAGIC
# MAGIC **TODO:** `DatabricksFunctionClient` を使用してサンプルペイロードを実行してツールキットをテストしてください。

# COMMAND ----------

## 最初のツール（ピックアップZIPによる平均運賃）をテスト
payload1 = <FILL_IN>
payload1_test_result = client.execute_function(
    function_name=<FILL_IN>,
    parameters=payload1
)
print(payload1_test_result.value)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD3.1: 最初のツールのテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # 最初のツール（ピックアップZIPによる平均運賃）をテスト
# MAGIC payload1 = {'pickup_zip_code': 10001}
# MAGIC payload1_test_result = client.execute_function(
# MAGIC function_name=tools[0].uc_function_name,
# MAGIC parameters=payload1
# MAGIC )
# MAGIC print(payload1_test_result.value)
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

## 2番目のツール（長距離乗車のカウント）をテスト
payload2 = <FILL_IN>
payload2_test_result = client.execute_function(
    function_name=<FILL_IN>,
    parameters=payload2
)
print(payload2_test_result.value)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクD3.2: 2番目のツールのテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # 2番目のツール（長距離乗車のカウント）をテスト
# MAGIC payload2 = {
# MAGIC 'pickup_zip_code': 10001,
# MAGIC 'min_distance': 10.0
# MAGIC }
# MAGIC payload2_test_result = client.execute_function(
# MAGIC   function_name=tools[1].uc_function_name,
# MAGIC   parameters=payload2
# MAGIC )
# MAGIC print(payload2_test_result.value)
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. エージェントの設定と実行
# MAGIC
# MAGIC ツールキットが設定・テストされたので、エージェントコードから分離されたエージェント設定ファイルを作成する準備ができました。クラスルーム設定の一環として、このラボが配置されているのと同じディレクトリに `lab_agent.json` というJSONファイルが読み込まれています。
# MAGIC 1. 左メニューに移動し、次のタスクを完了する前に `lab_agent.json` ファイルを確認してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. エージェント設定の読み込み
# MAGIC
# MAGIC **TODO:** JSONファイルからエージェント設定を読み込み、必要なパラメーターを抽出してください。

# COMMAND ----------

import json

## JSONファイルを読み込み
with open("./lab_agent.json", "r") as f:
    config = <FILL_IN>

llm_endpoint = <FILL_IN>
llm_temperature = <FILL_IN>
system_prompt = <FILL_IN>

print("Endpoint:", llm_endpoint)
print("Temperature:", llm_temperature)
print("System Prompt:", system_prompt)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクE1: エージェント設定の読み込み 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC import json
# MAGIC
# MAGIC # JSONファイルを読み込み
# MAGIC with open("./lab_agent.json", "r") as f:
# MAGIC   config = json.load(f)
# MAGIC
# MAGIC llm_endpoint = config['llm_endpoint']
# MAGIC llm_temperature = config['llm_temperature']
# MAGIC system_prompt = config["system_prompt"]
# MAGIC
# MAGIC print("Endpoint:", llm_endpoint)
# MAGIC print("Temperature:", llm_temperature)
# MAGIC print("System Prompt:", system_prompt)
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. 必要なライブラリのインポートとコンポーネントの初期化
# MAGIC
# MAGIC **TODO:** 必要なライブラリをインポートし、`ChatDatabricks` を使用して言語モデルを初期化してください。

# COMMAND ----------

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from databricks_langchain import ChatDatabricks
import mlflow

## ChatDatabricksを使用して言語モデルを初期化
llm_config = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクE2: 言語モデルの初期化 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC from langchain.agents import AgentExecutor, create_tool_calling_agent
# MAGIC from langchain.prompts import ChatPromptTemplate
# MAGIC from databricks_langchain import ChatDatabricks
# MAGIC import mlflow
# MAGIC
# MAGIC # 言語モデルを初期化
# MAGIC llm_config = ChatDatabricks(
# MAGIC   endpoint=llm_endpoint,
# MAGIC   temperature=llm_temperature
# MAGIC )
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### E3. プロンプトテンプレートの定義
# MAGIC
# MAGIC **TODO:** _システムプロンプト_ と会話構造を使用してプロンプトテンプレートを作成してください。

# COMMAND ----------

prompt_payload = ChatPromptTemplate.from_messages(
    [
        (
            <FILL_IN>,
            <FILL_IN>,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクE3: プロンプトテンプレートの定義 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC prompt_payload = ChatPromptTemplate.from_messages(
# MAGIC   [
# MAGIC     (
# MAGIC       "system",
# MAGIC       system_prompt,
# MAGIC     ),
# MAGIC     ("placeholder", "{chat_history}"),
# MAGIC     ("human", "{input}"),
# MAGIC     ("placeholder", "{agent_scratchpad}"),
# MAGIC   ]
# MAGIC )
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### E4. MLflowトレースの有効化とエージェント設定の作成
# MAGIC
# MAGIC **TODO:** MLflowオートロギングを有効にし、`langchain` ライブラリの `create_tool_calling_agent` を使用してエージェント設定を作成してください。

# COMMAND ----------

## MLflowトレースを有効化
<FILL_IN>

## エージェント設定を作成
agent_config = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクE4: MLflowの有効化とエージェントの作成 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # MLflowトレースを有効化
# MAGIC mlflow.langchain.autolog()
# MAGIC
# MAGIC # エージェント設定を作成
# MAGIC agent_config = create_tool_calling_agent(
# MAGIC   llm_config,
# MAGIC   tools,
# MAGIC   prompt_payload
# MAGIC )
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### E5. エージェントの実行
# MAGIC
# MAGIC **TODO:** エージェントエグゼキューターを作成し、`AgentExecutor()` を使用してNYCタクシーデータに関するクエリで実行し、レスポンスを取得してください。
# MAGIC
# MAGIC **ボーナス**: 両方のツールを呼び出すクエリを構築してください。

# COMMAND ----------

agent_executor = AgentExecutor(agent=<FILL_IN>, tools=<FILL_IN>, verbose=True)
response = agent_executor.invoke(
    {
        "input": <FILL_IN>
    }
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクE5: エージェントの実行 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC agent_executor = AgentExecutor(agent=agent_config, tools=tools, verbose=True)
# MAGIC response = agent_executor.invoke(
# MAGIC   {
# MAGIC     "input": "What's the average fare for trips from ZIP code 10001 and how many trips from that ZIP code are longer than 15 miles?"
# MAGIC   }
# MAGIC )
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. エージェントレスポンスとトレースの分析

# COMMAND ----------

# MAGIC %md
# MAGIC ### F1. エージェントのレスポンスの解析
# MAGIC
# MAGIC **TODO:** エージェントのレスポンスを抽出し、読みやすい形式で表示してください。

# COMMAND ----------

## レスポンスからテキストセグメントを抽出
output_segments = <FILL_IN>

print(output_segments)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクF1: エージェントレスポンスの解析 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # レスポンスからテキストセグメントを抽出
# MAGIC output_segments = response['output']
# MAGIC
# MAGIC print(output_segments)
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ### F2. 異なるクエリでの実験
# MAGIC
# MAGIC **TODO:** エージェントの機能をテストするために、異なるクエリでエージェントを実行してみてください。
# MAGIC
# MAGIC **BONUS**: 複数のZIPコードの提供など、異なる入力値間でエージェントが検索する能力を実証するクエリを作成してください。

# COMMAND ----------

## 異なるクエリを試す
custom_response = agent_executor.invoke(
    {
        "input": <FILL_IN>
    }
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスクF2: 異なるクエリでの実験 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # 異なるクエリを試す
# MAGIC custom_response = agent_executor.invoke(
# MAGIC   {
# MAGIC     "input": "Compare the average fare for ZIP codes 10001 and 10002, and tell me which one has more trips over 20 miles"
# MAGIC   }
# MAGIC )
# MAGIC <!-------------------解答コード終了------------------->
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC const el = document.getElementById("copy-block");
# MAGIC if (!el) return;
# MAGIC
# MAGIC const text = el.innerText;
# MAGIC
# MAGIC // Preferred modern API
# MAGIC if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC navigator.clipboard.writeText(text)
# MAGIC .then(() => alert("Copied to clipboard"))
# MAGIC .catch(err => {
# MAGIC console.error("Clipboard write failed:", err);
# MAGIC fallbackCopy(text);
# MAGIC });
# MAGIC } else {
# MAGIC fallbackCopy(text);
# MAGIC }
# MAGIC }
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC const textarea = document.createElement("textarea");
# MAGIC textarea.value = text;
# MAGIC textarea.style.position = "fixed";
# MAGIC textarea.style.left = "-9999px";
# MAGIC document.body.appendChild(textarea);
# MAGIC textarea.select();
# MAGIC try {
# MAGIC document.execCommand("copy");
# MAGIC alert("Copied to clipboard");
# MAGIC } catch (err) {
# MAGIC console.error("Fallback copy failed:", err);
# MAGIC alert("Could not copy to clipboard. Please copy manually.");
# MAGIC } finally {
# MAGIC document.body.removeChild(textarea);
# MAGIC }
# MAGIC }
# MAGIC </script>
# MAGIC </details>

# COMMAND ----------

# MAGIC %md
# MAGIC ## G. レビューと分析
# MAGIC
# MAGIC ### MLflowトレース分析
# MAGIC
# MAGIC 上記の出力に表示されるMLflowトレースUIを確認してください。**summary** タブをクリックして以下を確認してください：
# MAGIC
# MAGIC - **呼び出されたツール**: クエリに対して両方のツールが呼び出されているはずです
# MAGIC - **渡されたパラメーター**: 各UC関数への入力を確認してください
# MAGIC - **各ツールから返された結果**: 数値出力を確認してください
# MAGIC - **エージェントによって生成された最終レスポンス**: LLMがツールの結果をどのように統合したかを確認してください
# MAGIC
# MAGIC ### 主な観察点
# MAGIC
# MAGIC エージェントの実行に基づいて、以下を考慮してください：
# MAGIC
# MAGIC 1. **Tool Selection**: エージェントは各クエリに適切なツールを選択しましたか？
# MAGIC 2. **Parameter Passing**: 各関数に正しいパラメーターが渡されましたか？
# MAGIC 3. **Response Quality**: エージェントはツールの結果をどの程度うまく一貫した回答に統合しましたか？
# MAGIC 4. **Error Handling**: 無効なZIPコードやパラメーターを提供した場合はどうなりますか？

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC NYCタクシー乗車データを分析するためのUnity Catalog関数をツールとして活用するLangChainエージェントの構築に成功しました。このアプローチは、Unity Catalogが提供するガバナンス、セキュリティ、リネージ追跡を維持しながら、組織のデータ資産について推論し、行動できる本番環境対応のAIエージェントを構築する方法を実証しています。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>