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
# MAGIC # 講義 - Agent Bricksを使ったシングルエージェント
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC Agent Bricksは、技術ユーザーがプロダクション対応のドメイン特化型AIエージェントを迅速に構築・最適化できるよう設計された高レベルの抽象化を提供します。自動評価・最適化、Agent Learning on Human Feedback (ALHF)を含む機能により、コスト配慮とのバランスを取りながら品質を最大化することに焦点を当てています。
# MAGIC
# MAGIC 広範な手動設定と最適化を必要とする従来のエージェント開発アプローチとは異なり、**Agent Bricksは実装プロセスを合理化** し、ユーザーが低レベルの技術的詳細ではなく、問題、データ、メトリクスに集中できるようにします。このプラットフォームは、特定のユースケースとデプロイメントパターンに最適化された4つの異なるエージェントタイプをサポートしています。
# MAGIC
# MAGIC ## 学習目標
# MAGIC _この講義の終了時には、以下のことができるようになります：_
# MAGIC
# MAGIC - Agent Bricksの開発ライフサイクルと反復的最適化プロセスを理解する
# MAGIC - 4つのサポートされているエージェントタイプとその特定のユースケースを識別する
# MAGIC - 自動化エージェントとインタラクティブエージェントカテゴリの違いを説明する
# MAGIC - コストパフォーマンスバランスの最適化戦略を説明する
# MAGIC - Agent Bricksに組み込まれた評価・監視機能を認識する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. Agent Bricksの紹介
# MAGIC
# MAGIC ![agent-bricks-cost.png](../Includes/images/agent-bricks-cost.png "agent-bricks-cost.png")
# MAGIC
# MAGIC Agent Bricksは、ドメイン特化型エージェントシステムを構築するためのシンプルで強力なアプローチを提供します。このプラットフォームは、エンタープライズアプリケーションに必要な柔軟性を維持しながら、従来エージェント開発に関連していた複雑さの多くを抽象化します。
# MAGIC
# MAGIC Agent Bricksの核となる理念は、ユーザーがビジネス問題の定義と関連データの提供に集中できるようにし、プラットフォームがエージェントの最適化、評価、デプロイメントの技術的複雑さを処理することです。このアプローチにより、エンタープライズ環境でのAIエージェント実装の価値創出までの時間が大幅に短縮されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. サポートされているエージェントタイプとユースケース
# MAGIC
# MAGIC Agent Bricksは、特定のエンタープライズユースケースと運用パターン向けに設計された4つの主要エージェントタイプをサポートしています。これらの違いを理解することは、特定の要件に適したエージェントタイプを選択する上で重要です。
# MAGIC
# MAGIC **4つのエージェントタイプ：**
# MAGIC
# MAGIC 1. **Information Extraction (IE)** ：ドキュメント、PDF、電子メール、画像などの非構造化ソースから構造化データを自動抽出
# MAGIC 2. **Custom LLM (CLLM)** ：特定のタスクとデータセットに対してファインチューニングされ最適化されたドメイン特化型言語モデル
# MAGIC 3. **Knowledge Assistant (KA)** ：検索拡張生成を使用してナレッジベースに対する質問応答機能を提供するインタラクティブエージェント。つまり、KAはツール呼び出し機能がRAGアプリケーションに制限されたシングルエージェントです。
# MAGIC 4. **Multi-Agent Supervisor (MAS)** ：複雑な多段階タスクを完了するために複数の専門エージェントを管理・調整する協調システム。例えば、MASにツールセットを装備し、追加エージェントなしで、ツールキット付きのシングルエージェントとして動作させることができます。
# MAGIC
# MAGIC ### Genieエージェント
# MAGIC ユーザーはGenieエージェントを作成・使用して、自然言語でデータベースや他の構造化データをクエリし、データ分析をよりアクセシブルにできます。GenieエージェントはMASで調整することも、スタンドアロンのシングルエージェントとしても使用できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 運用カテゴリ
# MAGIC
# MAGIC
# MAGIC ![automated-interactive-agents.png](../Includes/images/automated-interactive-agents.png "automated-interactive-agents.png")
# MAGIC
# MAGIC エージェントは、意図された使用パターンに基づいて2つの運用モデルに分類されます：
# MAGIC
# MAGIC - **Automated Bricks**（情報抽出とカスタムLLM）：人間の介入を最小限に抑えた大規模バッチ処理シナリオに最適化されています。これらのエージェントはコストパフォーマンス最適化とスループットを優先します。
# MAGIC
# MAGIC - **Interactive Bricks**（ナレッジアシスタント、マルチエージェント・スーパーバイザー、Genie）：人間参加型の体験とリアルタイムインタラクションシナリオ向けに設計されています。これらのエージェントは会話インターフェースと動的応答生成に焦点を当てています。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. Agent Bricks開発ライフサイクル
# MAGIC
# MAGIC Agent Bricks開発プロセスは、継続的改善とフィードバック取り込みを通じてエージェントパフォーマンスを最適化するよう設計された構造化された反復的アプローチに従います。このライフサイクルにより、エージェントが初期要件を満たすだけでなく、実際の使用とフィードバックを通じて継続的に改善されることが保証されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 核となる3ステップ開発サイクル
# MAGIC
# MAGIC
# MAGIC
# MAGIC Agent Bricks開発ライフサイクルは、エージェント開発の基盤を形成する3つの主要フェーズで構成され、その後継続的な改善のための継続的反復が続きます。
# MAGIC
# MAGIC **Step 1: Specify Your Problem**
# MAGIC ![agent-bricks-high-level-architecture.png](../Includes/images/agent-bricks-high-level-architecture.png "agent-bricks-high-level-architecture.png")
# MAGIC
# MAGIC 高レベルでは、ユーザーは自分のユースケースに特化したエージェントの構築から始めます。例えば、MASでは、Genieエージェントでのツール呼び出しのみを許可するマネージドエージェントが必要かもしれません。適切な権限を設定した後、メトリクスの追跡とログ記録にMLflowが活用されます。
# MAGIC
# MAGIC この初期フェーズでは、AIエージェントの範囲と要件を定義します：
# MAGIC - チームと必要なタスクと期待される成果を明確に定義する
# MAGIC - 利用可能な4つのオプションから適切なエージェントタイプを選択する：情報抽出、カスタムLLM、ナレッジアシスタント、またはマルチエージェント・スーパーバイザー
# MAGIC - ユースケースに応じて、UC管理データセット（Deltaテーブル、UCボリューム）の提供、ツールの装備、他のエージェントの接続が必要
# MAGIC - 評価のための成功基準と品質メトリクスを確立する
# MAGIC
# MAGIC **Step 2: Optimize on Your Enterprise Data**
# MAGIC
# MAGIC Agent Bricksは品質対コストのトレードオフに基づいて最適なエージェントシステムを自動的に構築・最適化します：
# MAGIC - システムは特定のタスクに関連する評価ベンチマークを自動的に作成します（精度、製品関連性、顧客離反予測など）
# MAGIC - 最適化には複数の技術の知的選択と構成が含まれます：
# MAGIC   - 実証済み手法を使用した高度なプロンプト最適化
# MAGIC   - タスク要件とデータ可用性に基づく選択的ファインチューニング
# MAGIC   - 最適なツール選択と設定
# MAGIC   - 品質評価のためのカスタムLLMジャッジの実装
# MAGIC   - 応答品質向上のための報酬モデルフィルタリング
# MAGIC   - Reinforcement Learning from Human Feedback（RLHF）が有益な場合
# MAGIC
# MAGIC
# MAGIC ![setup-architecture-1.png](../Includes/images/setup-architecture-1.png "setup-architecture-1.png")
# MAGIC
# MAGIC
# MAGIC **Step 3: Continuous Improvement**
# MAGIC
# MAGIC 最終ステップでは、継続的最適化のためのフィードバックループを確立します：
# MAGIC - 最適化されたエージェントをプロダクション環境にデプロイ
# MAGIC - 自動化と人間による評価を通じてエージェント品質を継続的に測定
# MAGIC - 監視を通じて問題と改善機会を体系的に特定
# MAGIC - 自然言語フィードバックを適用してシステムパフォーマンスを向上
# MAGIC - 反復的向上のためのAgent Learning on Human Feedback（ALHF）を活用

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 評価・監視framework
# MAGIC
# MAGIC Agent Bricksは、プラットフォームに直接組み込まれた包括的な評価・監視機能を提供し、エージェントパフォーマンスと品質メトリクスの継続的な可視性を保証します。
# MAGIC
# MAGIC **Automatic MLflow Integration:**
# MAGIC
# MAGIC Agent Bricksを通じてデプロイされたすべてのエージェントには、包括的な追跡機能が自動的に含まれます：
# MAGIC - **Request Tracking**：タイムスタンプとユーザーコンテキストを含むすべての受信リクエストの完全ログ記録
# MAGIC - **Response Monitoring**：信頼度スコアと推論パスを含む送信レスポンスの詳細キャプチャ
# MAGIC - **Inter-Agent Communication**：マルチエージェントシステムにおけるエージェント間通信の完全トレース
# MAGIC - **Performance Metrics**：レイテンシ、スループット、リソース使用率データの自動収集
# MAGIC
# MAGIC **Quality Assessment Mechanisms:**
# MAGIC
# MAGIC プラットフォームは複数層の品質評価を実装します：
# MAGIC - **Automatic Benchmark Creation**：ユースケース要件に合わせたタスク特化型メトリクス
# MAGIC - **LLM Judge Evaluation**：評価タスク用に訓練された専門言語モデルを使用した自動品質スコアリング
# MAGIC - **Human Feedback Integration**：レビューアプリケーションを通じた専門家フィードバックの構造化収集と統合
# MAGIC - **Production Performance Monitoring**：ライブ環境でのエージェントパフォーマンスのリアルタイム追跡
# MAGIC - **Comparative Analysis**：ベースラインモデルと以前のエージェントバージョンに対するベンチマーク

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 他のサービスとの統合
# MAGIC ![agent-bricks-integration.png](../Includes/images/agent-bricks-integration.png "agent-bricks-integration.png")
# MAGIC
# MAGIC Agent BricksはMosaic AI Model Serving、Vector Search、Unity Catalog、Genie、MLflow 3、Databricks Appsと密接に統合されており、**AIエージェントをエンドツーエンドで構築、ガバナンス、評価、デプロイするための統合プラットフォーム** を作成しています。この統合により、ユーザーは自社のエンタープライズデータを使用してエージェントシステムを迅速にプロトタイプ、反復、デプロイでき、同時に最高クラスのガバナンス、セキュリティ、スケーラビリティを維持できます。
# MAGIC
# MAGIC #### Agent BricksがDatabricksスタックと連携する方法
# MAGIC
# MAGIC - **Mosaic AI Model Serving**：エージェントは自動負荷分散と監視を備えたスケーラブルなREST APIとしてデプロイできます。このサービングプラットフォームは安全な認証も提供し、MLflow 3とネイティブに統合して、リアルタイムトレースと品質評価を可能にします。
# MAGIC - **Vector Search**：エージェントはDatabricks Vector Searchを活用して関連する非構造化情報を効率的に検索し、検索拡張生成（RAG）とドキュメント・テーブル間のセマンティック検索などの高度なユースケースの両方をサポートします。
# MAGIC - **Unity Catalog**：すべてのデータ、モデル、エージェント、ツールにわたって統一されたガバナンスを保証します。エージェントロジック、データリネージ、ツールアクセスは規制とコンプライアンス要件を満たすよう制御され、エンタープライズセキュリティ要件との統合をサポートします。
# MAGIC - **Genie & Genie Spaces**：エージェントが構造化データと直接やり取り（例：テキストからSQLクエリ）し、複数のツールを調整して、エージェント機能を拡張（例：マルチエージェントまたはツール呼び出しアーキテクチャ）できるようにします。
# MAGIC - **MLflow 3**：エージェントの堅牢な実験追跡、バージョン管理、トレース、評価を提供します。リアルタイムトレースと自動品質測定（研究に裏付けられたLLMジャッジ付き）により、迅速なデバッグと改善サイクルが可能になります。
# MAGIC - **Databricks Apps**：組み込みチャットアプリ、フィードバック収集ポータル、プロダクションダッシュボードなどのユーザーインターフェースを提供します。これらのUIにより、ステークホルダーはエージェントとやり取りし、フィードバックを提出し、エージェントがビジネスニーズを満たすことを保証できます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>