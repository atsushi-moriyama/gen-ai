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

# MAGIC %md-sandbox
# MAGIC
# MAGIC # ラボ - エージェント評価の適用
# MAGIC
# MAGIC **概要**
# MAGIC
# MAGIC このラボでは、生成AIエージェント向けのMLflowの評価フレームワークを実際に体験できます。NYC Taxiデータセットを使用して、組み込みジャッジ（正確性、安全性）とカスタムガイドラインジャッジの両方を使用した評価ワークフローを構築します。
# MAGIC
# MAGIC このラボでは、評価データセットの作成、複数タイプのジャッジの設定、評価結果の分析を行い、エージェントのパフォーマンスを理解します。このラボは、実際のAIアプリケーションに適用できる自動評価ワークフローの実践的な実装に重点を置いています。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このラボの終了時には、以下ができるようになります：
# MAGIC
# MAGIC - 正確性と安全性評価のための **MLflowの組み込みジャッジを設定・実行** する
# MAGIC - 自然言語基準を使用したカスタムビジネスルール評価のための **ガイドラインジャッジを実装** する
# MAGIC - 異なるジャッジタイプに適した構造を持つ **評価データセットを作成** する
# MAGIC - MLflowのトレース機能と結果dataframesを使用して **評価結果を分析** する
# MAGIC - 評価モデルの分離と設定ファイル管理のための **ベストプラクティスを適用** する
# MAGIC
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">前提条件</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">このデモは<strong>01 - Agent Setup</strong>で作成されたエージェントを使用します。続行する前に、そのノートブックを完了していることを確認してください。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">注意</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">エージェントのトレースの一部として生成されたデータ型に関する<strong>ValueError</strong>または<strong>MLflowException</strong>エラーが発生した場合は、ノートブック内のセルを再実行する必要がある場合があります。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必須 - サーバーレスコンピュートを選択
# MAGIC
# MAGIC このノートブックでセルを実行する前に、ノートブックを **サーバーレスコンピュート** にアタッチしてください。
# MAGIC
# MAGIC **注意：** このデモは **サーバーレス（バージョン5）** でテストされています。  
# MAGIC サーバーレスバージョンを確認または変更するには、サーバーレス依存関係に関するDatabricksドキュメントを参照してください。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### コンピュート要件
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5を使用してテストされています。** 正しいバージョンのサーバーレスを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)を参照してください。
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">必須 - サーバーレスコンピュートを選択</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">続行する前に、このノートブックをサーバーレスコンピュートリソースにアタッチする必要があります。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### クラスルームセットアップ
# MAGIC
# MAGIC このコースの作業環境を設定するために、以下のセルを実行してください。
# MAGIC
# MAGIC このセットアップでは以下を行います：
# MAGIC - `DA` オブジェクト（Databricks Academyヘルパー）の初期化
# MAGIC - **デフォルトカタログ** と **スキーマ** の設定
# MAGIC - このデモに必要なサポート設定のプロビジョニング
# MAGIC
# MAGIC **注意：** `DA` オブジェクトはDatabricks Academyコースでのみ利用可能です

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-4

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の規約：**
# MAGIC
# MAGIC このラボ全体を通して、`DA` オブジェクトを参照します。このオブジェクトはDatabricks Academyによって提供され、ユーザー名、カタログ名、スキーマ名、作業ディレクトリ、データセットの場所などの変数が含まれています。これらの詳細を表示するには、以下のコードブロックを実行してください：

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1. NYC Taxiデータセットとエージェント機能の理解

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. エージェント機能のテスト
# MAGIC
# MAGIC 異なるタイプのクエリでエージェントを呼び出して、利用可能な機能をどのように使用するかを理解しましょう。

# COMMAND ----------

def agent_payload(question: str):
    return [{"input": [{"role": "user", "content": question}]}]

# COMMAND ----------

