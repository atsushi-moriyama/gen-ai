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
# MAGIC # デモ - MLflow組み込みジャッジの使用
# MAGIC **概要** 
# MAGIC
# MAGIC このデモンストレーションでは、AIエージェントを評価するためのMLflowの組み込みジャッジについて探求します。組み込みジャッジは、手動レビューを必要とせずにAIエージェントの応答の品質と正確性を評価するのに役立つ、研究で検証された自動評価機能を提供します。
# MAGIC
# MAGIC このデモでは、MLflowの評価フレームワークを活用してエージェントのパフォーマンスを標準化されたメトリクスを使用して体系的に評価する方法を学習します。正確性と安全性という2つの主要な評価次元に焦点を当て、これらのジャッジがAIアプリケーションに対して客観的な品質評価を提供する方法を実演します。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このデモンストレーションの終了時には、以下のことができるようになります：
# MAGIC
# MAGIC 1. **LLMジャッジ** と、自動エージェント評価におけるその役割を理解する
# MAGIC 2. 正しさと安全性の評価のために、**MLflowに組み込まれたジャッジを設定・使用する**
# MAGIC 3. 複数のスコアラーを用いた`mlflow.genai.evaluate()`を使用して、**包括的な評価を実行する**
# MAGIC 4. **評価結果を解釈し**、詳細な分析のためにMLflowのトレース機能を活用する
# MAGIC 5. 評価モデルと構成管理を分離するための **ベストプラクティスを適用する**
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
# MAGIC サーバーレスのバージョンを確認または変更するには、サーバーレスの依存関係に関するDatabricksドキュメントを参照してください。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### コンピュート要件
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモではサーバーレスコンピュートはバージョン5である必要があります。** 正しいバージョンを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies) を参照してください。
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
# MAGIC このセットアップでは以下が行われます：
# MAGIC - `DA` オブジェクト（Databricks Academyヘルパー）の初期化
# MAGIC - **デフォルトカタログ** と **スキーマ** の設定
# MAGIC - このデモに必要なサポート設定のプロビジョニング
# MAGIC
# MAGIC **注意：** `DA` オブジェクトはDatabricks Academyコースでのみ利用可能です

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-2

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の補足事項：**
# MAGIC
# MAGIC このデモ全体を通して、`DA` オブジェクトを参照します。このオブジェクトはDatabricks Academyによって提供され、ユーザー名、カタログ名、スキーマ名、作業ディレクトリ、データセットの場所などの変数が含まれています。これらの詳細を表示するには、以下のコードブロックを実行してください：

# COMMAND ----------

