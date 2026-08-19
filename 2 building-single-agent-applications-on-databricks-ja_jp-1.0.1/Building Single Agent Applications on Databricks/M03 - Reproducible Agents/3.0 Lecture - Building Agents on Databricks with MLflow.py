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
# MAGIC # 講義 - DatabricksでMLflowを使ったエージェント構築
# MAGIC
# MAGIC MLflowは、エンドツーエンドのトラッキング、観測可能性、評価により、GenAIアプリケーションを強化し、すべてを統合されたプラットフォーム内で実現します。したがって、開発、評価、デプロイメント、本番運用監視まで、AIエージェントのライフサイクル全体をサポートします。この講義では、MLflowの包括的な機能が、初期プロトタイピングから本番運用デプロイメント、継続的な観測可能性まで、エージェント開発ライフサイクルにおいて不可欠なコンポーネントとなる理由を探ります。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC _この講義の終了時に、以下のことができるようになります：_
# MAGIC
# MAGIC - MLflowの実験トラッキング機能が反復的なエージェント開発をどのようにサポートするかを説明する
# MAGIC - MLflowのトレーシングとタグ付けが包括的なエージェント観測可能性を提供する役割を説明する
# MAGIC - MLflowのモデルレジストリが再現可能で統制されたエージェントデプロイメントをどのように可能にするかを特定する
# MAGIC - エンタープライズエージェント管理におけるMLflowとUnity Catalogの統合の利点を分析する
# MAGIC
# MAGIC > この講義は、エージェント向けの基本的なMLflowコンセプトの紹介として位置づけられています。これはMLflowのすべてのコンポーネントの包括的な説明を意図したものではありません。この講義は[Databricks マネージド MLflow](https://www.databricks.com/product/managed-mlflow)に焦点を当てています。OSS MLflowのドキュメントについては、[こちら](https://mlflow.org/)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. エージェント開発の課題
# MAGIC
# MAGIC 本番運用対応のAIエージェントの構築は、従来の機械学習workflowsでは完全に対処できない独特の課題を提示します。これらの課題を理解することで、DatabricksのMLflowがエージェントライフサイクル全体のための包括的なプラットフォームにDatabricksを変えた理由を理解できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. エージェントシステムの複雑性
# MAGIC
# MAGIC AIエージェントは、いくつかの重要な点で従来のMLモデルとは根本的に異なります：
# MAGIC
# MAGIC - **Multi-step reasoning**： エージェントは、複数のステップにわたって計画、ツール使用、意思決定を含む複雑な多ターンインタラクションを実行します
# MAGIC - **Dynamic behavior**： 静的なモデルとは異なり、エージェントはコンテキスト、利用可能なツール、会話履歴に基づいて異なる動作を示すことができます
# MAGIC - **Tool integration**： エージェントはタスクを達成するために、外部システム、API、データソースとシームレスに統合する必要があります
# MAGIC - **Conversational context**： 多ターン会話にわたって状態とコンテキストを維持することで、デプロイメントと監視に複雑性が追加されます
# MAGIC
# MAGIC これらの特徴により、従来のMLプラットフォームが元々処理するように設計されていなかった開発、テスト、本番運用監視の独特な要件が生まれます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 観測可能性の要件
# MAGIC
# MAGIC エージェントの観測可能性は、従来のモデル監視をはるかに超えます：
# MAGIC
# MAGIC - **Execution tracing**：どのツールが呼び出され、なぜ呼び出されたかを含む、段階的な推論プロセスの理解
# MAGIC - **Performance analysis**：複雑な多段階workflowsにわたるレイテンシ、トークン使用量、コストの追跡
# MAGIC - **Quality assessment**：最終出力だけでなく、中間推論ステップとツール使用パターンの評価
# MAGIC - **Error diagnosis**：多段階プロセスで障害が発生する箇所の特定と根本原因の理解
# MAGIC
# MAGIC 適切な観測可能性なしでは、特に本番運用環境でのエージェントの動作のデバッグはほぼ不可能になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. ガバナンスと再現性の課題
# MAGIC
# MAGIC エージェントのエンタープライズデプロイメントには、堅牢なガバナンス機能が必要です：
# MAGIC
# MAGIC - **Version management**：エージェントロジック、プロンプト、ツール、設定の変更の追跡
# MAGIC - **Reproducibility**：開発、ステージング、本番運用環境間での一貫した動作の確保
# MAGIC - **Access control**：異なるエージェントバージョンをデプロイ、変更、またはアクセスできる人の管理
# MAGIC - **Audit trails**：コンプライアンスとデバッグのためのエージェント動作の完全な記録の維持
# MAGIC - **AI Guardrails**：ユーザーがmodel serving endpointレベルでデータコンプライアンスを設定し、強制することを可能にします（詳細は[こちら](https://docs.databricks.com/aws/en/ai-gateway/#ai-guardrails)をお読みください）。
# MAGIC
# MAGIC これらの要件により、エンタープライズグレードのガバナンス機能を持つ完全なエージェントライフサイクルを処理できるプラットフォームが必要になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. DatabricksのMLflow
# MAGIC ここでは、前のセクションで提起された問題にMLflowがどのように対処するかを理解するために、MLflowをもう少し詳しく分析します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. なぜトレーシングが必要なのか？
# MAGIC
# MAGIC なぜトレーシングが必要なのか（そしてそれが実際に何なのか）を理解するために、従来の機械学習推論を理解する必要があります。
# MAGIC
# MAGIC ### 従来のML推論（リクエスト/レスポンス）
# MAGIC 機械学習の典型的な推論フローは、以下の高レベルステップで構成されます：
# MAGIC 1. クライアントがサービングendpointのリクエストハンドラーに入力リクエストを送信します。
# MAGIC 1. ハンドラーがリクエストをモデルに転送して推論を行います。
# MAGIC 1. モデルの出力がハンドラーを通してクライアントに返されます。
# MAGIC
# MAGIC この基本的なシナリオでは、透明なコンポーネントは多くの場合、_入力_ と _出力_ だけです。
# MAGIC
# MAGIC エージェントの時代における堅牢な運用のために、**server-side transparency**、**latency/cost metrics**、**API logging** などのプロセスへの洞察も必要になる場合があります（これらはMLワークロードには必要ない場合があります）。これらの機能は、本番運用テレメトリとガバナンスのための **Databricks Model Serving** と **AI Gateway** の標準機能です。Databricksは **managed MLflow** をホストしており、トラッキングURIを `databricks` に設定することで、組み込みのセキュリティ、信頼性、検索、UIを備えたワークスペースに **traces** をログ記録します。さらに、[**Mosaic AI Agent Framework** でのデプロイ](https://docs.databricks.com/aws/en/generative-ai/agent-framework/deploy-agent)は、リアルタイムトレーシングを自動的に統合し、レビューアプリと本番運用トラフィックの監視を有効にできます。
# MAGIC
# MAGIC ### エージェントにはより多くの洞察が必要
# MAGIC - エージェントは複数の中間ステップ（例：検索、ツール使用、LLM呼び出し）を実行し、品質をデバッグし改善するために、各ステップ、その入力/出力、ステップごとのレイテンシ/トークン使用量を確認する必要があります。
# MAGIC - **MLflow tracing** は、これらをサポートされているライブラリ（OpenAI SDK、LangChain/LangGraph、DSPyなど）に対して **traces** と **span** として自動的にキャプチャし、開発と本番運用にわたってそれらを分析するためのUIとAPIを提供します。
# MAGIC - **tracing system** における単一の操作は **span** と呼ばれます。これは操作がいつ開始され終了したかを記録し、作業単位ごとのメタデータ、入力、出力とともに記録します。
# MAGIC > MLflowスパンは[OpenTelemetry標準](https://opentelemetry.io/docs/concepts/signals/traces/)に従っており、追加情報（トークンカウントなど）はカスタムフィールドとしてではなく、スパンのキー値属性に格納する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. エージェント向けトレーシング
# MAGIC エージェントシステムの開発における困難と、エージェントが作業単位あたりより多くの洞察を必要とする理由を理解したところで、**trace** が何かを定義する準備ができました。GenAIアプリケーションのコンテキストにおける **trace** は、DAG様の構造で配置されたスパンのコレクションであり、各スパンは単一の操作を表します。これらの単一の操作は、関数呼び出しやデータベースクエリなどです。
# MAGIC
# MAGIC 例として、3つのUCツールにアクセスできるエージェントの開発に取り組んでいるとします。また、実行時間が遅いことに気づいているが、問題が何かわからないとします。DatabricksのMLflowインターフェースは、このシナリオのトラブルシューティングに役立ちます。例えば、以下のことができます：
# MAGIC - 各推論ステップで使用された特定のFoundation Model APIを表示する。
# MAGIC - エージェントに使用されたシステムプロンプト（ある場合）を表示する。
# MAGIC - ツールが呼び出されたか、呼び出された順序、その入力/出力を特定する。
# MAGIC - 各ステップでのエージェントの推論。
# MAGIC - 最も実行に時間がかかったツールを特定するためのレイテンシ。これは例えば、最適化されたSQLクエリの構築に役立ちます。
# MAGIC - トークン使用量はスパンごとおよびトレース（集計）ごとに公開されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 階層スパン構造
# MAGIC
# MAGIC MLflowは、エージェントの実行を反映する階層スパン構造を使用してトレースデータを整理し、全体のリクエストまたはワークフローを表す単一のルートスパンから始まり、各サブステップに対してネストされた子スパンを持ちます。
# MAGIC
# MAGIC - **Parent spans**：「ユーザーリクエストの処理」などの高レベル操作
# MAGIC - **Child spans**：「検索ツールの呼び出し」や「レスポンスの生成」などの詳細なステップ
# MAGIC - **Span relationships**：実行フローを示す明確な親子関係で、アプリケーションの実行計画を模倣する必要があります。
# MAGIC - **Span types**：より良い整理のためのスパンの分類（`TOOL`、`CHAT_MODEL`、`RETRIEVER`）
# MAGIC
# MAGIC ![tracing-example.png](../Includes/images/tracing-example.png "tracing-example.png")
# MAGIC <p>
# MAGIC <em>
# MAGIC 親子スパン、関係、スパンタイプ、使用されたモデルを示すトレースの例。
# MAGIC </em>
# MAGIC </p>

