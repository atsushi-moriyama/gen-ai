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
# MAGIC # デモ - MLflowでのカスタムジャッジ
# MAGIC
# MAGIC **概要** 
# MAGIC
# MAGIC このデモンストレーションでは、生成AI アプリケーションの評価のためにMLflowでカスタムLLMジャッジを作成および実装する方法を探ります。カスタムジャッジは、特定のビジネス要件と評価基準に合わせてカスタマイズされた自然言語指示を使用して、複雑で微妙なスコアリングガイドラインを定義する柔軟性を提供します。
# MAGIC
# MAGIC `make_judge()` で構築されたカスタムジャッジは、評価ロジックの完全な制御を提供し、組み込みジャッジではカバーされない可能性がある品質次元を評価できます。これには、ドメイン固有の要件、複雑な多段階評価、およびエージェント実行パターンのトレースベース分析が含まれます。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このデモンストレーションの終了時に、以下ができるようになります：
# MAGIC
# MAGIC 1. **カスタムジャッジの作成** - 自然言語指示を使用して `mlflow.genai.judges.make_judge()` でカスタムジャッジを作成する
# MAGIC 2. **テンプレート変数の実装** - 入力、出力、期待値、実行トレースにアクセスするためのテンプレート変数を実装する
# MAGIC 3. **トレースベースジャッジの設計** - 完全なエージェント実行ワークフローを分析するトレースベースジャッジを設計する
# MAGIC 4. **フィードバック値タイプの設定** - カテゴリ、ブール、数値スコアリングシステムのフィードバック値タイプを設定する
# MAGIC 5. **ベストプラクティスの適用** - 効果的なジャッジ指示の作成とモデル選択のベストプラクティスを適用する
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">前提条件</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;"> このデモでは<strong>01 - Agent Setup</strong>で作成されたエージェントを使用します。続行する前に、そのノートブックを完了していることを確認してください。</p>
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
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモではサーバーレスコンピュートがバージョン5である必要があります。** 正しいバージョンを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)を参照してください。
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

