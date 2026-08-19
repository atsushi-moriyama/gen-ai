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
# MAGIC # ラボ - MLflowを使用した開発者とSMEフィードバック
# MAGIC
# MAGIC **概要**
# MAGIC
# MAGIC このラボでは、MLflowの人的フィードバック機能を使用した実践的な体験を提供し、異なるレビュアーペルソナからの評価の収集と管理に焦点を当てます。開発イテレーション、ドメインエキスパート評価、エンドユーザー入力収集をサポートするフィードバックワークフローの実装方法を学習します。このラボでは、品質評価と改善のためにトレースとスパンに構造化されたフィードバック、スコア、グラウンドトゥルースを添付できるMLflow Assessmentsについて説明します。
# MAGIC
# MAGIC 人的フィードバックは、自動化されたメトリクスを補完する定性的な洞察を提供するため、AIアプリケーションの改善に不可欠です。このラボでは、複数のステークホルダータイプからフィードバックを体系的に収集、整理、分析し、AIシステムの継続的な改善を推進する方法を実証します。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このラボの終了時には、以下のことができるようになります：
# MAGIC - MLflowアセスメントを使用して、開発者からのフィードバックのワークフローを実装する
# MAGIC - Chat UIを通じたSME（専門家）フィードバック収集の設定
# MAGIC - フィードバックと期待値評価タイプの区別
# MAGIC - MLflowのトレーシングインターフェースでの評価の追加とレビュー
# MAGIC - Databricks notebookでのSMEフィードバックのプログラム的レビュー
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">前提条件</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;"> このラボでは、<strong>01 - Agent Setup</strong>で作成されたエージェントを使用します。続行する前に、そのノートブックを完了していることを確認してください。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必須 - サーバーレスコンピュートの選択
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
# MAGIC **このデモでは、サーバーレスコンピュートはバージョン5である必要があります。** 正しいバージョンを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)を参照してください。
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">必須 - サーバーレスコンピュートの選択</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">続行する前に、このノートブックをサーバーレスコンピュートリソースにアタッチする必要があります。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### クラスルームセットアップ
# MAGIC
# MAGIC 次のセルを実行して、このコースの作業環境を設定してください。
# MAGIC
# MAGIC このセットアップでは以下が実行されます：
# MAGIC - `DA` オブジェクト（Databricks Academyヘルパー）の初期化
# MAGIC - **デフォルトカタログ** と **スキーマ** の設定
# MAGIC - このデモに必要なサポート設定のプロビジョニング
# MAGIC
# MAGIC **注意：** `DA` オブジェクトはDatabricks Academyコースでのみ利用可能です

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-6

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1. 評価タイプ
# MAGIC
# MAGIC MLflowは2つの異なるタイプの評価をサポートしており、それぞれ異なる評価目的に対応します。効果的なフィードバックワークフローを実装するには、これらのタイプを理解することが重要です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. フィードバック評価
# MAGIC
# MAGIC **フィードバック** は、アプリの実際の出力または中間ステップを評価します。「エージェントの応答は良かったか？」などの質問に答えます。フィードバックは、評価やコメントなどのアプリが生成したものを評価し、生成されたコンテンツに対する定性的な洞察を提供します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2. 期待値評価
# MAGIC
# MAGIC **期待値** は、アプリが生成すべき望ましいまたは正しい結果（グラウンドトゥルース）を定義します。例えば、これは「理想的な応答」をユーザーのクエリに対して示すことができます。特定の入力に対して、期待値は常に同じです。期待値はアプリが生成すべきものを定義し、評価データセットの作成に有用です。

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート2. レビュアーペルソナとMLflowサポート
# MAGIC
# MAGIC フィードバックが収集される主要なカテゴリは3つあり、それぞれMLflowエコシステム内で特定のアクセスパターンとユースケースがあります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1. 開発者レビュアー
# MAGIC
# MAGIC **開発者** レビュアーは、MLflow UI内でトレースに直接注釈を付けることができます。これらのレビュアーは完全なワークスペースアクセス権を持ち、開発およびテストフェーズ中に評価を追加できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2. ドメインエキスパートレビュアー
# MAGIC
# MAGIC **ドメインエキスパート** レビュアーは、アプリケーションの出力に構造化されたフィードバックを提供し、正しい応答の **期待値** を定義するために特定されたSMEです。これらのレビュアーは、_高品質な応答とはどのようなものか？_ という質問に答える基準を設定します。ドメインエキスパートフィードバックを収集するアプローチは2つあります：
# MAGIC - [Chat UI](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/live-app-testing)を使用したインタラクティブテスト
# MAGIC - [既存トレースのラベリング](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces)。これは **構造化された** 評価セッションに理想的です。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 2.3. エンドユーザーレビュアー
# MAGIC
# MAGIC **エンドユーザー** レビュアーは、ライブアプリケーションと対話しているユーザーです。これらのユーザーは実世界のパフォーマンスに対する独自の洞察を持ち、修正が必要な問題のあるクエリを特定し、将来のアップデート中に保持すべき成功した対話をハイライトするのに役立ちます。
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #0d47a1; font-size: 1.1em;">注意</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">
# MAGIC このラボでは、開発者とSMEフィードバックシナリオのみに焦点を当てます。<code>FastAPI</code>や<code>React</code>などのバックエンドおよびフロントエンドアプリケーション内でのユーザーフィードバックの詳細については、
# MAGIC <a href="https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/?language=Development">
# MAGIC       このドキュメント
# MAGIC     </a>を参照してください
# MAGIC </p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート3. 開発者フィードバックの実装
# MAGIC
# MAGIC まず、開発者が開発フェーズ中にフィードバックを提供する方法を探索します。MLflowトレーシングでは、開発中にトレースに直接フィードバックや期待値を追加でき、品質問題を記録したり、成功例をマークしたり、将来の参考のためのノートを追加したりする迅速な方法を提供します。
# MAGIC
# MAGIC ラボ初期化スクリプトは、評価用のトレースを作成しました。`demo_lab.run()` を実行すると、エージェントに3つのクエリでストレステストを行い、評価用に利用可能になりました。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1. フィードバック実験への移動
# MAGIC
# MAGIC 以下の手順に従って、フィードバック実験にアクセスし、開発者評価を提供してください：
# MAGIC
# MAGIC 1. 左側メニューの **Workspace** に移動してクリックします
# MAGIC 2. `feedback_experiment` という実験を見つけてクリックします
# MAGIC 3. **feedback-session-001** というセッションを作成しました - **Sessions** をクリックしてこのセッションを表示し、それをクリックします
# MAGIC 4. 左側に **Turn 1** から **Turn 3** が表示されます（下のスクリーンショットを参照）
# MAGIC
# MAGIC ![mlflow-assessment3.png](../Includes/images/feedback evaluation/mlflow-assessment3.png "mlflow-assessment3.png")
# MAGIC
# MAGIC ここで、セッションレベルとトレースレベルの両方で評価を追加できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. トレースレベル評価の表示
# MAGIC
# MAGIC 次に、ツール使用を評価するためのトレースレベル評価を追加します：
# MAGIC
# MAGIC 1. **Turn 1** をクリックし、**View full trace** または **Evaluate trace** を選択します
# MAGIC 2. トレースの右側に **Assessment** が表示されます - それをクリックします（スクリーンショット参照）
# MAGIC
# MAGIC ![mlflow-assessment1.png](../Includes/images/feedback evaluation/mlflow-assessment1.png "mlflow-assessment1.png")
# MAGIC
# MAGIC 3. 画面右側の **Add Feedback** または **Add Expectation** をクリックします
# MAGIC 4. これにより、**Assessment Type** から **Feedback** または **Expectations** を選択し、**Assessment Name** を入力し、**Data Type** から**String**、**Boolean**、または **Number** を選択するサブメニューが作成されます（下のスクリーンショット参照）
# MAGIC
# MAGIC ![mlflow-assessment2.png](../Includes/images/feedback evaluation/mlflow-assessment2.png "mlflow-assessment2.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3. ツール使用評価の設定
# MAGIC
# MAGIC ラボセットアップに基づいて、ツールが使用され、それが実際に正しいものであったことがわかります。以下の値で評価を記入してください：
# MAGIC
# MAGIC - **Assessment Type**: _Expectation_
# MAGIC - **Assessment Name**: `tool_usage`
# MAGIC - **Data Type**: _Boolean_
# MAGIC - **Value**: _True_
# MAGIC - **Rationale**: _そのツールは正しく使用されました。_
# MAGIC
# MAGIC **Create** をクリックしてトレースを閉じます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.4. セッションレベル評価の追加
# MAGIC
# MAGIC 次に、セッションレベル評価を追加しましょう：
# MAGIC
# MAGIC 1. Turn 1と同じプロセスを使用して、他の2つのターンを評価できます
# MAGIC 2. メインセッションメニューに戻り、**Session scorers** > **Feedback** の下の **Add Feedback** をクリックします
# MAGIC 3. 以下の値を記入します：
# MAGIC    - **Assessment Type**: フィードバック
# MAGIC    - **Assessment Name**: _ready_for_sme_feedback_
# MAGIC    - **Data Type**: _String_
# MAGIC    - **Value**: _True_
# MAGIC    - **Rationale**: _各ターンでの成果物を確認した結果、結果は正確であり、テストは完了し、SMEによるレビューの準備が整っています。_
# MAGIC 4. **Create** をクリックします
# MAGIC
# MAGIC **注意：** これで、次のセクションで説明するSMEレビュー用に送信する準備が整いました。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.. SMEフィードバックの実装
# MAGIC
# MAGIC 次に、SME（専門家）フィードバックを実装します。あなたがレビュー用のSMEとして行動していると仮定します。SMEフィードバック収集には2つのアプローチがあります：
# MAGIC
# MAGIC 1. **Chat UIを使用したインタラクティブテスト**
# MAGIC 2. **既存トレースのラベリング**
# MAGIC
# MAGIC このラボでは、Chat UIアプローチを使用します。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 4.1. エージェントフレームワークを使用したエージェントのデプロイ
# MAGIC
# MAGIC 次に、model serving エンドポイントにデプロイされたモデルが必要です。`databricks` SDKクラス `agent.deploy()` メソッドを使用します。必要なのは `model_name` と `uc_model_info` だけで、これらは両方ともクラスルームセットアップの一部として作成されました。
# MAGIC
# MAGIC **注意：** 時間の都合上、これは **01 Demo - Agent Setup** の実行の一部として実行されています。
# MAGIC
# MAGIC エージェントをデプロイする方法を示すコードスニペットは以下の通りです：
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.tracking import MlflowClient
# MAGIC from databricks import agents
# MAGIC
# MAGIC model_name = f"{catalog_name}.{schema_name}.{agent_name}"  # UC FQN
# MAGIC alias = "Champion"
# MAGIC
# MAGIC client = MlflowClient()
# MAGIC mv = client.get_model_version_by_alias(model_name, alias)
# MAGIC
# MAGIC # ModelVersionオブジェクトではなく、バージョンを渡す
# MAGIC deployment = agents.deploy(
# MAGIC     model_name=model_name,
# MAGIC     model_version=int(mv.version),  # strも動作します；明確にするためintにキャスト
# MAGIC     scale_to_zero=True
# MAGIC )
# MAGIC print("Endpoint:", deployment.endpoint_name)
# MAGIC ```
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
# MAGIC <code>scale_to_zero=True</code>は、エージェントエンドポイントがワークスペースリソースにスケールダウンされる可能性があることを意味します。これは、最初のクエリの実行に時間がかかる場合があることを意味します。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2. Chat UIを使用したインタラクティブテスト
# MAGIC
# MAGIC [`get_review_app()`](https://mlflow.org/docs/latest/api_reference/_modules/mlflow/genai/labeling.html#get_review_app)メソッドを使用して、レビューアプリを取得または作成します。
# MAGIC
# MAGIC **警告：** **ドメインエキスパート** がレビューアプリのChat UIを使用するには、以下の権限が必要です：
# MAGIC
# MAGIC - **アカウントアクセス**：Databricksアカウントでプロビジョニングされている必要がありますが、ワークスペースアクセスは *必要ありません*
# MAGIC - **エンドポイントアクセス**：モデル提供エンドポイントの `CAN_QUERY` 権限
# MAGIC - **MLflowアクセス**：MLflow実験に対する `CAN_EDIT` 権限を持つワークスペースアクセス
# MAGIC
# MAGIC ワークスペースアクセスを持たないユーザーの場合、アカウント管理者は以下を行うことができます：
# MAGIC - アカウントレベルのSCIMプロビジョニングを使用して、アイデンティティプロバイダーからユーザーを同期
# MAGIC - Databricksでユーザーとグループを手動で登録
# MAGIC
# MAGIC 詳細については、[ユーザーとグループの管理](https://docs.databricks.com/aws/en/admin/users-groups/scim/)を参照してください。