print(f"Username:          {DA.username}")
print(f"Catalog Name:      {DA.catalog_name}")
print(f"Schema Name:       {DA.schema_name}")
print(f"Working Directory: {DA.paths.working_dir}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### データセットアクセスの設定
# MAGIC
# MAGIC このデモンストレーションは、Databricks MarketplaceのAirbnbデータセットに依存しています。
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #0d47a1; font-size: 1.1em;">データセット情報</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">すべてのUnity Catalogとワークスペースの設定は、<strong>01 Demo - Agent Setup</strong>の実行の一部として適切にセットアップされ、テストされています。</code></p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1. LLMジャッジの理解

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. LLMジャッジとは何ですか？
# MAGIC
# MAGIC LLMジャッジは、品質評価にLLMを使用するMLflowの `Scorer` の一種です。`scorer` は、MLflowのエージェント評価フレームワークの重要なコンポーネントです。モデル、エージェント、アプリケーションの評価基準を定義するための統一されたインターフェースを提供します。
# MAGIC
# MAGIC **LLMジャッジの主要な特徴：**
# MAGIC - 人間の介入なしの **自動評価**
# MAGIC - **研究で検証された** 評価基準
# MAGIC - スコアと根拠の両方を含む **構造化されたフィードバック**
# MAGIC - 大規模評価ワークフローに対する **スケーラビリティ**

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2. スコアラーは従来のMLメトリクスとどう違うのですか？
# MAGIC
# MAGIC スコアラーはより柔軟で、従来のMLの意味で通常メトリクスとして表現されるスカラー値に加えて、より構造化された品質フィードバックを返すことができます。
# MAGIC
# MAGIC **従来のMLメトリクス：**
# MAGIC - 単一の数値（精度、F1スコア、RMSE）を返す
# MAGIC - 統計的パフォーマンスに焦点
# MAGIC - 予測が失敗した理由についての限られたコンテキスト
# MAGIC
# MAGIC **MLflowスコアラー：**
# MAGIC - 値と根拠を含む構造化された `Feedback` オブジェクトを返す
# MAGIC - 関連性、正確性、安全性などの質的側面を評価
# MAGIC - 評価決定の詳細な説明を提供
# MAGIC - バイナリ（「はい」/「いいえ」）と連続スコアリングの両方をサポート

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. 品質はどのように測定されますか？
# MAGIC
# MAGIC Databricksは以下を通じてジャッジの品質を継続的に改善しています：
# MAGIC - **研究による検証**：人間の専門家の判断との比較
# MAGIC - **指標の追跡**：[コーエンのカッパ係数](https://en.wikipedia.org/wiki/Cohen%27s_kappa)、精度、F1スコア
# MAGIC - **多様なテスト**：学術データセットおよび実世界データセットを用いた検証
# MAGIC
# MAGIC **品質保証プロセス：**
# MAGIC 1. **人間ベースラインの確立** - 専門家アノテーターがグラウンドトゥルース評価を作成
# MAGIC 2. **ジャッジパフォーマンス測定** - ジャッジの出力を人間の評価と比較
# MAGIC 3. **継続的改善** - パフォーマンスメトリクスと新しい研究に基づく定期的な更新
# MAGIC 4. **クロスバリデーション** - 異なるドメインとユースケースでのテスト

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 1.4. `mlflow.genai.judges` と `mlflow.genai.scorers`の違いは何ですか？
# MAGIC
# MAGIC これら2つのPythonモジュールの違いは、`judges` がスコアラーのサブセットであり、LLMジャッジがLLMベースの品質評価に焦点を当てた特殊なスコアラーとして機能することと考えることができます。対照的に、スコアラーはデータ抽出を処理し、適切なジャッジまたはアルゴリズムにルーティングすることで評価を調整します。多くの場合、自動化されたトレースレベル評価のために、ジャッジをスコアラー内にラップします。
# MAGIC
# MAGIC **モジュール階層：**
# MAGIC - **`mlflow.genai.scorers`** - LLMジャッジとその他のスコアリング方法の両方を含む高レベル評価インターフェース
# MAGIC - **`mlflow.genai.judges`** - 特定のLLMベース評価関数（スコアラーのサブセット）
# MAGIC
# MAGIC **それぞれを使用するタイミング：**
# MAGIC - `mlflow.genai.evaluate()` と自動ワークフローとの統合には **スコアラー** を使用
# MAGIC - 単一インスタンス評価またはカスタムスコアリングロジックには **ジャッジ** を直接使用
# MAGIC
# MAGIC このデモは `mlflow.genai.scorers` に集中するため、各評価（`scorers` モジュールの場合）は3つのコンポーネントによって定義されることに注意することが重要です：
# MAGIC - **データセット**: 入力と期待値（およびオプションで事前生成された出力とトレース）
# MAGIC - **スコアラー**: 評価基準
# MAGIC - **予測関数**: データセットの出力を生成
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">注意</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;">
# MAGIC         MLflowのGenAI評価システムについて詳しくは
# MAGIC         <a
# MAGIC           href="https://mlflow.org/docs/latest/genai/eval-monitor/#running-an-evaluation"
# MAGIC           target="_blank"
# MAGIC           rel="noopener noreferrer"
# MAGIC           style="color: #1976d2; text-decoration: underline;"
# MAGIC         >
# MAGIC           こちら
# MAGIC         </a>をご覧ください。
# MAGIC       </p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート2. 組み込みジャッジの概要
# MAGIC MLflowは、入力/出力ガイドラインや正確性などの一般的なユースケースに対して研究で検証されたジャッジを提供します。このデモンストレーションでは、いくつかの例を取り上げます。完全性のために、タイプに基づいて利用可能なスコアラーのリストを提供します。組み込みジャッジの完全なリストについては、[このドキュメント](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/scorers#built-in-llm-judges)を参照してください。
# MAGIC
# MAGIC ### 単一ターンスコアラー
# MAGIC 単一ターンスコアラーは、ユーザーからの単一の入力またはプロンプトに対するモデルの応答の品質、正確性、または関連性を評価します。各入力-応答ペア（またはターン）は独立してスコア付けされ、以前のコンテキストや後続の会話ターンは考慮されません。
# MAGIC | ジャッジ | 引数 | グラウンドトゥルースが必要 | 評価内容 |
# MAGIC |------|-----------|-----------------------|------------------|
# MAGIC | RelevanceToQuery | `inputs`, `outputs` | いいえ | 応答がユーザーのリクエストに直接関連しているかどうかを判定します。 |
# MAGIC | RetrievalRelevance | `inputs`, `outputs` | いいえ | 取得されたコンテキストがユーザーのリクエストに直接関連しているかどうかを評価します。 |
# MAGIC | Safety | `inputs`, `outputs` | いいえ | コンテンツが有害、攻撃的、または毒性のある素材から自由であるかどうかをチェックします。 |
# MAGIC | RetrievalGroundedness | `inputs`, `outputs` | いいえ | 応答が提供されたコンテキストに基づいているか、エージェントが幻覚を起こしているかを評価します。 |
# MAGIC | Correctness | `inputs`, `outputs`, `expectations` | はい | 提供されたグラウンドトゥルースと比較して応答が正しいかどうかを判定します。 |
# MAGIC | RetrievalSufficiency | `inputs`, `outputs`, `expectations` | はい | 取得されたコンテキストがグラウンドトゥルースの事実を含む応答を生成するために必要なすべての情報を含んでいるかどうかを評価します。 |
# MAGIC | Guidelines | `inputs`, `outputs` | いいえ | 応答が指定された自然言語ガイドラインを満たしているかどうかをチェックします。 |
# MAGIC | ExpectationsGuidelines | `inputs`, `outputs`, `expectations` | いいえ（`expectations` にガイドラインが必要） | 応答が期待値で定義された例ごとの自然言語基準を満たしているかどうかを評価します。 |
# MAGIC
# MAGIC
# MAGIC ### マルチターンスコアラー
# MAGIC
# MAGIC マルチターンスコアラーは、個別のターンではなく、会話セッション全体を評価します。セッションIDを持つトレースが必要で、MLflow 3.7.0では実験的機能です。
# MAGIC
# MAGIC | スコアラー | 評価内容 | セッションが必要 |
# MAGIC |-------|------------------|------------------|
# MAGIC | ConversationCompleteness | エージェントが会話全体を通してすべてのユーザーの質問に対処しているかどうかを判定します。 | はい |
# MAGIC | ConversationalRoleAdherence | アシスタントが会話全体を通して割り当てられた役割を一貫して維持しているかどうかを評価します。 | はい |
# MAGIC | ConversationalSafety | アシスタントの応答が安全で、有害または不適切なコンテンツから自由であるかどうかをチェックします。 | はい |
# MAGIC | ConversationalToolCallEfficiency | 会話全体でのツール使用が効率的、適切、非冗長であったかどうかを評価します。 | はい |
# MAGIC | KnowledgeRetention | アシスタントが以前のユーザー入力からの情報を正しく保持し適用しているかどうかを評価します。 | はい |
# MAGIC | UserFrustration | ユーザーが会話中にフラストレーションを示しているかどうか、そのフラストレーションが効果的に解決されたかどうかを判定します。 | はい |

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート3. 組み込みジャッジの例

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1. 例1：正確性評価
# MAGIC
# MAGIC ここでは `Correctness` ジャッジの使用を見ていきます。これは、提供されたグラウンドトゥルース情報と比較してアプリケーションの応答が事実的に正しいかどうかを評価し、 `expected_facts` または `expected_response` として定義されます。事前生成された出力を渡すのではなく、前のデモで構築したカスタムエージェントからの出力を評価することに注意してください。
# MAGIC
# MAGIC **"Correctness" ジャッジが評価する内容：**
# MAGIC - 応答にすべての期待される事実が含まれているかどうか
# MAGIC - その応答が提供されたグラウンドトゥルースと矛盾する場合
# MAGIC - 生成されたコンテンツの全体的な事実の正確性
# MAGIC
# MAGIC **入力要件：**
# MAGIC - **グラウンドトゥルースデータ** - `expected_facts`（事実の陳述のリスト）または `expected_response`（完全な期待される回答）のいずれか
# MAGIC - **応答データ** - エージェントまたはモデルからの実際の出力
# MAGIC - **オプションのコンテキスト** - 評価に役立つ追加情報

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.1.1 "Correctness" ジャッジインスタンスの作成
# MAGIC
# MAGIC `correctness_eval` という `Correctness` クラスのインスタンスを作成します。デフォルトでは、組み込みジャッジは評価タスクに最適化されたDatabricksホスト型LLMを使用しますが、`model` パラメータを使用して異なるモデルを指定することができます。
# MAGIC
# MAGIC **モデル指定形式：** `<provider>:/<model-name>`
# MAGIC - Databricksモデルの場合：`databricks:/model-endpoint-name`
# MAGIC - OpenAIモデルの場合：`openai/gpt-4o`
# MAGIC - その他のLiteLLM互換プロバイダーの場合：`provider/model-name`

# COMMAND ----------

from mlflow.genai.scorers import Correctness

correctness_eval = Correctness(
    model=correctness_eval_endpoint)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC #### 3.1.2 評価データセットの読み込み
# MAGIC
# MAGIC 次に、ボリューム `agent_vol` に `correctness_eval` として保存されている評価データセットを読み込みます。これには評価用の2つの異なるデータポイントがあることに注意してください。もちろん、独自のプロジェクトではより多くを使用する必要があります。
# MAGIC
# MAGIC **正確性評価のためのデータセット構造：**
# MAGIC - **inputs** - エージェントに送信されるクエリまたはリクエスト
# MAGIC - **outputs** - エージェントによって生成された応答（一部の評価モードではオプション）
# MAGIC - **expectations** - 以下のいずれかを含むグラウンドトゥルース情報：
# MAGIC   - `expected_facts`: 存在すべき事実の陳述のリスト
# MAGIC   - `expected_response`: 比較用の完全な期待される回答
# MAGIC
# MAGIC 次のセルを実行すると、評価データセットが表示されます。
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">
# MAGIC         その他の評価データタイプの理解
# MAGIC       </strong>
# MAGIC       <ul style="margin: 12px 0 0 16px; color: #333;">
# MAGIC         <li>
# MAGIC           直接評価のデータ形式のリストについては、
# MAGIC           <a href="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/eval-harness#data-formats-for-direct-evaluation">
# MAGIC             このドキュメント
# MAGIC           </a>を参照してください。
# MAGIC         </li>
# MAGIC         <li>
# MAGIC           解答シート評価のデータ形式のリストについては、
# MAGIC           <a href="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/eval-harness#data-formats-for-answer-sheet-evaluation">
# MAGIC             このドキュメント
# MAGIC           </a>を参照してください。
# MAGIC         </li>
# MAGIC         <li>
# MAGIC           SDKでMLflow評価データセットを使用することについての詳細は、
# MAGIC           <a href="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/eval-datasets#mlflow-evaluation-dataset-sdk-reference">
# MAGIC             このドキュメント
# MAGIC           </a>を参照してください。
# MAGIC         </li>
# MAGIC       </ul>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

import json 
from pprint import pprint
from pathlib import Path

path = Path(f"/Volumes/{catalog_name}/{schema_name}/agent_vol/correctness_eval.json")

with path.open("r", encoding="utf-8") as f:
    eval_dataset = json.load(f)

pprint(eval_dataset)

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.1.3 "correctness" の評価を実行する
# MAGIC
# MAGIC 次に、データセット `eval_dataset` を評価します。次のセルに示されている `mlflow.genai.evaluate()` の入力パラメータを分解してみましょう：
# MAGIC - **data**: これはスコアラーに公開する評価データセットです。
# MAGIC - **predict_fn**: これはラムダ関数を使用して、上記で読み込まれたエージェント（`agent`）を事前定義された `predict` メソッドを使用して呼び出します。
# MAGIC - **scorers**: これは評価したい評価のリストです。この場合、上記で `Correctness` クラスを使用してインスタンス化された `correctness_eval` のみに関心があります。
# MAGIC
# MAGIC **評価プロセス：**
# MAGIC 1. **データの反復** - MLflowが評価データセットの各項目を処理
# MAGIC 2. **予測の生成** - エージェントが各入力に対して応答を生成
# MAGIC 3. **トレースの作成** - MLflowが各予測に対してトレースを自動作成
# MAGIC 4. **ジャッジ評価** - "Correctness" ジャッジが応答を期待される事実と比較（`<catalog_name>.<schema_name>.agent_vol` で見つけることができます）
# MAGIC 5. **結果の集計** - 個別のスコアがサマリーメトリクスにコンパイル
# MAGIC
# MAGIC **指示：**
# MAGIC
# MAGIC - 次のセルを実行した後、出力にはMLflowで評価結果を表示するボタンが含まれます。それをクリックしてください。
# MAGIC - 以下のような画面で **MLflow Experiments** に移動します。
# MAGIC
# MAGIC ![mlflow-evaluation-runs.png](../Includes/images/built-in agents with mlflow/mlflow-evaluation-runs.png "mlflow-evaluation-runs.png")
# MAGIC - 最新の実行をクリックすると、より詳細なトレースが表示されます。以下は例です。フィードバックと期待される出力を確認して、評価が **Pass** または **Fail** として返された理由を理解できます。一般的に、これはすべてのメトリクスで発生します。
# MAGIC
# MAGIC ![mlflow-evaluation-runs2.png](../Includes/images/built-in agents with mlflow/mlflow-evaluation-runs2.png "mlflow-evaluation-runs2.png")
# MAGIC - また、クエリからのリクエストを示すトレースも表示されます

# COMMAND ----------

correctness_results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=lambda input: agent.predict({"input": input}),
    scorers=[correctness_eval],
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.1.4 "correctness" の結果の確認
# MAGIC
# MAGIC 結果は **EvaluationResult** オブジェクトで、実行ID、集計されたメトリクス、および `results_df` と呼ばれるデータフレームが含まれており、これはさらなる検査のための行ごとのサマリーPandas dataframeです。
# MAGIC
# MAGIC **EvaluationResultコンポーネント：**
# MAGIC - **run_id** - MLflowでのこの評価実行の一意の識別子
# MAGIC - **metrics** - 集計されたパフォーマンスメトリクス（例：平均正確性スコア）
# MAGIC - **result_df** - 個別のスコアと根拠を含む詳細な例ごとの結果
# MAGIC
# MAGIC **結果の理解：**
# MAGIC - **Value** - "yes" は正しい応答を示し、"no" は不正確を示す
# MAGIC - **Rationale** - ジャッジの決定の詳細な説明
# MAGIC - **トレースリンク** - 任意の行をクリックして完全なMLflowトレースを表示
# MAGIC
# MAGIC **指示：**
# MAGIC 次のセルを実行した後、任意の行をクリックすると、さらなる検査のためのMLflowトレースが表示されます。

# COMMAND ----------

print(f"The run ID is: {correctness_results.run_id}")
print(f"The aggregated metrics are: {correctness_results.metrics}")
print("\nThe results from the previous batch of inputs:")
display(getattr(correctness_results, "result_df", None))

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 3.2. 例2：安全性評価
# MAGIC
# MAGIC 安全性評価は、コンテンツが有害、攻撃的、または毒性のある素材から自由であるかどうかを測定します。このジャッジは、応答が安全ガイドラインを満たし、不適切なコンテンツを含まないことを確認する必要があるアプリケーションにとって特に価値があります。
# MAGIC
# MAGIC **Safetyジャッジは評価を行う：**
# MAGIC - コンテンツが有害、攻撃的、または不適切な素材を含んでいるかどうか
# MAGIC - 回答が安全に関するガイドラインおよび基準を満たしている場合
# MAGIC - 生成されたコンテンツの全体的な安全性と適切性
# MAGIC
# MAGIC **安全性の要件：**
# MAGIC - **入力と出力コンテンツ** - ジャッジはユーザー入力とエージェント応答の両方を調査
# MAGIC - **グラウンドトゥルース不要** - 安全性評価には期待される応答は必要ない
# MAGIC - **コンテンツ分析** - ジャッジは安全性違反と不適切な素材についてテキストを調査
# MAGIC
# MAGIC `Safety` クラスをインポートして再び `mlflow.genai.evaluate()` を使用することで、上記と同じタイプのワークフローをこのメトリクスに適用できます
# MAGIC
# MAGIC **指示：**
# MAGIC 次の2つのセルを実行し、**MLflowで評価結果を表示** をクリックして出力を再び検査してください。どの出力がSafetyメトリクスで失敗しましたか？理由を理解するためにフィードバックを読んでください。

# COMMAND ----------

from mlflow.genai.scorers import Safety

safety_eval = Safety(
    model=safety_eval_endpoint)

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.2.1 安全性評価データセットの読み込み
# MAGIC
# MAGIC 次に、さまざまな安全性シナリオをテストする例を含む安全性評価データセットを読み込みます。このデータセットはボリュームに `safety_eval` として保存されており、安全性応答を評価するためのさまざまなタイプのコンテンツが含まれています。

# COMMAND ----------

path = Path(f"/Volumes/{catalog_name}/{schema_name}/agent_vol/safety_eval.json")

with path.open("r", encoding="utf-8") as f:
    safety_eval_dataset = json.load(f)

pprint(safety_eval_dataset)

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.2.2 安全性評価の実行
# MAGIC
# MAGIC 次に、同じ評価フレームワークを使用して安全性データセットを評価します。Safetyジャッジは、エージェントの回答に有害、不快、または不適切な内容が含まれていないかを審査します。

# COMMAND ----------

safety_results = mlflow.genai.evaluate(
    data=safety_eval_dataset,
    predict_fn=lambda input: agent.predict({"input": input}),
    scorers=[safety_eval],
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### 3.2.3 `Safety` 結果の理解
# MAGIC
# MAGIC "Safety' スコアラーは有害または不適切な素材についてコンテンツを評価し、エージェントの応答の安全性についての洞察を提供します：
# MAGIC
# MAGIC **結果の解釈：**
# MAGIC - **"yes"** - コンテンツは安全で適切
# MAGIC - **"no"** - コンテンツに有害、攻撃的、または不適切な素材が含まれている
# MAGIC - **Rationale** - 特定された安全性の懸念の詳細な説明
# MAGIC
# MAGIC **一般的な安全性の懸念：**
# MAGIC - **有害なコンテンツ** - 暴力、ヘイトスピーチ、または危険な指示
# MAGIC - **不適切な素材** - アダルトコンテンツまたは攻撃的な言語
# MAGIC - **毒性のある行動** - ハラスメント、いじめ、または差別的なコンテンツ
# MAGIC
# MAGIC この評価は、エージェントがさまざまなタイプのユーザーインタラクションにわたって適切な安全基準を維持することを確実にするのに役立ちます。

# COMMAND ----------

print(f"The run ID is: {safety_results.run_id}")
print(f"The aggregated metrics are: {safety_results.metrics}")
print("\nThe results from the safety evaluation:")
display(getattr(safety_results, "result_df", None))

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート4. 複数のメトリクスを一度に評価
# MAGIC
# MAGIC `mlflow.genai.evaluate()` を使用すると、1回の呼び出しで複数の評価スコアラーを実行し、"scorers" パラメータにリストを渡すことで、すべての結果メトリクスを単一の評価実行でログできます。これを行うには、例えば `scorers=[safety_eval, correctness_eval]` を設定することで、スコアラーのリストにさらに追加するだけです。
# MAGIC
# MAGIC **指示：**
# MAGIC 次のセルを実行した後、前と同様に評価を検査してください。トレースを検査する際、`correctness` と `Safety` の両方が存在することがわかります。
# MAGIC
# MAGIC ![mlflow-evaluation-runs3.png](../Includes/images/built-in agents with mlflow/mlflow-evaluation-runs3.png "mlflow-evaluation-runs3.png")

# COMMAND ----------

scorers = [safety_eval, correctness_eval]
mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=lambda input: agent.predict({"input": input}),
    scorers=scorers
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このデモンストレーションでは、自動エージェント評価のためのMLflowの組み込みジャッジを活用する方法を成功裏に学習しました。2つの重要な評価次元を探求しました：
# MAGIC
# MAGIC 1. **正確性評価** - グラウンドトゥルースに対する事実の正確性の評価
# MAGIC 2. **安全性評価** - コンテンツが有害または不適切な素材から自由であるかどうかの評価
# MAGIC
# MAGIC これらの組み込みジャッジは、OOBのLLM評価に有用ですが、[ガイドラインジャッジ、カスタムジャッジ、コードベースのスコアラー](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/scorers#built-in-llm-judges)など、探求すべき他のアプローチもあります。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>