# MAGIC %run ../Includes/Classroom-Setup-5

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1. カスタムジャッジの理解

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 1.1. カスタムジャッジとは？
# MAGIC
# MAGIC カスタムLLMジャッジは、`mlflow.genai.judges.make_judge()` を使用して作成される特殊な評価関数で、自然言語指示を使用してGenAIアプリケーション用の複雑で微妙なスコアリングガイドラインを定義できます。一般的な品質次元をカバーする組み込みジャッジとは異なり、カスタムジャッジは評価基準の完全な制御を提供します。これは、 `mlflow.genai.judges.scorers()` に依存していた以前のデモとは異なるインポートされたクラスであることに注意してください。
# MAGIC
# MAGIC **カスタムジャッジの主要特性：**
# MAGIC - **自然言語指示** - 評価基準を平易な英語で定義
# MAGIC - **テンプレート変数アクセス** - 評価で入力、出力、期待値、トレースを使用
# MAGIC - **柔軟なフィードバックタイプ** - カテゴリ、ブール、または数値スコアを返す
# MAGIC - **ドメイン固有評価** - 独自のビジネス要件と品質基準に対応
# MAGIC
# MAGIC MLflowの `make_judge` 関数は、独自の指示と基準に従ってGenAI出力を評価するためのカスタムLLMベースのジャッジ（スコアラー）を作成します。ジャッジの名前、自然言語指示（`{inputs}`、`{{outputs}}` などのテンプレート変数付き、これについては以下で説明します）、およびオプションでモデルと出力タイプを指定すると、関数は応答、会話、またはトレースを評価するために使用できる呼び出し可能なジャッジオブジェクトを返します。
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">
# MAGIC         <code>mlflow.genai.judges.make_judge()</code>について詳しく
# MAGIC       </strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;">
# MAGIC         <code>make_judges</code>クラスについて詳しくは
# MAGIC         <a href="https://mlflow.org/docs/latest/genai/eval-monitor/scorers/llm-judge/make-judge/" target="_blank">
# MAGIC           こちら
# MAGIC         </a>をご覧ください。
# MAGIC       </p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2. カスタムジャッジのテンプレート変数
# MAGIC
# MAGIC カスタムジャッジは **テンプレート変数** を使用して、エージェントの実行のさまざまな側面にアクセスします。これらの変数は包括的な評価に必要なコンテキストを提供します：
# MAGIC
# MAGIC - **`{{inputs}}`** - エージェントに提供される入力データ
# MAGIC - **`{{outputs}}`** - エージェントによって生成される出力データ  
# MAGIC - **`{{expectations}}`** - 正解または期待される結果
# MAGIC - **`{{trace}}`** - エージェントの完全な実行トレース
# MAGIC - **`{{conversation}},`** - エージェントの完全な実行
# MAGIC
# MAGIC **重要な制約：**
# MAGIC - 指示には少なくとも1つのテンプレート変数を含める必要があります
# MAGIC - これら4つの変数のみが許可されています（`{{question}}` のようなカスタム変数は検証エラーを引き起こします）
# MAGIC - これにより一貫した動作が保証され、テンプレートインジェクションの問題が防がれます
# MAGIC - `make_judge` を使用する場合（以下参照）、上記の4つのテンプレート変数のうち少なくとも1つを含む必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. カスタムジャッジの種類
# MAGIC
# MAGIC カスタムジャッジは、評価アプローチに基づいて2つの主要なタイプに分類できます：
# MAGIC
# MAGIC **標準カスタムジャッジ：**
# MAGIC - 入力、出力、期待値を評価
# MAGIC - コンテンツ品質と正確性に焦点
# MAGIC - 応答検証とコンテンツ評価に適している
# MAGIC
# MAGIC **トレースベースジャッジ：**
# MAGIC - Model Context Protocol（MCP）ツールを使用して完全な実行トレースを分析
# MAGIC - ツール使用パターンと実行ワークフローを検証
# MAGIC - パフォーマンスのボトルネックを特定し、失敗を調査
# MAGIC - 多段階エージェントプロセスを検証
# MAGIC
# MAGIC トレースベースジャッジの場合、トレース分析機能を有効にするために `make_judge()` で `model` パラメータを指定する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.4. 評価データセットの読み込み
# MAGIC
# MAGIC 次のセルを実行して、Unity Catalogの `agent_vol` から評価データセットを読み取るヘルパー関数を作成します。これらのデータセットを使用して、さまざまなタイプのカスタムジャッジをデモンストレーションします。

# COMMAND ----------

# MAGIC %md
# MAGIC 次のセルを実行して、カスタムジャッジで使用する評価データセットを表示します。

# COMMAND ----------

import json 
from pathlib import Path

path = Path(f"/Volumes/{catalog_name}/{schema_name}/agent_vol/custom_eval.json")
    
with path.open("r", encoding="utf-8") as f:
    custom_eval = json.load(f)

print("✅ Loaded dataset custom_eval as `custom_eval`")
pprint(custom_eval)

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート2. 標準カスタムジャッジの作成

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1. 基本的なカスタムジャッジの実装
# MAGIC
# MAGIC 応答の完全性を評価する最初のカスタムジャッジを作成しましょう。このジャッジは、エージェントの応答がユーザーの質問のすべての側面を完全に対処しているかどうかを評価します。
# MAGIC
# MAGIC **カスタムジャッジの主要コンポーネント：**
# MAGIC - **name** - 評価結果でのジャッジの識別子
# MAGIC - **instructions** - テンプレート変数を使用した自然言語評価基準
# MAGIC - **feedback_value_type** - 期待される戻り値のタイプ（カテゴリカルな回答に対する "literal"）

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC まず、**フィードバックタイプ** を定義しましょう。`feedback_value_type` はシリアライゼーションでサポートされているタイプの1つで、ジャッジは構造化出力を使用して指定されたタイプを強制します（推奨）。
# MAGIC
# MAGIC 現在、サポートされているタイプは
# MAGIC - **PbValueType**: MLflowの `PbValueType` は、評価でフィードバックや期待値に許可されるプリミティブタイプのセットを表します：`float`、`int`、`str`、または `bool`。フィードバックや期待値フィールドに格納できる値の種類を定義するタイプエイリアスとして使用されます。
# MAGIC - **Literal** タイプとPbValueType値：以下でこれを使用します。
# MAGIC - `dict[str, PbValueType]`
# MAGIC - `list[PbValueType]`
# MAGIC
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">
# MAGIC         <code>make_judge</code>ソースコード
# MAGIC       </strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;">
# MAGIC         <code>make_judge</code>のソースコードは
# MAGIC         <a href="https://mlflow.org/docs/latest/api_reference/_modules/mlflow/genai/judges/make_judge.html" target="_blank">
# MAGIC           こちら
# MAGIC         </a>で読むことができます。
# MAGIC       </p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