# COMMAND ----------

from mlflow.genai.labeling import get_review_app

review_app = get_review_app()

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3. レビューアプリの設定
# MAGIC
# MAGIC レビューアプリをエージェントに接続しましょう。次のセルの出力にはレビューアプリのURLが含まれます。それをクリックすると、以下のことができます：
# MAGIC
# MAGIC - ウェブブラウザーを通じてチャットインターフェースにアクセス
# MAGIC - 質問を入力してアプリケーションと対話
# MAGIC - 組み込みのフィードバックコントロールを使用して各応答後にフィードバックを提供
# MAGIC - 複数の対話をテストするために会話を継続
# MAGIC
# MAGIC **代替UIアプローチ：** 左側メニューの **Serving** に移動し、デプロイされたエージェントをクリックし、**Use** の横のドロップダウンメニューを選択して **Open review app** を選択することもできます。

# COMMAND ----------

# MAGIC %md
# MAGIC 次のコードスニペットでは、ラボセットアップの一部として作成された `agent_name` と `model_username_string` 文字列変数を使用しています。

# COMMAND ----------

review_app.add_agent(
    agent_name = agent_name,
    model_serving_endpoint = model_username_string
)

print(f"Share this URL: {review_app.url}/chat")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.4. テストクエリとフィードバックの提供
# MAGIC
# MAGIC 次に、クエリを渡してフィードバックを提供しましょう。便宜上、**Copy to clipboard** ボタンが追加されています - それをクリックしてクエリをコピーしてください。レビューアプリに貼り付けてください。以下は画面の表示例のスクリーンショットです：
# MAGIC
# MAGIC ![feedback-app.png](../Includes/images/feedback evaluation/feedback-app.png "feedback-app.png")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC ミッションには個室がいくつありますか？
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

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.5. フィードバックの送信
# MAGIC
# MAGIC フィードバックを追加しましょう。結果は良好で、ツールが使用されたことが明確に確認できるはずです。前のスクリーンショットで示されているように、**Awaiting Feedback** ウィンドウで **Yes** を選択した後、以下をフィードバックにコピー＆ペーストしてください。貼り付け後、**Done** をクリックしてください。フィードバックが送信されたというメッセージが表示されます。
# MAGIC
# MAGIC ![feedback-app2.png](../Includes/images/feedback evaluation/feedback-app2.png "feedback-app2.png")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <button onclick="copyBlock()">クリップボードにコピー</button>
# MAGIC
# MAGIC <pre id="copy-block" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; padding:14px 16px; font-size:0.85rem; line-height:1.35; white-space:pre;">
# MAGIC <code>
# MAGIC エージェントは「他に何かお手伝いできることはありますか？」という言葉で締めくくるべきです。
# MAGIC </code></pre>
# MAGIC
# MAGIC <script>
# MAGIC function copyBlock() {
# MAGIC   const el = document.getElementById("copy-block");
# MAGIC   if (!el) return;
# MAGIC
# MAGIC   const text = el.innerText;
# MAGIC
# MAGIC   // 推奨される最新のAPI
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
# MAGIC ### 4.6. 送信されたフィードバックの表示
# MAGIC
# MAGIC **Serving** のmodel serving エンドポイントに戻り、**Traces** をクリックして最新のトレースを選択してください（トレースがすぐに表示されない場合は、リロードアイコンをクリックする必要があるかもしれません）。トレース画面では、おなじみの出力が表示されますが、送信したフィードバックも表示されます（下のスクリーンショット参照）。
# MAGIC
# MAGIC ![feedback-app3.png](../Includes/images/feedback evaluation/feedback-app3.png "feedback-app3.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.7. ノートブックでのSMEフィードバックの表示
# MAGIC
# MAGIC 上記で述べたように、MLflowトレースはUIを使用して利用可能ですが、次のセルで示すように、SMEからの評価をプログラム的に表示することもできます。これにより、必要に応じて下流でのレポート機能が可能になります。まず `get_experiment_by_name()` でmlflow実験を取得し、次に `search_traces()` で実験名を挿入してトレースを検索します。この例では、デプロイされたモデルにリンクされたトレースなので `eval_demo_experiment` を使用していることに注意してください。また、ラボセットアップの一部として作成された `deployed_model_experiment_loc` の保存された値も使用しています。これは実験 `eval_demo_experiment` の場所です。
# MAGIC
# MAGIC 次のセルを実行した後、スクロールして1つのレコードの評価を展開してください。これにより最新の評価が表示されます（生成されたPandas dataframeで `head(1)` を使用したため）。

