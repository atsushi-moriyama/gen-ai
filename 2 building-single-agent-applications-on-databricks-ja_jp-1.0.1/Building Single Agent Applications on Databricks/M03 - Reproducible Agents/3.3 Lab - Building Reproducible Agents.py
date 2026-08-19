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
# MAGIC # ラボ - MLflowトレーシングを使用した再現可能なAIエージェントの構築
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このハンズオンラボでは、前回のデモンストレーションで学んだ概念を適用して、Unity Catalogを使用して独自のAIエージェントを構築、トレース、登録します。カスタムトレーシング関数を実装し、エージェントの動作を検証し、本番利用のためにエージェントをUnity Catalogに登録します。このラボは、エンタープライズ環境で堅牢で観測可能なAIシステムを構築するために不可欠な実践的な実装スキルに焦点を当てています。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このラボの終了時には、以下のことができるようになります：
# MAGIC
# MAGIC - 適切な検証とエラーハンドリングを備えたカスタムトレーシング関数を実装する
# MAGIC - MLflowタグ戦略を適用してエージェントトレースを整理・分類する
# MAGIC - エージェントが適切なツールを使用することを保証するツール検証関数を作成する
# MAGIC - 完全な依存関係管理を備えたAIエージェントをUnity Catalogにログ・登録する
# MAGIC - MLflowとUnity Catalogレジストリの両方からエージェントをログ、登録、推論する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境のセットアップ

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバーレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバーレスを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC
# MAGIC MLflowトレーシングとエージェント機能に必要なPythonライブラリをインストールします。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-3.3

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. Airbnbデータセットの確認
# MAGIC クラスルームセットアップの一部として、AirbnbデータセットがUnity Catalog内のDeltaテーブルとして処理・保存されています。次のセルを実行して、データセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('sf_airbnb_listings')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. エージェントの読み込み
# MAGIC
# MAGIC このラボ全体で使用する事前設定されたエージェントをインポートします。
# MAGIC
# MAGIC **注意:** `mlflow.autolog` はエージェントのコードの一部として設定されているため、このノートブックで開始する必要はありません。

# COMMAND ----------

# MAGIC %md
# MAGIC まず、`demo_agent_config.json` ファイルを構築するカスタム関数を使用して開始します。これは、上記で定義した **catalog** と **schema** に固有である必要があります。実際には、これを動的または静的にするかは、使用ケースによって異なります。

# COMMAND ----------

# エージェントモジュールを再読み込み
%reload_ext autoreload
%autoreload 2

from lab_agent import AGENT as agent

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. タグを使用したカスタムトレーシング
# MAGIC
# MAGIC このセクションでは、MLflowタグを使用してトレースを整理・分類するカスタムトレーシング関数を実装します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. トレースタグの定義
# MAGIC
# MAGIC トレースの分類と整理に役立つタグ辞書を作成します。これらのタグはカスタムトレーシング関数に適用されます。

# COMMAND ----------

## 以下のキーと値を持つタグ辞書を作成してください：
## - component: "input_validation"
## - stage: "preprocessing" 
## - span_scope: "tool_function"
## - env: "dev"
## - trace_version: "v1.0.0"
## - input_type: "question"

