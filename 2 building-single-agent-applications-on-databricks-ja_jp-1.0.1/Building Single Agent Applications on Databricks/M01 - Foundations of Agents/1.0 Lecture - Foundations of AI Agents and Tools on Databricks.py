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
# MAGIC # 講義 - DatabricksにおけるAIエージェントとツールの基礎
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このレクチャーでは、Databricks platform内でのAIエージェントとツールの基本概念を紹介します。現代のAIアプリケーションには、データとやり取りし、分析タスクを実行し、利用可能な情報に基づいて情報に基づいた意思決定を行うことができるエージェントが必要です。これらの基本概念を理解することで、ガバナンス、セキュリティ、分析能力を組み合わせた堅牢でスケーラブルなAIソリューションを構築する準備が整います。
# MAGIC
# MAGIC AIエージェントは、ユーザーのプロンプトに基づいて情報を提供するだけの従来のAIシステムからの革命的な変化を表しています。代わりに、エージェントは利用可能なツールを使用して、より正確で情報に基づいた意思決定を行い、ユーザー定義の目標を達成するために環境内で自律的に行動します。
# MAGIC
# MAGIC ### 学習目標
# MAGIC
# MAGIC _このレクチャーの終了時には、以下のことができるようになります：_
# MAGIC
# MAGIC - AIエージェントとは何かを定義し、その中核となる構成要素と機能を理解する
# MAGIC - AIエージェントアーキテクチャにおけるツールの役割と、それらがエージェント機能をどのように拡張するかを説明する
# MAGIC - エージェントツールのガバナンスと管理にUnity Catalogを使用する利点を特定する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. AIエージェントの理解

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. AIエージェントとは何か？
# MAGIC
# MAGIC **AI Agent** は、環境を認識し、意思決定を行い、特定の目標を達成するために行動を取ることができるインテリジェントなソフトウェアシステムです。ユーザーからの継続的な入力を必要とする従来のAIシステムとは異なり、AIエージェントは以下のことができる自律システムです：
# MAGIC
# MAGIC - 複雑な問題や状況について **推論** する
# MAGIC - 目標を達成するための行動の順序を **計画** する
# MAGIC - 新しい情報に基づいて行動を **適応** させる
# MAGIC - 外部システムやデータソースと **相互作用** する
# MAGIC - 経験から **学習** して将来のパフォーマンスを向上させる
# MAGIC
# MAGIC AIエージェントを魅力的にするのは、その **適応性** です。エージェントは、最新のデータセットを動的に取得して意思決定やプロセスに情報を提供するツールを使用するため、複雑で予測不可能なタスクに理想的です。人間が目標を設定する一方で、AIエージェントはそれらの目標を達成する最良の方法を決定します。
# MAGIC
# MAGIC データ分析とビジネスインテリジェンスの文脈では、AIエージェントは、自然言語クエリを理解し、複雑な分析タスクを実行できる、ユーザーとデータシステム間のインテリジェントな仲介者として機能します。
# MAGIC
# MAGIC ![agent-framework.png](../Includes/images/agent-framework.png "agent-framework.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. AIエージェントの進化
# MAGIC
# MAGIC AIエージェントは、その創設以来大幅に進化してきました：
# MAGIC
# MAGIC - **1960s - Rule-Based Systems**
# MAGIC     - 事前に決められたロジックツリーを持つ基本的なチャットボット
# MAGIC     - 硬直的で、ルールベースのプログラミング
# MAGIC     - 単純で、スクリプト化された応答に限定
# MAGIC
# MAGIC - **1990s - Statistical Learning**
# MAGIC     - 情報を処理するより自律的なシステム
# MAGIC     - 単純な意思決定機能
# MAGIC     - 消費者向けAIデバイスの基盤
# MAGIC
# MAGIC - **2000s - Machine Learning Integration**
# MAGIC     - ロボット掃除機やデジタルアシスタント（Siri、Alexa）などの消費者デバイス
# MAGIC     - 統計的機械学習モデルとニューラルネットワーク
# MAGIC     - 強化された意思決定と分析機能
# MAGIC
# MAGIC - **2020s - Large Language Models**
# MAGIC     - 深層強化学習とトランスフォーマーベースの大規模言語モデル（LLM）による突破
# MAGIC     - マルチモーダルインターフェースと高度な推論
# MAGIC     - 複雑な環境との動的な相互作用
# MAGIC     - 機能強化のためのツール呼び出し機能

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. AIエージェントの主要原理
# MAGIC
# MAGIC AIエージェントは、従来のソフトウェアとは区別される3つの基本原理に基づいて動作します：
# MAGIC
# MAGIC #### **知覚**
# MAGIC エージェントが動作している文脈を理解するための最初のステップです。言語モデルにとって、これには以下が含まれます：
# MAGIC - テキスト、写真、または音声によるユーザー入力とクエリ
# MAGIC - センサーやAPIからの環境データ
# MAGIC - 履歴コンテキストと会話記憶
# MAGIC
# MAGIC #### **意思決定**
# MAGIC エージェントは、アルゴリズムを通じて収集された情報を処理し、ユーザーの目標に従って適切な行動を決定します：
# MAGIC - 要件と制約の分析
# MAGIC - 必要なステップとツールの使用の決定
# MAGIC - 最適な実行順序の計画
# MAGIC
# MAGIC #### **行動**
# MAGIC 最後に、エージェントは目標を達成するための具体的なステップを実行します：
# MAGIC - データベースクエリとAPI呼び出しの実行
# MAGIC - データの処理と変換
# MAGIC - レポートと推奨事項の生成
# MAGIC - 現実世界の結果に影響を与える意思決定

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. AIエージェントの中核構成要素
# MAGIC 現代のAIエージェントは通常、連携して動作するいくつかの主要構成要素で構成されています：
# MAGIC
# MAGIC 1. **Large Language Model (LLM) Brain**
# MAGIC 自然言語を処理し、文脈を理解し、どのような行動を取るかについて意思決定を行う中央推論エンジン。
# MAGIC 1. **Memory System**
# MAGIC 会話履歴、文脈、学習した情報を保存し、時間を通じて一貫した相互作用を維持。
# MAGIC 1. **Planning Module**
# MAGIC 複雑なリクエストをより小さく管理可能なタスクに分解し、最適な行動順序を決定。
# MAGIC 1. **Tool Interface**
# MAGIC エージェントを外部システム、データベース、API、テキスト生成を超えてその機能を拡張する関数に接続。
# MAGIC 1. **Execution Engine**
# MAGIC 計画された行動の実際の実行を管理し、外部ツールやシステムからの応答を処理。
# MAGIC
# MAGIC <p align="center">
# MAGIC <img src="../Includes/images/example-agent-framework.png" alt="a4-core-components-of-ai-agents" width="50%">
# MAGIC </p>
# MAGIC <p align="center"><em>エージェントパターンの例：LLMは、ユーザーのリクエストに基づいて環境内でタスクを計画し実行するブレインとして機能します。ツールはUnity Catalog内に安全に保存でき、エージェントメモリはDelta LakeとLakebaseで使用できます。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ### A5. 複雑さによるAIエージェントのタイプ
# MAGIC
# MAGIC AIエージェントは、その複雑さと応用によって異なります。これらのタイプを理解することは、特定のユースケースに適したアプローチを選択するのに役立ちます：
# MAGIC 1. **Simple Reflex Agents**
# MAGIC     - 現在の条件のみに基づいて意思決定を行う
# MAGIC     - 例：汚れを感知したときのみ掃除するロボット掃除機
# MAGIC     - 履歴や将来の影響を考慮しない
# MAGIC 1. **Model-Based Reflex Agents**
# MAGIC     - 現在の状態を考慮し、世界モデルを使用して行動を導く
# MAGIC     - 例：時間、天気、設定に基づいて調整するスマートサーモスタット
# MAGIC     - 単純反射エージェントよりも洗練されている
# MAGIC 1. **Goal-Based Agents**
# MAGIC     - 望ましい目標を達成するための特定の戦略を計画
# MAGIC     - 行動順序を開発し、進捗を評価
# MAGIC     - 例：交通とルートを考慮するGoogle Mapsなどのナビゲーションシステム
# MAGIC 1. **Utility-Based Agents**
# MAGIC     - 最適な効率のために目標を達成する複数の方法を評価
# MAGIC     - リスク・リワードモデルと最適化基準を考慮
# MAGIC     - 例：投資戦略を調整するAI取引ボット
# MAGIC 1. **Learning Agents**
# MAGIC     - 過去の行動から学習し、将来の状況に適応
# MAGIC     - パフォーマンスを分析し、効率の改善を求める
# MAGIC     - 例：ユーザー行動に基づいて改善する推奨システム