from typing import Literal

response_completeness_feedback_value_type = Literal["complete", "partial", "incomplete"]

# COMMAND ----------

# MAGIC %md
# MAGIC フィードバックタイプができたので、以下のコードでは以下を渡します：
# MAGIC - ジャッジの名前、`response_completeness`
# MAGIC - 指示、これは `coherent_instructions` オブジェクトに格納されています
# MAGIC - フィードバック値タイプ、`feedback_value_type`

# COMMAND ----------

from mlflow.genai.judges import make_judge

# 応答完全性のカスタムジャッジを作成
completeness_judge = make_judge(
    name="response_completeness",
    instructions=(
        coherent_instructions
    ),
    feedback_value_type=response_completeness_feedback_value_type
)

# COMMAND ----------

# MAGIC %md
# MAGIC 以下は、`make_judge` で渡すことができるさまざまな引数の要約です。このデモでは一部はカバーされません。
# MAGIC
# MAGIC
# MAGIC
# MAGIC | フィールド名            | 説明 |
# MAGIC |----------------------|-------------|
# MAGIC | `name` | ジャッジの名前。 |
# MAGIC | `instructions` | 評価のための自然言語指示。以下のテンプレート変数のうち **少なくとも1つ** を含む必要があります：`{{inputs}}`、`{{outputs}}`、`{{expectations}}`、`{{conversation}}`、または`{{trace}}`。カスタム変数はサポートされていません。 <br><br> **注意：** `{{conversation}}`は`{{expectations}}`と一緒にのみ使用でき、`{{inputs}}`、`{{outputs}}`、または`{{trace}}`と組み合わせることはできません。 |
# MAGIC | `model` | 評価に使用されるモデル識別子（例：`"openai:/gpt-4"`）。 |
# MAGIC | `description` | ジャッジが評価する内容の説明。 |
# MAGIC | `feedback_value_type` | "Feedback" オブジェクトの `value` フィールドのタイプ仕様。ジャッジは構造化出力を使用してこのタイプを強制します。指定されていない場合、タイプはジャッジによって推論されます。このフィールドを明示的に指定することが **推奨** されます。 <br><br> **サポートされているタイプ（`FeedbackValueType`に一致）：** <br> • `int` — 整数評価（例：1–5スケール） <br> • `float` — 浮動小数点スコア（例：0.0–1.0） <br> • `str` — テキスト応答 <br> • `bool` — はい/いいえ評価 <br> • `Literal[values]` — 列挙型のような選択肢（例：`Literal["good", "bad"]`） <br> • `dict[str, int \| float \| str \| bool]` — 文字列キーとプリミティブ値を持つ辞書 <br> • `list[int \| float \| str \| bool]` — プリミティブ値のリスト <br><br> **注意：** Pydantic `BaseModel` タイプはサポートされていません。 |
# MAGIC | `inference_params` | モデルに渡されるオプションの推論パラメータ辞書（例：`temperature`、`top_p`、`max_tokens`）。これらのパラメータは評価動作の細かい制御を可能にします。低いtemperatureは通常、より決定論的で再現可能な結果をもたらします。 |

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2. カスタムジャッジデータセットの検査
# MAGIC
# MAGIC カスタムジャッジインスタンス `completeness_judge` ができたので、カスタムジャッジのテストに使用する評価データセットを調べましょう。このデータセットには、完全性を評価するためのさまざまなタイプのクエリと応答が含まれています。

