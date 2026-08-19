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
# MAGIC # MLflowとエージェント開発
# MAGIC
# MAGIC ## はじめに
# MAGIC
# MAGIC 検索エージェントの構築は、標準的なモデルの訓練とは異なります。ユーザークエリ、埋め込みモデル、Vectorデータベース、大規模言語モデル間の動的な相互作用を調整する必要があります。このレッスンでは、**MLflow 3.0+** がこれらのエージェントを開発、デバッグ、ガバナンスするために必要なインフラストラクチャをどのように提供するかを探求します。単純なロギングを超えて、検索ステップの深いトレーサビリティとDatabricks Unity Catalogを使用したエージェントアーティファクトのガバナンスを探求します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC * **MLflowのコンポーネント** の中核とエージェント開発における特定の役割を特定する。  
# MAGIC * プロンプトと検索設定のバリエーションを追跡するための **エクスペリメント** を設定する。  
# MAGIC * 標準的なモデルフレーバーと **GenAI固有のフレーバー**（LangChain、PyFunc）を区別する。  
# MAGIC * **MLflow tracing** を利用して、特定の検索失敗（空の検索結果、高レイテンシなど）を診断する。  
# MAGIC * **Unity Catalog model registry** を使用して検索エージェントを登録し、ガバナンスする。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. エージェント向けMLflowの基盤
# MAGIC
# MAGIC MLflowは、エンドツーエンドの機械学習ライフサイクルを管理するために設計されたオープンソースプラットフォームです。エージェント開発の文脈では、すべての設定、コードバージョン、実行トレースの中央記録システムとして機能します。
# MAGIC
# MAGIC その価値を理解するために、「MLflowなし」のシナリオを考えてみましょう：開発者は複雑なチェーンをデバッグするために、散在するprint()文や基本的なログに頼ることがよくあります。このアプローチは、特定のクエリが失敗した *理由* を理解する必要がある場合に失敗します。それはVector Searchでのタイムアウト、埋め込みモデルへの不正なクエリ、それとも推論エラーだったのでしょうか？構造化された追跡システムなしに、これらの中間的な失敗を特定の設定変更と関連付けることはほぼ不可能になります。
# MAGIC
# MAGIC **MLflowを使用すると**、検索パラメータから最終生成まで、エージェントの動作のすべての側面が体系的に記録されます。これにより、「どの正確な設定がこの高品質な応答を生み出したか？」という質問に確実に答えることができます。
# MAGIC
# MAGIC ### A1. MLflowのコンポーネント
# MAGIC
# MAGIC 特定のworkflowsに入る前に、プラットフォームのアーキテクチャの柱を理解することが重要です。MLflowは単一のツールではなく、エージェントライフサイクルの異なる段階を処理する統合されたコンポーネントのスイートです。最初のコード行から最終的な本番ガバナンスまでを扱います。
# MAGIC
# MAGIC * **MLflow tracking：** パラメータ、コードバージョン、メトリクス、出力ファイルをログするためのAPIとUI。検索エージェントの場合、これにはシステムプロンプトと検索設定の追跡が含まれます。  
# MAGIC * **MLflow tracing：** エージェントの階層的な実行フローをキャプチャする専用の観測性機能で、特定の検索ツール呼び出しのデバッグに不可欠です。  
# MAGIC * **MLflow models：** 構築に使用されたライブラリに関係なく、さまざまな下流ツール（リアルタイムサービングなど）で使用できるモデルをパッケージ化するための標準形式。  
# MAGIC * **MLflow Model Registry：** モデルライフサイクル管理、バージョン管理、ステージ遷移（ステージングから本番など）で協力するための一元化されたリポジトリ。
# MAGIC
# MAGIC ### A2. エクスペリメントと実行
# MAGIC
# MAGIC コンポーネントを理解したら、開発サイクルの最初のステップは反復を整理することです。検索エージェントをテストする際、20種類の異なるシステムプロンプトやチャンク戦略を試すかもしれませんが、構造なしではこれは急速に混沌となります。
# MAGIC
# MAGIC **エクスペリメント** は、「顧客サポート検索エージェント」などの特定のプロジェクトの主要な論理コンテナとして機能します。エクスペリメント内で、個々の **実行** は特定の時点でのエージェントの特定の状態をキャプチャします。MLflowは、すべての実行について **推論エンジンの設定** をログすることで、再現性の問題を解決します：
# MAGIC
# MAGIC * **System Prompts：** エージェントのペルソナを定義する特定の指示（例：「あなたは検索されたコンテキストのみに基づいて回答する親切なアシスタントです」）。  
# MAGIC * **Model Configuration：** 温度や `max_tokens` などのパラメータ。 
# MAGIC * **Retriever Settings：** 検索するチャンクの数（k）やVector類似度のフィルタリング閾値などの重要なパラメータ。
# MAGIC
# MAGIC 開発者は`mlflow.set_experiment()`を使用して、これらの実行が保存されるワークスペースの場所を定義し、検索ロジックの反復を整理します。
# MAGIC
# MAGIC ### A3. モデルフレーバーとラッパー
# MAGIC
# MAGIC エクスペリメントをログし、勝利設定を見つけた後、そのエージェントをデプロイメント用にパッケージ化する方法が必要です。Pythonスクリプトを単純に保存し、依存関係、環境、特定のロードロジックなしに本番で動作することを期待することはできません。
# MAGIC
# MAGIC **Model Flavor** は、ユーザーが手動でこれらの依存関係を処理する必要なく、MLflowがモデルを保存、ロード、サービングできるようにする統合です。
# MAGIC
# MAGIC * **Native GenAI Flavors：** MLflowには、**LangChain**（mlflow.langchain）や **OpenAI** などのライブラリのネイティブサポートが含まれています。これらのフレーバーは、検索チェーンとそのコンポーネントのシリアル化を自動的に処理します。  
# MAGIC * **PyFunc Flavor：** 本番グレードの検索エージェントでは、特定の再ランキングステップや動的フィルター適用など、ネイティブフレーバーではカバーできないカスタムロジックが必要になることがよくあります。Python関数（PyFunc）フレーバーを使用すると、predict()メソッドを公開する限り、任意のPythonコードをモデルとしてラップできます。
# MAGIC
# MAGIC **注意：** 検索エージェントにPyFuncを使用する場合、カスタム検索コードと必要な設定ファイルがログされたアーティファクトに含まれていることを確認してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 観測性とトレーシング
# MAGIC
# MAGIC パッケージ化されたエージェントができたところで、新しい課題に直面します：**なぜそのように動作するのかを理解すること** です。従来のモデルとは異なり、精度を単純にチェックするだけで済みますが、検索エージェントはユーザー、Vectorデータベース、LLM間の相互作用の「ブラックボックス」であり、標準的なデバッグ方法を効果的でなくします。
# MAGIC
# MAGIC ### B1. トレーシングの必要性
# MAGIC
# MAGIC ユーザーが「リモートワークのポリシーは何ですか？」と尋ね、エージェントが「わかりません」と答えた場合、単純なテキストログでは理由がわかりません。検索ツールがドキュメントを見つけられなかったのでしょうか？検索が遅くてタイムアウトしたのでしょうか？それともLLMが検索されたコンテキストを無視したのでしょうか？**MLflow tracing** は、チェーン内のすべてのステップの入力と出力を記録することで、この実行グラフへの高精度な可視性を提供します。
# MAGIC
# MAGIC ### B2. トレースとスパン
# MAGIC
# MAGIC <!-- <img src="../Includes/images/04-mlflow-tracing-ui.png" alt="MLflow tracing UI" /> -->
# MAGIC ![04-mlflow-tracing-ui](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/04-mlflow-tracing-ui.png)
# MAGIC
# MAGIC *図1. この図はMLflowのトレーシングUIを示しています。* 
# MAGIC
# MAGIC MLflowトレーシングは、**traces** と **spans** を使用して実行フローを視覚化します。
# MAGIC
# MAGIC * **trace：** ユーザーの最初の質問から最終的な回答まで、リクエストのライフサイクル全体を表します。  
# MAGIC * **span：** 個々の作業単位を表します。検索エージェントでは、通常「query_embedding」、「retrieval_tool」、「context_generation」の特定のスパンが表示されます。
# MAGIC
# MAGIC トレーシングは、サポートされているライブラリ（例：`mlflow.langchain.autolog()`）の **auto-logging** または、カスタム検索関数用の `@mlflow.trace` デコレータを使用した **Manual Instrumentation** によって有効にできます。
# MAGIC
# MAGIC ### B3. 検索失敗の診断
# MAGIC
# MAGIC トレーシングの主要な価値は、検索ツールの特定の失敗モードをデバッグすることにあります。トレーシングにより、開発者は標準ログでは見えない問題を特定できます：
# MAGIC
# MAGIC 1. **空または無関係な検索：** **Retriever Span** の出力を検査することで、Vectorデータベースから返されたチャンクを正確に確認できます。スパン出力が空であるか、良いクエリにもかかわらず無関係なテキストが含まれている場合、問題は埋め込みモデルまたはチャンク戦略にあり、LLMではないことがわかります。  
# MAGIC 2. **Vector Searchのレイテンシ：** スパンは **Latency**（持続時間）をキャプチャします。エージェントが遅い場合、トレースウォーターフォールは`vector_search` スパンが4秒かかったのに対し、LLM生成は500msしかかからなかったことを明らかにするかもしれません。これにより、最適化の努力をモデルではなくデータベースクエリに向けることができます。  
# MAGIC 3. **コンテキストがあるにもかかわらずの幻覚：** トレースが検索スパンが正しいドキュメントを返したが、LLMスパン出力がそれを無視していることを示している場合、推論の失敗を特定したことになります。これは、提供されたコンテキストへの厳密な遵守を強制するためにシステムプロンプトを改良する必要があることを示しています。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. Unity Catalogによるガバナンス
# MAGIC
# MAGIC 機能し、デバッグされたエージェントができたところで、最終的なハードルに直面します：本番ガバナンスです。開発者が検証なしに本番エンドポイントに直接コードをプッシュすることを許可することはできませんし、基盤となるデータへの無統制なアクセスを許可することもできません。これにより、堅牢なレジストリシステムが必須となります。
# MAGIC
# MAGIC ### C1. Unity Catalogモデルレジストリ
# MAGIC
# MAGIC エンタープライズ環境にデプロイされるエージェントには、厳格なガバナンスと監視が必要です。**Unity Catalog（UC）** は、これらのアセットの一元化されたレジストリとして機能します。従来のワークスペースモデルレジストリとは異なり、UCはデータとAIアセット全体でアクセス制御を統合する3レベルの名前空間（`catalog.schema.model`）を提供します。
# MAGIC
# MAGIC * **access control：** 基盤となるVector Searchテーブルと同様に、登録されたエージェントに対する権限（`SELECT`、`EXECUTE`）を管理できます。  
# MAGIC * **Lineage：** UCは、エージェントによって使用されたデータテーブル（Vector Searchインデックス経由）を追跡し、生ドキュメントからデプロイされたエージェントまでのエンドツーエンドのリネージを提供します。
# MAGIC
# MAGIC ### C2. エージェントのロギングと登録
# MAGIC
# MAGIC エージェントをガバナンスするワークフローには、特定のシグネチャでモデルをログし、その後登録することが含まれます。
# MAGIC
# MAGIC 1. **モデルシグネチャの定義：** エージェントは通常、文字列入力またはチャット履歴のリストを受け入れます。サービングendpointがリクエストを正しく検証できるように、`mlflow.models.ModelSignature`を使用してこの入出力スキーマを定義する必要があります。  
# MAGIC 2. **モデルのログ：** `mlflow.langchain.log_model`（または適切なフレーバー）を使用します。UIが機能するテストウィジェットを生成できるように、**入力例** を含めることがベストプラクティスです。  
# MAGIC 3. **登録：** エクスペリメントにログされたら、モデルバージョンは以下を使用してUnity Catalogに登録されます：  
# MAGIC    `mlflow.register_model("runs:/<run_id>/model", "catalog.schema.retrieval_agent")`
# MAGIC
# MAGIC **注意：** **Retrieval tool** 自体（Unity Catalog関数として定義されている場合）も、一貫したセキュリティ境界を維持するために、同じカタログ構造内でガバナンスされるべきです。
# MAGIC
# MAGIC
# MAGIC <!-- <img src="../Includes/images/04-model-registery.png" alt="Model Registery in UC" /> -->
# MAGIC ![04-model-registery](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/04-model-registery.png)
# MAGIC
# MAGIC *図2. この図はUCモデルレジストリインターフェースを示しています。* 
# MAGIC
# MAGIC
# MAGIC *参考：* [Unity Catalogでのモデル管理ドキュメント](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle)

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. まとめ
# MAGIC
# MAGIC このレッスンでは、検索中心のworkflowsに対するMLflowの適応について概説しました。**MLflowのコンポーネント** の中核と、**エクスペリメント** が検索とプロンプトの特定の設定をどのようにキャプチャするかを定義しました。検索失敗（検索結果の悪化）と推論失敗（幻覚など）を区別するための重要なツールとして**MLflow tracing** を探求しました。最後に、これらのエージェントのバージョン管理のための統制されたレジストリを提供する **Unity Catalog** の役割について説明しました。
# MAGIC
# MAGIC **重要なポイント：**
# MAGIC
# MAGIC 1. **検索にはトレーシングが不可欠：** 中間検索スパン出力を見ることなく、エージェントがなぜ「わかりません」と言ったのかを効果的にデバッグすることはできません。  
# MAGIC 2. **カスタムロジックのためのPyFunc：** 複雑な検索戦略では、カスタム再ランキングやフィルタリングロジックをカプセル化するためにpyfuncラッパーが必要になることがよくあります。  
# MAGIC 3. **Unity Catalogによるガバナンス：** エージェントは、ソースドキュメントへのリネージと安全なアクセス制御を確保するために、Unity Catalog（catalog.schema.model）に登録されるべきです。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>