# COMMAND ----------

# MAGIC %md
# MAGIC ### A6. すべてのLLMがツールを使用できるか？
# MAGIC いいえ、すべてのLLMがツール呼び出し機能を持っているわけではありません。Databricksでは、LLMによるツールの使用は、Databricks AssistantやLLMが外部システム、データベース、またはAPIと相互作用できるカスタムエージェントframeworksなどの特定のframeworksと統合を通じて有効になります。この機能はすべてのLLMに固有のものではありません。安全で効果的なツールの使用を確保するために、追加のエンジニアリング、オーケストレーション、セキュリティ制御が必要です。例えば、Databricks AssistantはDatabricks環境内で質問に答えたり行動を実行したりするためにツールを使用するように設計されていますが、これはプラットフォームの機能であり、すべてのLLMの普遍的な機能ではありません。
# MAGIC
# MAGIC > ツール呼び出しを実行できるFoundation Model APIの完全なリストについては、[こちら](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling#supported-models)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. エージェントツールの理解

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. エージェントツールとは何か？
# MAGIC
# MAGIC **Agent tools** は、AIエージェントが外部システムと相互作用し、特定のタスクを実行する能力を拡張する特殊な関数や機能です。ツールをAIエージェントの「手」と考えてください。LLMが推論と意思決定のための「脳」を提供する一方で、ツールはエージェントが実際にデータを操作し、APIを呼び出し、計算を実行し、現実世界と相互作用することを可能にします。
# MAGIC
# MAGIC ツールは、エージェントを純粋に会話的なシステムから実用的で生産的なアシスタントに変換します。いくつかの例には以下が含まれます：
# MAGIC
# MAGIC - データベースクエリを実行し、特定の情報を取得する
# MAGIC - 複雑な計算と統計分析を実行する
# MAGIC - 外部APIやウェブサービスと相互作用する
# MAGIC - さまざまな形式でデータを処理・変換する
# MAGIC - レポート、可視化、要約を生成する
# MAGIC - 現在のデータに基づいてリアルタイムの意思決定を行う

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. ツールが従来のAI構成要素とどう異なるか
# MAGIC
# MAGIC エージェントツールが他のAI技術とどのように関連するかを理解することが重要です。ツールと機械学習モデル、チャットボット、従来のAPIを区別するのに役立つ例を以下に示します：
# MAGIC
# MAGIC #### **Tools vs. Machine Learning Models**
# MAGIC - **ML Models**: エージェントが使用するインテリジェンス（予測、生成、推論）を提供
# MAGIC - **Agent Tools**: エージェントが行動を取ったり情報を取得したりするために呼び出すことができる実行可能な機能 — 一部のツールはMLモデルを呼び出すかもしれませんが、他のツールはAPI、データベース、またはビジネスロジックを実行するかもしれません
# MAGIC - **Example**: 感情モデルが顧客メッセージをスコア化し、エージェントはそのスコアに基づいてツール（例：`escalate_ticket`）を使用して行動を取る
# MAGIC
# MAGIC #### **Tools vs. Chatbots**
# MAGIC - **Chatbots**: 限定された範囲内で会話応答を提供（スクリプト、検索、事前定義フロー）
# MAGIC - **Agent Tools**: エージェントが応答を超えて行動することを可能にする — エージェントは行動を実行することを決定できる（例：データベースを検索、メールを送信、レコードに書き込み）
# MAGIC - **Key Point**: チャットボットは会話する；エージェントはツールを使用して現実世界で *物事を行う*
# MAGIC
# MAGIC #### **Tools vs. Traditional APIs**
# MAGIC - **Traditional APIs**: 関数を選択し呼び出すために手動プログラミングが必要
# MAGIC - **Agent Tools**: 文脈と目標に基づいてAI推論によって動的に選択・オーケストレーションされる
# MAGIC - **Intelligence**: ツールはメタデータと説明を公開するため、エージェントは *いつ*、*どのように* それらを使用するかを理解する

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. ツールの選択とオーケストレーション
# MAGIC
# MAGIC 現代のAIエージェントの主要機能の一つは、**インテリジェントなツール選択** です。ユーザーリクエストが提示されたとき、エージェントは以下を行う必要があります：
# MAGIC
# MAGIC 1. **Analyze the Request**: ユーザーが達成しようとしていることを理解する
# MAGIC 2. **Identify Required Tools**: リクエストを満たすためにどのツールが必要かを決定する
# MAGIC 3. **Plan Execution Order**: ツールを呼び出すべき順序を決定する
# MAGIC 4. **Execute and Coordinate**: 適切なパラメータでツールを呼び出し、応答を処理する
# MAGIC 5. **Synthesize Results**: 複数のツールからの出力を一貫した応答に組み合わせる
# MAGIC 6. **Learn and Adapt**: 成功パターンに基づいてツール選択を改善する
# MAGIC
# MAGIC このオーケストレーション機能により、エージェントは複雑な多段階workflowsを自動的に処理でき、動的な問題解決アプローチを必要とするシナリオに理想的です。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. Unity Catalogとエージェントツールガバナンス
# MAGIC Databricksのツールエコシステムを理解することが重要です。これにより、どのツール使用ケースが最適かを決定できます。現在、エージェントツールを作成するための3つのオプションがあります：
# MAGIC 1. **Unity Catalog function tools**: これはこのコースの主要な焦点です。ツールはUC UDFとして定義され、エージェントのツールの中央レジストリとしてUCで管理されます。これにより、組み込みのセキュリティとコンプライアンス機能が提供され、発見可能性と再利用が容易になります。
# MAGIC 1. **Agent-code tools**: これらはエージェントのコード内で直接定義されるツールです。REST APIの呼び出し、任意のコードの実行、または低レイテンシツールの実行に最適です。ただし、このアプローチには、UCがテーブルにもたらす組み込みガバナンスと発見可能性が不足しています。
# MAGIC 1. **Model Context Protocol (MCP) tools**: これらはツールの相互運用性のためのMCP標準に従うツールです。Databricks管理のMCPサーバーが現在利用可能で、リリース状況は[こちら](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp)で確認できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. なぜエージェントツールにUnity Catalogを使用するのか？
# MAGIC エージェントを構成する基本要素の理解ができたので、まずツールが保存される場所と、Unity Catalogを介してプラットフォーム上でどのようにガバナンスされるかを見ることで、Databricksがどのようにツール呼び出しを可能にするかに注目しましょう。
# MAGIC
# MAGIC ![example-agent-framework-with-uc.png](../Includes/images/example-agent-framework-with-uc.png "example-agent-framework-with-uc.png")
# MAGIC
# MAGIC <p align="center"><em>従来のツール呼び出しには包括的なガバナンスが不足しています。Unity Catalogを使用することで、ユーザーは構造化および非構造化データを取得するためのツールを構築し、AI Playgroundでそれらのツールをテストできます。Unity Catalog接続を介して外部ツール（Slack、Google Calendar、またはAPIサービスなど）を接続する際、認証情報と認証の管理はUnity Catalogポリシーによってガバナンスされます。これにより、安全で監査可能なアクセスを確保し、外部サービスとの統合に組織全体のガバナンスを適用できます</em></p>
# MAGIC
# MAGIC **Unity Catalog** は、エンタープライズグレードの機能を備えたエージェントツール管理の基盤を提供します：
# MAGIC
# MAGIC 1. **Centralized Governance**
# MAGIC     - すべてのUC対応workspacesにわたって、関数を含むデータとAI資産の統一オブジェクトモデルと3レベル名前空間。
# MAGIC     - アクセスと分析を簡素化するシステムテーブルによる組み込み監査とリネージ。
# MAGIC     - 'Catalog Explorer' と 'Search' による一貫したメタデータと発見可能性。
# MAGIC     - ガバナンスされたツール：UCに登録された関数はエージェントツールとして使用でき、再利用と制御を可能にします。
# MAGIC 1. **Security and Access Control**
# MAGIC     - 関数/ツールでのEXECUTEを含むきめ細かい権限（ANSI GRANT）。
# MAGIC     - workspaces間で一貫したアクセスのための集中アイデンティティ統合（SCIM、アカウントレベルアイデンティティ）。
# MAGIC     - Python UDFの安全で分離された実行；外部接続と場所への管理されたアクセス。
# MAGIC         - Python UDFにはUnity Catalogと、サーバーレス/プロ SQL warehouse、またはUC対応クラスターが必要です。
# MAGIC     - カタログ → スキーマ → オブジェクト（テーブル、ビュー、ボリューム、モデル、関数）に整合した役割ベースの階層権限。
# MAGIC 1. **Discoverability and Documentation**
# MAGIC     - リッチメタデータ（関数とパラメータのコメント）、リネージ、ブラウズ機能を持つ検索可能なカタログ。
# MAGIC     - ツール呼び出しを支援するための関数の推奨docstring（目的、パラメータ、戻り値、例、変更ログ）。
# MAGIC     - ガバナンスされた資産の発見を加速するAI駆動ドキュメントのプラットフォームサポート。
# MAGIC 1. **Scalability and Performance**
# MAGIC     - UC管理ツールはDatabricksコンピュートを介して実行；エージェントツール実行はサーバーレス汎用コンピュート（Spark Connectサーバーレス）を使用します。一部の統合はSQL warehouse（uc_function）を介してUC関数を実行できます。
# MAGIC     - SQL warehouseでのスケーリングと同時実行制御；ワークロード需要に合わせたクラスターでのオートスケーリング。
# MAGIC 1. **External Tool Support**
# MAGIC     - Unity Catalog接続を介して[外部ツール](https://docs.databricks.com/aws/en/generative-ai/agent-framework/external-connection-tools)（Slack、Google Calendar、またはAPIサービスなど）を接続する際、認証情報と認証の管理はUnity Catalogポリシーによってガバナンスされます。これにより、安全で監査可能なアクセスを確保し、外部サービスとの統合に組織全体のガバナンスを適用できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. ツールの登録と管理
# MAGIC
# MAGIC Unity CatalogはSQLベースのエージェントツールを登録・管理するための複数のアプローチを提供します。エージェントでのツール使用をトレースするために、Databricksは自動シグネチャとトレース、レスポンソエージェントインターフェースなどの管理されたMLflowエージェントツール機能を活用します。このコースでは、ツールロジックをシンプルで直接的に保つことでツール呼び出しの基礎に集中します（例：エージェントの[Vector search](https://www.databricks.com/product/machine-learning/vector-search)を実行する能力には深く入りません）。これにより、エージェント開発にDatabrick platformを使用する方法に焦点を当てることができます。
# MAGIC
# MAGIC #### **SQL-Based Registration**
# MAGIC LLMで使用できる包括的なメタデータを持つ `CREATE OR REPLACE FUNCTION` 文の使用：
# MAGIC - 型と説明を持つ明確なパラメータ定義
# MAGIC - 関数レベルのドキュメントと使用ガイダンス
# MAGIC - 決定論的動作仕様
# MAGIC - 組み込みバリデーションとエラーハンドリング
# MAGIC
# MAGIC #### **Programmatic Registration**
# MAGIC 自動化されたツール管理のための `DatabricksFunctionClient()` の使用：
# MAGIC - プログラマティックな作成と更新
# MAGIC - CI/CDパイプラインとの統合
# MAGIC - バッチ操作と一括管理
# MAGIC - 自動化されたテストとバリデーションworkflows
# MAGIC
# MAGIC #### **ドキュメントのベストプラクティス**
# MAGIC SQL関数には、AIエージェントがその目的を理解するのに役立つリッチメタデータを含める必要があります：
# MAGIC - ビジネスロジックを説明する包括的な関数コメント
# MAGIC - 期待されるデータ型と範囲を持つパラメータ説明
# MAGIC - 戻り値の仕様と出力例
# MAGIC - 使用例と一般的なパターン
# MAGIC - [適切な場合](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-sql-function#parameters)に関数を`DETERMINISTIC` とマークする
# MAGIC
# MAGIC 両方のアプローチにより、SQL関数がガバナンスとセキュリティ標準を維持しながら、適切にドキュメント化、バージョン管理され、AIエージェントにアクセス可能であることが保証されます。
# MAGIC
# MAGIC
# MAGIC MLflowは、特にエージェントツールを扱う際に、堅牢なトレース、バージョン管理、評価、本番デプロイメントを提供し、Databricksでエージェントベースアプリケーションを構築、監視、デプロイするための基盤となります
# MAGIC ![example-agent-framework-with-sql-function.png](../Includes/images/example-agent-framework-with-sql-function.png "example-agent-framework-with-sql-function.png")
# MAGIC
# MAGIC
# MAGIC <p align="center"><em>エージェントframeworkとUC SQL関数の基本構造の例。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. その他のツールと一般的なパターン
# MAGIC このコースで議論されたもの以外にも、UCのエージェントツールに焦点を当てますが、他にも存在するツールがあることを指摘することが重要です。
# MAGIC
# MAGIC #### Model Context Protocol（MCP）
# MAGIC MCPの主な利点は標準化です。一度ツールを作成すれば、構築したエージェントでも第三者のエージェントでも、どのエージェントでも使用できます。同様に、チームや組織外の他の人が開発したツールも使用できます。
# MAGIC > DatabricksでのMCPについては[こちら](https://docs.databricks.com/aws/en/generative-ai/mcp/)をご覧ください。公式MCPドキュメントは[こちら](https://modelcontextprotocol.io/docs/getting-started/intro)でも読むことができます。
# MAGIC #### Mosaic AI Vector Search
# MAGIC Mosaic AI Vector Searchは、Databricks Data Intelligence Platformに組み込まれ、そのガバナンスと生産性ツールと統合されたVector searchソリューションです。ベクトル検索は、埋め込みの取得に最適化された検索の一種です。
# MAGIC > Vector searchについては[こちら](https://docs.databricks.com/aws/en/vector-search/vector-search)をご覧ください。
# MAGIC #### 一般的なツールパターン
# MAGIC 以下は、今日Databricksに存在するいくつかの一般的なツールパターンと、読み物への追加リンクの要約です。
# MAGIC | ツールパターン| 説明|
# MAGIC |-------------|------------|
# MAGIC | **[構造化データ取得ツール](https://docs.databricks.com/aws/en/generative-ai/agent-framework/structured-retrieval-tools)** | SQLテーブル、データベース、構造化データソースをクエリします。                                   |
# MAGIC | **[非構造化データ取得ツール](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unstructured-retrieval-tools)** | ドキュメントコレクションを検索し、検索拡張生成を実行します。                    |
# MAGIC | **[コードインタープリターツール](https://docs.databricks.com/aws/en/generative-ai/agent-framework/code-interpreter-tools)**         | エージェントが計算、データ分析、動的処理のためにPythonコードを実行できるようにします。   |
# MAGIC | **[外部接続ツール](https://docs.databricks.com/aws/en/generative-ai/agent-framework/external-connection-tools)**      | SlackなどのAPIサービスに接続します。                                        |
# MAGIC | **[AI Playgroundプロトタイピング](https://docs.databricks.com/aws/en/generative-ai/agent-framework/ai-playground-agent)**      | AI PlaygroundでUnity Catalogツールをエージェントに素早く追加し、動作をプロトタイプします。 |
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC これで、DatabricksにおけるAIエージェントとUC関数ツールの基礎となる概念と原理について包括的な基盤を得ました。このレクチャーでは、単純なルールベースシステムから、世界中の産業を変革している今日の洗練されたツール対応システムまでのAIエージェントの進化を取り上げました。
# MAGIC
# MAGIC このレクチャーの主要な要点は以下の通りです：
# MAGIC
# MAGIC - **AI agents** は、知覚、意思決定、行動機能を組み合わせて複雑な問題を解決する自律システムです
# MAGIC - **Agent tools** は、外部システム、データソース、特殊関数へのインターフェースを提供することでAI機能を拡張します
# MAGIC - **Unity Catalog** は、エンタープライズグレードのエージェントツールデプロイメントに必要なガバナンス、セキュリティ、管理frameworkを提供します
# MAGIC
# MAGIC エージェントとは何か、そしてツールがエージェント動作の中核構成要素であることを理解したので、DatabricksのUCツールについてもう少し深く掘り下げてみましょう。
# MAGIC
# MAGIC ## 次のステップ
# MAGIC - SQL関数を構築し、AI Playgroundでテストするための次のデモンストレーションに進んでください。
# MAGIC - エージェントに関するより多くのトレーニングについては、[Databricksコースカタログ](https://www.databricks.com/training/catalog?search=agent)の他のコース提供をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>