# COMMAND ----------

print("Custom Judge Evaluation Dataset:")
pprint(custom_eval)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.3. カスタムジャッジ評価の実行
# MAGIC
# MAGIC 評価データセットに対してカスタムジャッジを実行しましょう。`mlflow.genai.evaluate()` を使用して各例を処理し、完全性評価を生成します。

# COMMAND ----------

completeness_results = mlflow.genai.evaluate(
    data=custom_eval,
    predict_fn=lambda input: agent.predict({"input": input}),
    scorers=[completeness_judge]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.4. カスタムジャッジ結果の検査
# MAGIC
# MAGIC 完全性評価の結果を調べます。ジャッジはカテゴリスコアと各決定を説明する詳細な根拠の両方を提供します。

# COMMAND ----------

print(f"The run ID is: {completeness_results.run_id}")
print(f"The aggregated metrics are: {completeness_results.metrics}")
print("\nThe results from the completeness evaluation:")
display(completeness_results.result_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート3. トレースベースカスタムジャッジの作成

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 3.1. トレースベース評価の理解
# MAGIC
# MAGIC トレースベースジャッジは、エージェントの実行の完全な実行トレースを分析して、エージェント実行中に何が起こったかを理解します。Model Context Protocol（MCP）ツールを使用してトレースを自律的に探索し、以下についての洞察を提供できます：
# MAGIC
# MAGIC - **ツール使用パターン** - 適切なツールが選択され、正しく使用されたかどうか
# MAGIC - **パフォーマンスボトルネック** - 遅いまたは非効率的な実行ステップの特定  
# MAGIC - **実行失敗** - 特定の操作が失敗した理由の理解
# MAGIC - **多段階ワークフロー** - 複雑なエージェント推論チェーンの検証
# MAGIC
# MAGIC <div style="
# MAGIC   border-left: 4px solid #ff9800;
# MAGIC   background: #fff3e0;
# MAGIC   padding: 14px 18px;
# MAGIC   border-radius: 4px;
# MAGIC   margin: 16px 0;
# MAGIC ">
# MAGIC   <strong style="display:block; color:#e65100; margin-bottom:6px; font-size: 1.1em;">
# MAGIC     警告
# MAGIC   </strong>
# MAGIC   <div style="color:#333;">
# MAGIC トレースベースジャッジは<code>make_judge()</code>で<code>model</code>パラメータを指定する必要があります。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. ツール使用ジャッジの作成
# MAGIC
# MAGIC 与えられたリクエストに対してエージェントが適切にツールを使用したかどうかを検証するトレースベースジャッジを作成しましょう。前回と同様に、`feedback_value_type`を作成し、エージェントの設定ファイルからインポートされた指示（`tool_usage_instructions`）を使用します。今回は、ツールが使用されたかどうかを実際に尋ねているだけなので、タイプを `bool` に設定します。

# COMMAND ----------

tool_feedback_value_type = bool

# COMMAND ----------

# ツール使用検証のトレースベースジャッジを作成
tool_usage_judge = make_judge(
    name="tool_usage_validator",
    instructions=(
        tool_usage_instructions
    ),
    feedback_value_type=tool_feedback_value_type,
    model=custom_eval_endpoint  # トレースベースジャッジに必要
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3. トレースデータセットの作成
# MAGIC カスタムジャッジにトレースを渡す方法をデモンストレーションするために、まず次のステップでヘルパー関数 `gen_trace_data()` を使用してセッションIDでトレースを構築する必要があります。これにより、渡されたセッションIDの下に3つの異なるトレースが作成されます（例：`session-demo4-001` がデフォルトで、あなたのユーザー名と一緒に使用されます（これらは **A7. エージェント評価設定の読み込み** で定義されました））。その後、これらの値を使用してトレースを検索します。

# COMMAND ----------

from typing import Tuple, Dict, Any
from mlflow.entities import SpanType

def gen_trace_data(query: str, model :str =custom_eval_endpoint, user_id :str =username, session_id :str =session_id) -> Tuple[Dict[str, Any]]:
    with mlflow.start_span(name = "populate_agent_trace",span_type=SpanType.AGENT) as span:
        mlflow.update_current_trace(
            metadata={
                "mlflow.trace.session": session_id,
                "mlflow.trace.user": user_id
            },
            tags={
                "training_type": "agent_eval_training",
                "model": model,
                "agent_type": "TOOL-CALLING"
            }
        )

        query_payload = [
            {"input": [{"role": "user", "content": query}]}]

        response = agent.predict(query_payload)

        # 可視性のためにスパンレベルで入力と出力をログ
        span.set_inputs({"query": query})
        span.set_outputs({"response": response})
        trace_id = span.trace_id

    return query, trace_id

# COMMAND ----------

# ツール呼び出しをテストするサンプルクエリ
queries = [
    "How many Entire home/apt listings are in the Mission neighborhood?",
    "Count the number of Private room listings in Nob Hill.",
    "What is the average listing price in Haight Ashbury?"
    ]

# Generate traces for the queries
for query in queries:
    gen_trace_data(query=query)

# COMMAND ----------

# MAGIC %md
# MAGIC 次に、次のセルで示すように `experiment_id` と `session_id` を使用してトレースを読み込みます。`session_traces` は、検査することもできるトレースのリストを返します（次のセルの出力を参照）。

# COMMAND ----------

session_traces = mlflow.search_traces(
    locations=[experiment_id],
    filter_string=f"metadata.`mlflow.trace.session` = '{session_id}'",
    return_type="list")
session_traces[0]

# COMMAND ----------

# MAGIC %md
# MAGIC 単一エージェントの応答を実行します。

# COMMAND ----------

trace = session_traces[0]

# 全体の会話セッションを評価
feedback = tool_usage_judge(trace=trace)

# COMMAND ----------

print(f"Assessment: {feedback.value}")
print(f"Rationale: {feedback.rationale}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.4. バッチトレースベースジャッジ評価の実行
# MAGIC
# MAGIC トレースベースジャッジを実行して、実行中にエージェントがどの程度ツールを使用するかを分析します。

# COMMAND ----------

trace_judge_results = mlflow.genai.evaluate(
    data=session_traces,
    scorers=[tool_usage_judge]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.5. トレースジャッジ結果の検査
# MAGIC
# MAGIC トレースベース評価の結果を確認します。ジャッジはツール使用パターンと実行品質についての洞察を提供します。

# COMMAND ----------

print(f"The run ID is: {trace_judge_results.run_id}")
print(f"The aggregated metrics are: {trace_judge_results.metrics}")
print("\nThe results from trace-based evaluation:")
display(trace_judge_results.result_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このデモンストレーションでは、生成AIアプリケーションの包括的な評価のためにMLflowでカスタムLLMジャッジを作成および実装する方法を学びました。応答品質を評価する標準カスタムジャッジと、エージェント実行パターンを分析するトレースベースジャッジの両方を探りました。
# MAGIC
# MAGIC **重要なポイント：**
# MAGIC 1. カスタムジャッジは組み込みスコアラーを超えた柔軟な評価機能を提供します
# MAGIC 2. テンプレート変数により入力、出力、期待値、実行トレースへのアクセスが可能になります
# MAGIC 3. トレースベースジャッジはエージェントのツール使用とワークフローパターンについて深い洞察を提供します
# MAGIC 4. 適切なフィードバック値タイプ設定により一貫した評価結果が保証されます
# MAGIC 5. MLflowの評価フレームワークはカスタムジャッジを既存のワークフローとシームレスに統合します
# MAGIC
# MAGIC これらのカスタム評価機能により、特定のGenAIアプリケーション要件に合わせた堅牢な品質保証プロセスを構築できます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>