## 旅行情報に関するクエリでエージェントをテストする
## get_trip_info機能をトリガーするクエリを使用する
test_query_1 = <FILL_IN>
result_1 = agent.predict(agent_payload(test_query_1))
print(f"Query: {test_query_1}")
print(f"Response: {result_1}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC test_query_1 = "What's the average trip distance for trips from zip code 10001 to 10002?"
# MAGIC result_1 = agent.predict(agent_payload(test_query_1))
# MAGIC print(f"Query: {test_query_1}")
# MAGIC print(f"Response: {result_1}")
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC   const el = document.getElementById("answer-1");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
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

# COMMAND ----------

## 料金計算クエリでエージェントをテストする
## calculate_fare_estimate機能をトリガーするクエリを使用する
test_query_2 = <FILL_IN>
result_2 = agent.predict(agent_payload(test_query_2))
print(f"Query: {test_query_2}")
print(f"Response: {result_2}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC <code>
# MAGIC test_query_2 = "What would be the estimated fare for a 5.2 mile trip with a base fare of $3.50?"
# MAGIC result_2 = agent.predict(agent_payload(test_query_2))
# MAGIC print(f"Query: {test_query_2}")
# MAGIC print(f"Response: {result_2}")
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート2. 組み込みジャッジの実装

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1. 組み込みジャッジ用の評価データセット作成
# MAGIC
# MAGIC 正確性と安全性ジャッジをテストするための2つの入力、期待される事実、期待される応答を含む評価データセットを作成します。評価データセットの一部はあなたのために記入されています。
# MAGIC
# MAGIC **ヒント：** 行き詰まった場合は、`./artifacts/evaluation_datasets/nyc_taxi_eval.json` でサンプル評価データセットを確認できます。

# COMMAND ----------

## 組み込みジャッジ用の評価データセットを作成する
## 各クエリにexpected_factsを含む入力と期待値を含める
eval_dataset_builtin = [
  {
    "inputs": {
      "input": [
        {
          "role": <FILL_IN>,
          "content": <FILL_IN>
        }
      ]
    },
    "expectations": {
      "expected_facts": [
        <FILL_IN>
      ]
    }
  },
  {
    "inputs": {
      "input": [
        {
          "role": <FILL_IN>,
          "content": <FILL_IN>
        }
      ]
    },
    "expectations": {
      "expected_facts": [
        <FILL_IN>
      ]
    }
  }
]

print("Created evaluation dataset for built-in judges:")
from pprint import pprint
pprint(eval_dataset_builtin)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC eval_dataset_builtin = [
# MAGIC   {
# MAGIC     "inputs": {
# MAGIC       "input": [
# MAGIC         {
# MAGIC           "role": "user",
# MAGIC           "content": "What is the average fare for trips from zip code 10001 to 10002?"
# MAGIC         }
# MAGIC       ]
# MAGIC     },
# MAGIC     "expectations": {
# MAGIC       "expected_facts": [
# MAGIC         "Tool used is trip_info",
# MAGIC         "Pickup zip code is 10001",
# MAGIC         "Dropoff zip code is 10002",
# MAGIC         "Response includes average fare information"
# MAGIC       ]
# MAGIC     }
# MAGIC   },
# MAGIC   {
# MAGIC     "inputs": {
# MAGIC       "input": [
# MAGIC         {
# MAGIC           "role": "user",
# MAGIC           "content": "How many trips were taken from zip code 10003 to 10004?"
# MAGIC         }
# MAGIC       ]
# MAGIC     },
# MAGIC     "expectations": {
# MAGIC       "expected_facts": [
# MAGIC         "Tool used is trip_info",
# MAGIC         "Pickup zip code is 10003",
# MAGIC         "Dropoff zip code is 10004",
# MAGIC         "Response includes trip count",
# MAGIC         "Response includes 'Are there any additional questions I can help with?'"
# MAGIC       ]
# MAGIC     }
# MAGIC   }
# MAGIC ]
# MAGIC
# MAGIC print("Created evaluation dataset for built-in judges:")
# MAGIC from pprint import pprint
# MAGIC pprint(eval_dataset_builtin)
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2. 組み込みジャッジの設定
# MAGIC
# MAGIC 設定されたエンドポイントを使用して、正確性と安全性ジャッジを設定します。

# COMMAND ----------

## 組み込みジャッジをインポートして設定する
from mlflow.genai.scorers import <FILL_IN>, <FILL_IN>

## 正確性ジャッジインスタンスを作成
correctness_eval = <FILL_IN>(
    model=<FILL_IN>
)

## 安全性ジャッジインスタンスを作成
safety_eval = <FILL_IN>(
    model=<FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC from mlflow.genai.scorers import Correctness, Safety
# MAGIC
# MAGIC # Create correctness judge instance
# MAGIC correctness_eval = Correctness(
# MAGIC     model=correctness_eval_endpoint
# MAGIC )
# MAGIC
# MAGIC # Create safety judge instance
# MAGIC safety_eval = Safety(
# MAGIC     model=safety_endpoint
# MAGIC )
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.3. 組み込みジャッジ評価の実行
# MAGIC
# MAGIC 正確性と安全性ジャッジの両方を同時に使用して評価を実行します。結果を確認するには **MLflowで評価結果を表示** をクリックしてください。

# COMMAND ----------

## 両方の組み込みジャッジで評価を実行
builtin_results = mlflow.genai.evaluate(
    data=<FILL_IN>,
    predict_fn=<FILL_IN>,
    scorers=<FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC builtin_results = mlflow.genai.evaluate(
# MAGIC     data=eval_dataset_builtin,
# MAGIC     predict_fn=lambda input: agent.predict({"input": input}),
# MAGIC     scorers=[correctness_eval, safety_eval]
# MAGIC )
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.4. 組み込みジャッジ結果の分析
# MAGIC
# MAGIC 評価結果を確認し、"print" 文や `builtin_results()` を使用して採点の根拠を理解してください。

# COMMAND ----------

## 評価結果とメトリクスを表示
print(f"Run ID: {<FILL_IN>}")
print(f"Aggregated Metrics: {<FILL_IN>}")
print("\nDetailed Results:")
display(<FILL_IN>)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC print(f"Run ID: {builtin_results.run_id}")
# MAGIC print(f"Aggregated Metrics: {builtin_results.metrics}")
# MAGIC print("\nDetailed Results:")
# MAGIC display(builtin_results.result_df)
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.5. 更新と反復（オプション）
# MAGIC
# MAGIC エージェントは期待値をパスしましたか？そうでない場合は、`./artifacts/configs/nyc_taxi_agent_config.yaml` のシステムプロンプトを更新して、エージェントが評価期待値と一致するようにしてください。すべての評価が **パス** するまで、このプロセスの上で反復してください。
# MAGIC
# MAGIC 例えば、デフォルトのシステムプロンプトは
# MAGIC
# MAGIC ```
# MAGIC You are an expert in answering questions regarding NYC Taxi data.
# MAGIC ```
# MAGIC
# MAGIC これは、例えば _What is the average fare for trips from zip code 10001 to 10002?_ という質問を渡して、出力に以下を期待する場合には、あまり説明的ではありません
# MAGIC - Tool used is trip_info,
# MAGIC - Pickup zip code is 10001,
# MAGIC - Dropoff zip code is 10002,
# MAGIC - Response includes 'Are there any additional questions I can help with?'
# MAGIC
# MAGIC その場合、システムプロンプトを _You are an expert in answering questions regarding NYC Taxi data. You will always respond with "Are there any additional questions I can help with?"_ に更新するかもしれません（下のスクリーンショットを参照）。
# MAGIC
# MAGIC ![update_system_prompt.png](../Includes/images/applying agent eval/update_system_prompt.png "update_system_prompt.png")

# COMMAND ----------

# MAGIC %md
# MAGIC プロンプトを更新した後、以下のコードスニペットでエージェントを再デプロイできます。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC import mlflow
# MAGIC import yaml
# MAGIC from mlflow.models.resources import DatabricksServingEndpoint, DatabricksFunction
# MAGIC
# MAGIC # 既存のYAML設定ファイルを指す（model_configとして渡すのと同じもの）
# MAGIC CONFIG_YAML = "../artifacts/configs/nyc_taxi_agent_config.yaml"  # &lt;— これを設定
# MAGIC
# MAGIC # YAMLから設定を読み込む
# MAGIC with open(CONFIG_YAML, "r") as f:
# MAGIC     cfg = yaml.safe_load(f)
# MAGIC
# MAGIC # YAMLから値を取得（適切なフォールバック付き）
# MAGIC CATALOG = cfg["CATALOG_NAME"]
# MAGIC SCHEMA = cfg["SCHEMA_NAME"]
# MAGIC MODEL_BASE_NAME = cfg.get("MODEL_NAME", "nyc_taxi_eval_agent")  # YAMLのオプションキー；デフォルトは"nyc_agent"
# MAGIC UC_MODEL_NAME = f"{CATALOG}.{SCHEMA}.{MODEL_BASE_NAME}"
# MAGIC
# MAGIC LLM_ENDPOINT = cfg["LLM_ENDPOINT_NAME"]
# MAGIC
# MAGIC # ツールはTOOL1/TOOL2として、またはYAMLのTOOLS: [ ... ]リストとして提供可能
# MAGIC if "TOOLS" in cfg and isinstance(cfg["TOOLS"], (list, tuple)) and len(cfg["TOOLS"]) &gt; 0:
# MAGIC     tool_names = [f"{CATALOG}.{SCHEMA}.{t}" for t in cfg["TOOLS"]]
# MAGIC else:
# MAGIC     tool1 = cfg.get("TOOL1")
# MAGIC     tool2 = cfg.get("TOOL2")
# MAGIC     tool_names = [f"{CATALOG}.{SCHEMA}.{t}" for t in [tool1, tool2] if t]
# MAGIC
# MAGIC # YAML駆動の値からMLflowリソースを構築
# MAGIC resources = [DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT)] + [
# MAGIC     DatabricksFunction(function_name=t) for t in tool_names
# MAGIC ]
# MAGIC
# MAGIC # 以前に使用したのと同じpythonモデルファイル
# MAGIC AGENT_PY = "../artifacts/nyc_taxi_agent.py"
# MAGIC
# MAGIC # オプションのエイリアス（cfg.get("ALIAS", "champion")でYAMLから取得することも可能）
# MAGIC ALIAS = "challenger"
# MAGIC
# MAGIC mlflow.set_registry_uri("databricks-uc")  # UCに登録することを確認
# MAGIC
# MAGIC with mlflow.start_run(tags={
# MAGIC     "training_type": "agent_eval_training",
# MAGIC     "model": LLM_ENDPOINT,
# MAGIC     "agent_type": "TOOL-CALLING",
# MAGIC     "agent_id": "agent2",
# MAGIC }):
# MAGIC     logged = mlflow.pyfunc.log_model(
# MAGIC         artifact_path="agent",
# MAGIC         python_model=AGENT_PY,
# MAGIC         model_config=CONFIG_YAML,  # 編集したYAML（SYSTEM_PROMPTを含む）
# MAGIC         artifacts={
# MAGIC             "agent_config": CONFIG_YAML,
# MAGIC             # "agent_eval_config": "/Workspace/Users/you/path/to/eval_config.yaml",  # オプション
# MAGIC         },
# MAGIC         input_example={"input": [{"role": "user", "content": "hello"}]},
# MAGIC         pip_requirements=[
# MAGIC             "databricks-openai", "backoff", "pyyaml",
# MAGIC             # 以前にdatabricks-connectをピン留めした場合は、ここでピンを保持：
# MAGIC             # f"databricks-connect=={version('databricks-connect')}",
# MAGIC         ],
# MAGIC         resources=resources,
# MAGIC         registered_model_name=UC_MODEL_NAME,  # 新しいUCモデルバージョンを作成
# MAGIC     )
# MAGIC
# MAGIC new_version = logged.registered_model_version
# MAGIC print("New UC version:", new_version)
# MAGIC
# MAGIC # オプション：エイリアスを新しいバージョンに切り替え：
# MAGIC from mlflow.tracking import MlflowClient
# MAGIC MlflowClient().set_registered_model_alias(
# MAGIC     name=UC_MODEL_NAME, alias=ALIAS, version=new_version
# MAGIC )
# MAGIC
# MAGIC # エイリアスで読み込み
# MAGIC agent = mlflow.pyfunc.load_model(f"models:/{UC_MODEL_NAME}@{ALIAS}")
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // 推奨される最新API
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

# COMMAND ----------

# MAGIC %md
# MAGIC これで、セクション **2.3** と **2.4** に戻って再評価できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート3. ガイドラインジャッジの実装

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1. グローバルガイドラインデータセットの作成
# MAGIC
# MAGIC すべての応答に均一に適用されるグローバルガイドラインをテストするための評価データセットを作成します。
# MAGIC
# MAGIC **ヒント：** 行き詰まった場合は、`./artifacts/evaluation_datasets/nyc_taxi_guidelines_eval.json` でサンプル評価データセットを確認できます。

# COMMAND ----------

## グローバルガイドライン用の評価データセットを作成
eval_dataset_guidelines = [
    {
        "inputs": <FILL_IN>
    }
]

print("Created evaluation dataset for global guidelines:")
pprint(eval_dataset_guidelines)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC eval_dataset_guidelines = [
# MAGIC   {
# MAGIC     "inputs": {
# MAGIC       "input": [
# MAGIC         {
# MAGIC           "role": "user",
# MAGIC           "content": "What is the average fare for trips from zip code 10001 to 10002?"
# MAGIC         }
# MAGIC       ]
# MAGIC     },
# MAGIC     "expectations": {
# MAGIC       "expected_facts": [
# MAGIC         "The average fare for trips between zip codes 10001 and 10002 is $12.50."
# MAGIC       ],
# MAGIC       "guidelines": [
# MAGIC         "The response should be professional and courteous",
# MAGIC         "The response should include specific numerical values when providing calculations or statistics",
# MAGIC         "The response should clearly indicate when it's using NYC taxi data"
# MAGIC     ]
# MAGIC     }
# MAGIC   }
# MAGIC ]
# MAGIC
# MAGIC print("Created evaluation dataset for global guidelines:")
# MAGIC pprint(eval_dataset_guidelines)
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. グローバルガイドラインジャッジの実装
# MAGIC
# MAGIC 応答がプロフェッショナルで、特定のフォーマット要件を含むことを確保するグローバルガイドラインジャッジを作成します。

# COMMAND ----------

## ガイドラインジャッジをインポートして設定する
from mlflow.genai.scorers import <FILL_IN>

## プロフェッショナルな応答のためのグローバルガイドラインを作成
professional_guideline = <FILL_IN>(
    name=<FILL_IN>,
    guidelines=[
        <FILL_IN>,
        <FILL_IN>
    ],
    model_name=<FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC <code>
# MAGIC from mlflow.genai.scorers import Guidelines
# MAGIC
# MAGIC # Create a global guideline for professional responses
# MAGIC professional_guideline = Guidelines(
# MAGIC     name="professional_response",
# MAGIC     guidelines=[
# MAGIC         "The response should be professional and courteous",
# MAGIC         "The response should include specific numerical values when providing calculations or statistics",
# MAGIC         "The response should clearly indicate when it's using NYC taxi data"
# MAGIC     ],
# MAGIC     model_name=guidelines_endpoint
# MAGIC )
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3. グローバルガイドライン評価の実行
# MAGIC
# MAGIC グローバルガイドラインジャッジを使用して評価を実行します。結果を確認するには **MLflowで評価結果を表示** をクリックしてください。

# COMMAND ----------

## グローバルガイドラインで評価を実行
guidelines_results = mlflow.genai.evaluate(
    data=<FILL_IN>,
    predict_fn=<FILL_IN>,
    scorers=<FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC
# MAGIC <code>
# MAGIC guidelines_results = mlflow.genai.evaluate(
# MAGIC     data=eval_dataset_guidelines,
# MAGIC     predict_fn=lambda input: agent.predict({"input": input}),
# MAGIC     scorers=[professional_guideline]
# MAGIC )
# MAGIC </code>
# MAGIC
# MAGIC </pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート4. 包括的評価分析

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1. 評価結果の比較
# MAGIC
# MAGIC 異なるジャッジタイプからの結果を分析・比較して、それらの強みと使用例を理解します。

# COMMAND ----------

## 比較のためにすべての評価実行の結果を表示
print("=== BUILT-IN JUDGES RESULTS ===")
print(f"Run ID: {<FILL_IN>}")
print(f"Metrics: {<FILL_IN>}")
display(<FILL_IN>)

print("\n=== GLOBAL GUIDELINES RESULTS ===")
print(f"Run ID: {<FILL_IN>}")
print(f"Metrics: {<FILL_IN>}")
display(<FILL_IN>)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC print("=== BUILT-IN JUDGES RESULTS ===")
# MAGIC print(f"Run ID: {builtin_results.run_id}")
# MAGIC print(f"Metrics: {builtin_results.metrics}")
# MAGIC display(builtin_results.result_df)
# MAGIC
# MAGIC print("\n=== GLOBAL GUIDELINES RESULTS ===")
# MAGIC print(f"Run ID: {guidelines_results.run_id}")
# MAGIC print(f"Metrics: {guidelines_results.metrics}")
# MAGIC display(guidelines_results.result_df)
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2. 包括的評価の作成
# MAGIC
# MAGIC 単一の評価実行で複数のジャッジタイプを組み合わせて、包括的な品質評価を取得します。

# COMMAND ----------

## 複数のジャッジタイプを使用した包括的評価を作成
## 組み込みデータセットを使用し、正確性とグローバルガイドラインを組み合わせる
comprehensive_results = mlflow.genai.evaluate(
    data=<FILL_IN>,
    predict_fn=<FILL_IN>,
    scorers=<FILL_IN>
)

print("=== COMPREHENSIVE EVALUATION RESULTS ===")
print(f"Run ID: {<FILL_IN>}")
print(f"Metrics: {<FILL_IN>}")
display(<FILL_IN>)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <details>
# MAGIC <summary style="cursor: pointer; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px; font-weight: bold;">回答を表示するにはクリック</summary>
# MAGIC
# MAGIC
# MAGIC <button onclick="copyAnswer1()">クリップボードにコピー</button>
# MAGIC
# MAGIC
# MAGIC <pre id="answer-1" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC
# MAGIC <pre id="answer-13" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC comprehensive_results = mlflow.genai.evaluate(
# MAGIC     data=eval_dataset_builtin,
# MAGIC     predict_fn=lambda input: agent.predict({"input": input}),
# MAGIC     scorers=[correctness_eval, professional_guideline]
# MAGIC )
# MAGIC
# MAGIC print("=== COMPREHENSIVE EVALUATION RESULTS ===")
# MAGIC print(f"Run ID: {comprehensive_results.run_id}")
# MAGIC print(f"Metrics: {comprehensive_results.metrics}")
# MAGIC display(comprehensive_results.result_df)
# MAGIC </code></pre>
# MAGIC
# MAGIC </details>
# MAGIC
# MAGIC <script>
# MAGIC function copyAnswer1() {
# MAGIC  const el = document.getElementById("answer-1");
# MAGIC  if (!el) return;
# MAGIC
# MAGIC
# MAGIC  const text = el.innerText;
# MAGIC
# MAGIC
# MAGIC  if (navigator.clipboard && navigator.clipboard.writeText) {
# MAGIC    navigator.clipboard.writeText(text)
# MAGIC      .then(() => alert("Copied to clipboard"))
# MAGIC      .catch(err => {
# MAGIC        console.error("Clipboard write failed:", err);
# MAGIC        fallbackCopy(text);
# MAGIC      });
# MAGIC  } else {
# MAGIC    fallbackCopy(text);
# MAGIC  }
# MAGIC }
# MAGIC
# MAGIC
# MAGIC function fallbackCopy(text) {
# MAGIC  const textarea = document.createElement("textarea");
# MAGIC  textarea.value = text;
# MAGIC  textarea.style.position = "fixed";
# MAGIC  textarea.style.left = "-9999px";
# MAGIC  document.body.appendChild(textarea);
# MAGIC  textarea.select();
# MAGIC  try {
# MAGIC    document.execCommand("copy");
# MAGIC    alert("Copied to clipboard");
# MAGIC  } catch (err) {
# MAGIC    console.error("Fallback copy failed:", err);
# MAGIC    alert("Could not copy to clipboard. Please copy manually.");
# MAGIC  } finally {
# MAGIC    document.body.removeChild(textarea);
# MAGIC  }
# MAGIC }
# MAGIC </script>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このラボでは、MLflowの組み込みジャッジとガイドラインジャッジを使用して、AIエージェント向けの包括的な評価フレームワークを正常に実装しました。以下を学習しました：
# MAGIC
# MAGIC - 異なる評価ニーズに対応する複数タイプのジャッジの設定と実行
# MAGIC - 様々なジャッジタイプに適切に構造化された評価データセットの作成
# MAGIC - MLflowのトレース機能と結果分析機能を使用した評価結果の分析
# MAGIC - 評価設定とモデル管理のためのベストプラクティスの適用
# MAGIC
# MAGIC これらの評価手法は、AIエージェントが品質基準を満たし、本番環境で確実に機能することを保証するための基盤となります。客観的な組み込み評価基準と柔軟なガイドライン評価基準を組み合わせることで、特定のビジネス要件に合わせて適応可能な包括的な品質評価が可能になります。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>