# COMMAND ----------

# MAGIC %md
# MAGIC ### B4. カスタムトレーシングとタグ付け
# MAGIC
# MAGIC MLflowは、カスタムトレーシングニーズにも柔軟なAPIを提供します（これは実演で確認します）。
# MAGIC
# MAGIC - **Custom Tracing**： [`@mlflow.trace`](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/fluent-apis#decorator)デコレーターを使用すると、ほとんど追加作業なしで任意の関数をトレースされたスパンに変換できます。適用すると、軽量でありながら強力なコードのインストルメンテーション方法を提供します：
# MAGIC - MLflowは、トレースされた関数間の親子関係を **自動的に推論** し、自動トレーシング統合との完全な互換性を確保します。
# MAGIC - 関数内で発生した例外は **キャプチャされ、スパンイベントとしてログ記録** されます。
# MAGIC - 関数の名前、入力、出力、実行時間は、追加の設定なしで記録されます。
# MAGIC - `mlflow.openai.autolog` などの自動トレーシング機能とシームレスに動作します。
# MAGIC - 以下の引数を受け取ります：
# MAGIC - `name`：デフォルト（装飾された関数の名前）からスパン名をオーバーライドするパラメーター。
# MAGIC - `span_type`：スパンのタイプを設定するパラメーター。組み込みの[スパンタイプ](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/data-model#span-types)のいずれかまたは文字列を設定します。
# MAGIC - `attributes` パラメータを使用して、スパンにカスタム属性を追加します。
# MAGIC
# MAGIC > **Function Type Considerations**
# MAGIC `@mlflow.trace` デコレーターを使用する際の関数タイプと対応依存関係の完全なリストを表示するには、[このドキュメント](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/fluent-apis#decorator)をご覧ください。
# MAGIC
# MAGIC - **Tagging**：タグはトレースのライフサイクル全体で更新できる柔軟なキー値ペアですが、メタデータは不変でトレース作成時に一度設定されます。
# MAGIC ![tagging-example.png](../Includes/images/tagging-example.png "tagging-example.png")
# MAGIC <p>
# MAGIC <em>
# MAGIC MLflowインターフェースでタグがどのように表示されるかを示す例。
# MAGIC </em>
# MAGIC </p>
# MAGIC
# MAGIC > このコースでは、Spanオブジェクトスキーマのサブセットのみを扱います。Spanオブジェクトスキーマの詳細については、[こちら](https://mlflow.org/docs/latest/genai/concepts/span/#span-object-schema)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. エージェントガバナンスのためのUnity Catalogのモデル
# MAGIC
# MAGIC MLflowと **Unity Catalog** の統合により、エージェントを **Unity Catalog models** として登録することで、エージェントデプロイメントのエンタープライズグレードガバナンスが可能になり、他のビジネスクリティカルな資産と同じ厳密さで管理できます。
# MAGIC
# MAGIC
# MAGIC ![mlflow-with-uc-diagram.png](../Includes/images/mlflow-with-uc-diagram.png "mlflow-with-uc-diagram.png")
# MAGIC <p>
# MAGIC <em>
# MAGIC データソースとツールをUnity Catalog（または外部ツール）に登録したら、まずMLflowでエージェントをパッケージ化し、モデルのURIを使用してエージェントコードをUCに登録できます。
# MAGIC </em>
# MAGIC </p>
# MAGIC
# MAGIC
# MAGIC ### UCのモデルレジストリによる集中ガバナンス
# MAGIC
# MAGIC エージェントをUCモデルとして登録することで、エージェント資産の集中化されたクロスワークスペースカタログが提供されます：
# MAGIC - **Version management**： MLflowはエージェントコード、設定、宣言されたリソースの特定時点のスナップショットをログ記録します；各UCモデルバージョンは、参照およびデプロイできる不変のスナップショットです。
# MAGIC - **Lineage tracking**： 入力をログ記録する際（例：`mlflow.log_input` を使用）、UCはモデルと上流データセット間のリネージを表示します；リネージはfeature storeトレーニングフローでもキャプチャされます。
# MAGIC - **Access control**： きめ細かいUC権限により、モデルを作成、読み取り、変更できる人と、エージェントが依存する関数の実行、テーブルのクエリ、接続の使用、その他のリソースへのアクセスができる人を管理します。
# MAGIC - **Cross-workspace sharing**： UCのモデルは、同じmetastoreに接続されたworkspaces間で発見可能で管理可能です。
# MAGIC - **Governed tags**： タグは登録されたモデルとモデルバージョンに適用できます；統制されたタグ（パブリックプレビュー）は、一貫した分類と制御のために標準化されたキー/値と割り当て権限を強制します。ドキュメントは[こちら](https://docs.databricks.com/aws/en/database-objects/tags#supported-securable-objects)をご覧ください。
# MAGIC
# MAGIC ### 再現可能なデプロイメント
# MAGIC
# MAGIC UC + MLflowを使用することで、エージェントデプロイメントが再現可能で観測可能であることが保証されます：
# MAGIC - **Immutable versions**： 登録されたモデルバージョンは不変のスナップショットです；必要に応じてメタデータを更新できますが、コード/依存関係の変更には新しいバージョンが必要です。
# MAGIC - **Dependency capture**： MLflowは環境依存関係（例：pip/conda経由）をキャプチャして、一貫したロードとサービングを可能にします。
# MAGIC - **Managed serving**： UC登録エージェントをModel Serving endpointにデプロイし、組み込みのスケーリング、トレーシング、フィードバックと監視のためのレビューアプリを提供します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC MLflowは、初期実験から本番運用デプロイメントと監視まで、AIエージェント開発のすべての側面に対応する包括的なプラットフォームに進化しました。実験トラッキング、トレーシング、モデルレジストリ、評価機能の組み合わせにより、現代のAIエージェントの複雑性を処理するのに独特に適しています。
# MAGIC
# MAGIC Unity Catalogとより広範なDatabricksエコシステムとのプラットフォーム統合により、エンタープライズエージェントデプロイメントに必要なガバナンス、セキュリティ、スケーラビリティが提供されます。AIエージェントがビジネスアプリケーションでますます重要になるにつれて、エージェント開発の基盤プラットフォームとしてのMLflowの役割は継続的に成長するでしょう。
# MAGIC
# MAGIC ## 次のステップ
# MAGIC トレーシング、タグ付け、Unity Catalogでの再現可能なエージェント構築のためのMLflowの基本的な理解ができたので、MLflowでのトレーシングについて議論する次のデモを完了する準備が整いました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>