tags = {
    <FILL_IN>
}

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク B1.1: トレースタグの定義 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC tags = {
# MAGIC     "component": "input_validation",
# MAGIC     "stage": "preprocessing",
# MAGIC     "span_scope": "tool_function",
# MAGIC     "env": "dev",
# MAGIC     "trace_version": "v1.0.0",
# MAGIC     "input_type": "question"
# MAGIC }
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
# MAGIC ### B2. 必要なライブラリのインポート
# MAGIC
# MAGIC カスタムトレーシング実装に必要なMLflowライブラリをインポートします。具体的には、`mlflow.entities` から `SpanType` モジュールを取り込みます。

# COMMAND ----------

import mlflow 
from mlflow.entities import SpanType

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. ツール検証関数の作成
# MAGIC
# MAGIC エージェントがレスポンスでツールを使用したかどうかを検証する2つのヘルパーエージェントツール（Python関数）を作成します。これは、エージェントが期待される動作パターンに従うことを保証するのに役立ちます。このセクションは `lab_agent_update.py` で行われていることを模倣しますが、カスタムトレーシングの基本とタグを使用したカスタムトレースのテストに焦点を当てます。以下のコードをエージェントに統合するステップは完了しており、完全な統合については常に`lab_agent_update.py` を参照できます。
# MAGIC
# MAGIC このセクションのコードはほぼ完成しており、特定の使用ケースではなくMLflowの側面に焦点を当てることができます。ただし、必要に応じて独自のカスタムコードを追加してください。

# COMMAND ----------

# MAGIC %md
# MAGIC #### B3.1 ツール使用検証関数
# MAGIC
# MAGIC この関数は、モデルレスポンスがツールを使用したかどうかをチェックし、構造化された結果を返します。カスタムコードのほとんどは作成済みです。

# COMMAND ----------

## validate_tool_usage関数を完成させてください
## span_type=SpanType.TOOLとname="Check Tool Usage"を指定した@mlflow.traceデコレータを使用してください

<FILL_IN>
def validate_tool_usage(result):
    """Check whether the model response used a tool and return a structured result."""
    
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default) if hasattr(obj, key) else default

    ## resultから出力を抽出
    output_list = _get(result, "output", []) or []

    ## ツール使用を検索
    tool_calls = [
        item for item in output_list
        if _get(item, "type") in ("function_call", "function_call_output")
    ]

    if not tool_calls:
        return {
            "used_tool": False,
            "error": "No tools were used during the model response.",
        }

    ## デバッグ用にツール名とコールIDを収集
    tools_info = [
        {
            "name": _get(item, "name"),
            "call_id": _get(item, "call_id"),
            "type": _get(item, "type"),
        }
        for item in tool_calls
    ]

    return {
        "used_tool": True,
        "tools": tools_info,
        "tool_count": len(tools_info)
    }

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク B3.1: ツール使用検証関数 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC @mlflow.trace(
# MAGIC     span_type=SpanType.TOOL,
# MAGIC     name="Check Tool Usage"
# MAGIC )
# MAGIC def validate_tool_usage(result):
# MAGIC     """Check whether the model response used a tool and return a structured result."""
# MAGIC     
# MAGIC     def _get(obj, key, default=None):
# MAGIC         if isinstance(obj, dict):
# MAGIC             return obj.get(key, default)
# MAGIC         return getattr(obj, key, default) if hasattr(obj, key) else default
# MAGIC
# MAGIC     # Extract outputs from result
# MAGIC     output_list = _get(result, "output", []) or []
# MAGIC
# MAGIC     # Find tool usage
# MAGIC     tool_calls = [
# MAGIC         item for item in output_list
# MAGIC         if _get(item, "type") in ("function_call", "function_call_output")
# MAGIC     ]
# MAGIC
# MAGIC     if not tool_calls:
# MAGIC         return {
# MAGIC             "used_tool": False,
# MAGIC             "error": "No tools were used during the model response.",
# MAGIC         }
# MAGIC
# MAGIC     # Collect tool names and call IDs for debugging
# MAGIC     tools_info = [
# MAGIC         {
# MAGIC             "name": _get(item, "name"),
# MAGIC             "call_id": _get(item, "call_id"),
# MAGIC             "type": _get(item, "type"),
# MAGIC         }
# MAGIC         for item in tool_calls
# MAGIC     ]
# MAGIC
# MAGIC     return {
# MAGIC         "used_tool": True,
# MAGIC         "tools": tools_info,
# MAGIC         "tool_count": len(tools_info)
# MAGIC     }
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
# MAGIC #### B3.2 レスポンス評価関数
# MAGIC
# MAGIC この関数はモデルレスポンスを評価し、ツールが使用されなかった場合にエラーを発生させます。コードのほとんどは完成しています。

# COMMAND ----------

## evaluate_response関数を完成させてください
## name="Evaluate Response"を指定した@mlflow.traceデコレータを使用してください

<FILL_IN>
def evaluate_response(result):
    """Evaluate the model response and raise error if no tool was used."""
    
    validation = validate_tool_usage(result)
    
    if not validation["used_tool"]:
        ## ツールが使用されなかった場合、明示的にエラーを発生させる
        raise ValueError(validation["error"])
    
    return {
        "message": f"{validation['tool_count']} tool(s) used successfully.",
        "details": validation["tools"]
    }

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク B3.2: レスポンス評価関数 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC @mlflow.trace(name="Evaluate Response")
# MAGIC def evaluate_response(result):
# MAGIC     """Evaluate the model response and raise error if no tool was used."""
# MAGIC     
# MAGIC     validation = validate_tool_usage(result)
# MAGIC     
# MAGIC     if not validation["used_tool"]:
# MAGIC         # If no tool was used, explicitly raise an error
# MAGIC         raise ValueError(validation["error"])
# MAGIC     
# MAGIC     return {
# MAGIC         "message": f"{validation['tool_count']} tool(s) used successfully.",
# MAGIC         "details": validation["tools"]
# MAGIC     }
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
# MAGIC ### B4. LLM呼び出し関数の作成
# MAGIC
# MAGIC エージェントを呼び出し、やり取りをキャプチャするトレース関数を作成します。今回は関数を一から構築する必要があります。

# COMMAND ----------

## call_llmという関数を作成してください：
## - name="Call LLM"とspan_type=SpanType.CHAT_MODELを指定した@mlflow.traceデコレータを使用
## - questionパラメータを受け取る
## - agent.predict(question)を返す

<FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク B4.1: LLM呼び出し関数の作成 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC @mlflow.trace(
# MAGIC     name="Call LLM",
# MAGIC     span_type=SpanType.CHAT_MODEL
# MAGIC )
# MAGIC def call_llm(question: str):
# MAGIC     return agent.predict(question)
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
# MAGIC ### B5. メイン処理関数の作成
# MAGIC
# MAGIC タグ付けと検証を含む全体のプロセスを統制するメイン関数を作成します。3つの主要なステップで一から関数を作成する必要があります：
# MAGIC 1. 現在のトレースを新しいタグで更新する
# MAGIC 2. 先ほど定義した `call_llm()` を使用してLLMを呼び出す
# MAGIC 3. `evaluate_response()` を使用してツール評価を取得する

# COMMAND ----------

## process_questionという関数を作成してください：
## - name="Process Question"を指定した@mlflow.traceデコレータを使用
## - user_inputとinclude_metadataパラメータを受け取る
## - mlflow.update_current_trace(tags)を使用して現在のトレースをタグで更新
## - user_inputを使用してcall_llmを呼び出す
## - evaluate_responseを使用してレスポンスを評価
## - ValueError例外を処理し、適切なメッセージを出力

<FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク B5.1: メイン処理関数の作成 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC @mlflow.trace(name="Process Question")
# MAGIC def process_question(user_input: str, include_metadata: bool = True):
# MAGIC     """Main function that calls LLM and formats response"""
# MAGIC
# MAGIC     # Step 1: Update the current trace with new tags
# MAGIC     mlflow.update_current_trace(tags)
# MAGIC     
# MAGIC     # Step 2: Call the LLM
# MAGIC     llm_response = call_llm(user_input)
# MAGIC     
# MAGIC     # Step 3: Get tool evaluation
# MAGIC     try:
# MAGIC         summary = evaluate_response(llm_response)
# MAGIC         print(summary)
# MAGIC     except ValueError as e:
# MAGIC         print(f"Tool validation failed: {e}")
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
# MAGIC ## C. カスタムトレースのテスト
# MAGIC
# MAGIC 異なるタイプのプロンプトを使用してカスタムトレーシング実装をテストします。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. ヘルパー関数とテストプロンプトの定義
# MAGIC
# MAGIC 以下では、プロンプトをフォーマットし、テストケースを定義するヘルパー関数を作成します。また、上記で構築したロジックに基づいた適切なテストのために、成功/失敗プロンプトがどのようなものかを定義します。

# COMMAND ----------

def format_prompt(prompt: str) -> dict:
    return {
        "input": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

# COMMAND ----------

# テストプロンプトを定義
success_prompt = "What is the price average for Mission?"
fail_prompt = "Hi!"

success_prompt_formatted = format_prompt(success_prompt)
fail_prompt_formatted = format_prompt(fail_prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 成功したツール使用のテスト
# MAGIC
# MAGIC ツール使用をトリガーするはずのプロンプトでトレーシングをテストします。

# COMMAND ----------

## success_prompt_formattedとtagsを使用してprocess_questionを呼び出してください
## これにより成功したツール使用が結果として得られるはずです

result = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク C2.1: 成功したツール使用のテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC result = process_question(success_prompt_formatted, tags)
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
# MAGIC ### C3. 失敗したツール使用のテスト
# MAGIC
# MAGIC ツール使用をトリガーしないはずのプロンプトでトレーシングをテストします。

# COMMAND ----------

## fail_prompt_formattedとtagsを使用してprocess_questionを呼び出してください
## これによりツール検証の失敗が結果として得られるはずです

result = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク C3.1: 失敗したツール使用のテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC result = process_question(fail_prompt_formatted, tags)
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
# MAGIC ## D. エージェントのMLflowログとUC登録
# MAGIC
# MAGIC このセクションでは、エージェントをMLflowにログし、本番デプロイのためにUnity Catalogに登録します。このクラスルームセットアップの一部として、 `lab_agent_update` という `.py` ファイルがあります。このファイルは、上記で記入したカスタムトレーシングを実装していますが、`mlflow.types.responses` と併用できるように適合されています。続行する前に、左側のメニューでこのファイルに移動し、認識のためにコードをスキャンしてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. エージェント設定の読み取り
# MAGIC
# MAGIC 以下では、エージェントの設定とツールを定義する設定ファイルを出力します。

# COMMAND ----------

import json
# エージェントJSON設定ファイルを読み取り
with open('lab_agent_config.json', 'r') as f:
    agent_config = json.load(f)
print(agent_config)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. 必要なリソースのインポート
# MAGIC
# MAGIC Unity Catalog統合に必要なMLflowリソースをインポートします。モデルが以下にアクセスできるようにする適切なライブラリを取り込む必要があります：
# MAGIC - Unity Catalogに登録された関数
# MAGIC - Unity Catalogに登録されたテーブル
# MAGIC - DatabricksがホストするModel serving endpoints
# MAGIC
# MAGIC **注意:** 適切なライブラリのレビューについては、[このドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#implement-automatic-authentication-passthrough)をご覧ください。

# COMMAND ----------

## mlflow.models.resourcesから必要なクラスをインポートしてください

from importlib.metadata import version
from mlflow.models.resources import (
    <FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク D2.1: 必要なリソースのインポート 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC from importlib.metadata import version
# MAGIC from mlflow.models.resources import (
# MAGIC     DatabricksFunction,
# MAGIC     DatabricksTable,
# MAGIC     DatabricksServingEndpoint
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
# MAGIC ### D3. モデルメタデータの定義
# MAGIC
# MAGIC 入力例、モデル名、登録タグを設定します。以下は、モデルと一緒にログする必要があるメタデータの例です。必要に応じて更新してください：
# MAGIC - 入力例
# MAGIC - モデル名
# MAGIC - タグ

# COMMAND ----------

input_example = format_prompt(success_prompt)

model_name = "reproducible-agents-lab"

tags_to_register = {
    "framework": "openai",
    "stage": "dev",
    "version": "1"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. リソースの設定
# MAGIC
# MAGIC エージェントが使用するUnity Catalogリソースを定義します。このリストには、先ほど取り込んだのと同じライブラリが含まれている必要があります。
# MAGIC - `agent_config` には、endpoint名と共に先ほど作成されたツールリストが含まれていることを思い出してください
# MAGIC - また、このラボの開始時に `sf_airbnb_listings` というテーブルが作成されており、これがツールのロジックの基盤となっていることも思い出してください

# COMMAND ----------

## 以下を含むresourcesリストを作成してください：

resources = [
    DatabricksFunction(<FILL_IN>),
    DatabricksFunction(<FILL_IN>),
    DatabricksTable(<FILL_IN>),
    DatabricksServingEndpoint(<FILL_IN>)
]

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク D4.1: リソースの設定 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC resources = [
# MAGIC     DatabricksFunction(function_name=f"{agent_config.get('tool_list')[0]}"),
# MAGIC     DatabricksFunction(function_name=f"{agent_config.get('tool_list')[1]}"),
# MAGIC     DatabricksTable(table_name=f"{catalog_name}.{schema_name}.sf_airbnb_listings"),
# MAGIC     DatabricksServingEndpoint(endpoint_name=agent_config['llm_endpoint'])
# MAGIC ]
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
# MAGIC ### D5. 更新されたエージェントの読み込み
# MAGIC
# MAGIC カスタムトレーシング機能を含む更新されたエージェントを読み込みます。

# COMMAND ----------

# MAGIC %reload_ext autoreload
# MAGIC %autoreload 2
# MAGIC
# MAGIC from lab_agent_update import AGENT as updated_agent

# COMMAND ----------

# MAGIC %md
# MAGIC ### D6. 更新されたエージェントのテスト
# MAGIC
# MAGIC ログする前に、更新されたエージェントが正しく動作することを確認します。セクション **B. Custom Tracing with Tags** でのテスト中に、それぞれ成功と失敗した2つの変数 `success_prompt_formatted` と `fail_prompt_formatted` があったことを思い出してください。

# COMMAND ----------

updated_agent.predict(success_prompt_formatted)

# COMMAND ----------

updated_agent.predict(fail_prompt_formatted)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D7. エージェントをMLflowにログ
# MAGIC
# MAGIC 必要なすべての依存関係と設定を含むエージェントをMLflowにログします。

# COMMAND ----------

## MLflowログプロセスを完成させてください：
## - MLflowランを開始
## - mlflow.set_tags()を使用してタグを設定
## - 適切なパラメータでmlflow.pyfunc.log_model()を使用してモデルをログ
## - 後で使用するためにモデルURIを保存

with mlflow.<FILL_IN>:
    <FILL_IN>
    logged_agent_info = mlflow.<FILL_IN>(
        name=<FILL_IN>,
        python_model=<FILL_IN>,
        code_paths=<FILL_IN>,
        input_example=<FILL_IN>,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={version('databricks-connect').version}",
        ],
        resources=<FILL_IN>
    )
    model_uri = <FILL_IN>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク D7.1: エージェントをMLflowにログ 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC with mlflow.start_run():
# MAGIC     mlflow.set_tags(tags_to_register)
# MAGIC     logged_agent_info = mlflow.pyfunc.log_model(
# MAGIC         name=model_name,
# MAGIC         python_model="lab_agent_update.py",
# MAGIC         code_paths=["lab_agent_config.json"],
# MAGIC         input_example=input_example,
# MAGIC         pip_requirements=[
# MAGIC             "databricks-openai",
# MAGIC             "backoff",
# MAGIC             f"databricks-connect=={version('databricks-connect')}",
# MAGIC         ],
# MAGIC         resources=resources
# MAGIC     )
# MAGIC     model_uri = logged_agent_info.model_uri
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
# MAGIC ### D8. MLflowモデル推論のテスト
# MAGIC
# MAGIC ログされたモデルが正しく動作することを確認するためにテストします。

# COMMAND ----------

## モデル（pyfunc flavor）を読み込む
## モデルは先ほど定義した入力例でログされている
## ログされた依存関係を使用して、提供された入力データでモデルを検証

pyfunc_model = mlflow.<FILL_IN>

input_data = pyfunc_model.<FILL_IN>

result = mlflow.<FILL_IN>(
    model_uri=<FILL_IN>,
    input_data=<FILL_IN>,
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク D8.1: MLflowモデル推論のテスト 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC # モデル（pyfunc flavor）を読み込む
# MAGIC # モデルは先ほど定義した入力例でログされている
# MAGIC # ログされた依存関係を使用して、提供された入力データでモデルを検証
# MAGIC
# MAGIC pyfunc_model = mlflow.pyfunc.load_model(model_uri)
# MAGIC
# MAGIC input_data = pyfunc_model.input_example
# MAGIC
# MAGIC result = mlflow.models.predict(
# MAGIC     model_uri=model_uri,
# MAGIC     input_data=input_data,
# MAGIC     env_manager="uv",
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
# MAGIC ### D9. エージェントをUnity Catalogに登録
# MAGIC
# MAGIC ガバナンスと本番デプロイのためにエージェントをUnity Catalogに登録します。

# COMMAND ----------

## Unity Catalog登録を完成させてください：
## - レジストリURIを"databricks-uc"に設定
## - catalog、schema、model nameを使用してUCモデル名を作成
## - mlflow.register_model()を使用してモデルを登録

mlflow.<FILL_IN>
UC_MODEL_NAME = f"{catalog_name}.{schema_name}.{model_name}"

uc_registered_model_info = mlflow.<FILL_IN>(
    model_uri=<FILL_IN>, 
    name=<FILL_IN>
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ##### タスク D9.1: エージェントをUnity Catalogに登録 解答
# MAGIC <details>
# MAGIC <summary>EXPAND FOR SOLUTION CODE</summary>
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC <!-------------------解答コードを以下に追加------------------->
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC UC_MODEL_NAME = f"{catalog_name}.{schema_name}.{model_name}"
# MAGIC
# MAGIC uc_registered_model_info = mlflow.register_model(
# MAGIC     model_uri=model_uri, 
# MAGIC     name=UC_MODEL_NAME
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
# MAGIC ### D10. Unity Catalogモデル推論のテスト
# MAGIC
# MAGIC Unity Catalogに登録されたモデルが正しく動作することを確認し、モデル（`catalog_name.schema_name.reproducible-agents-lab` にある）に移動してモデルの最新バージョンをクリックすることで、UIにトレースが表示されることを確認します。そこで **Traces** を見つけてクリックし、次のセルを実行した後にトレースを表示してください。

# COMMAND ----------

import mlflow
from mlflow.types.responses import ResponsesAgentRequest

# モデル（pyfunc flavor）を読み込む
pyfunc_model = mlflow.pyfunc.load_model(model_uri)

# モデルは入力例でログされている
input_data = format_prompt("What is the price average for Haight Ashbury")

# ログされた依存関係を使用して、提供された入力データでモデルを検証
result = mlflow.models.predict(
    model_uri=model_uri,
    input_data=input_data,
    env_manager="uv",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC このラボを完了することで、MLflowトレーシングを使用した再現可能なAIエージェントの構築に関するこのラボを正常に完了しました。このハンズオンエクササイズを通じて、以下のことを達成しました：
# MAGIC
# MAGIC - **カスタムトレーシング関数を実装** - エージェントの動作を監視するための適切な検証とエラーハンドリングを備えた関数を実装
# MAGIC - **MLflowタグ戦略を適用** - より良い観測可能性とデバッグのためにトレースを整理・分類
# MAGIC - **ツール検証関数を作成** - エージェントが適切なツールを使用し、期待される動作パターンに従うことを保証
# MAGIC - **AIエージェントをログ・登録** - 本番デプロイのための完全な依存関係管理を備えたUnity Catalogへの登録
# MAGIC - **エージェントの登録とテストを成功** - MLflowとUnity Catalogレジストリの両方からの登録とテスト
# MAGIC
# MAGIC これらのスキルは、観測可能で再現可能、かつガバナンス可能な本番対応のAIシステムを構築するために不可欠です。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>