# COMMAND ----------

deployed_model_experiment_loc

# COMMAND ----------

import pandas 

mlflow.set_tracking_uri("databricks")

## 実験IDの解決
exp = mlflow.get_experiment_by_name(deployed_model_experiment_loc)
exp_id = exp.experiment_id
print("Experiment ID:", exp_id)

## 文字列実験IDを使用してトレースをクエリ；安全な表示のためにトップレベルフィールドに制限
traces_df = mlflow.search_traces(
    locations=[str(exp_id)],            ## strである必要があります
    include_spans=True,                ## 重いネストされたスパンツリーを除外
    return_type="pandas"
)
traces_df.head(1)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このラボでは、異なるレビュアーペルソナにわたってMLflowを使用した人的フィードバックワークフローを正常に実装しました：
# MAGIC
# MAGIC - MLflow UI でのダイレクトトレース注釈による **開発者からのフィードバック**
# MAGIC - **SMEからのフィードバック**：リアルタイム評価のための対話型チャットUIの活用
# MAGIC
# MAGIC フィードバックと期待値評価タイプの区別、MLflowのトレーシングインターフェースのナビゲーション、異なるレビュアータイプに必要な権限とアクセスパターンの理解を学習しました。これらのスキルは、構造化された人的フィードバック収集を通じて継続的に改善される堅牢なAIアプリケーションを構築するために不可欠です。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>