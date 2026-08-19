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
# MAGIC
# MAGIC ## DatabricksにおけるGenAIエージェント評価
# MAGIC
# MAGIC このコースでは、従来のソフトウェアテストでは対処できない非決定論的AIシステムの独特な課題に対応し、MLflowの評価frameworkを使用してAIエージェントを体系的に評価する方法を受講者に教えます。受講者は、正確性や安全性などの一般的な基準のための組み込みジャッジ、ビジネス固有の要件のためのガイドラインジャッジ、専門的なニーズのためのカスタムジャッジなど、さまざまな評価アプローチの実装を学びます。このコースでは、キュレートされたデータセットを使用したオフライン評価と本番運用監視の両方をカバーし、MLflowのトレース機能を使用してエージェントの実行パターンを理解し、さまざまなステークホルダータイプから人間のフィードバックを収集する実践的な経験を提供します。実践的なデモンストレーションとラボを通じて、受講者はAIエージェント開発ライフサイクル全体を通じて継続的な品質改善を推進する評価ワークフローを作成するスキルを身につけます。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 前提条件
# MAGIC
# MAGIC ### Python固有のスキル
# MAGIC - 基本的なPython構文とデータ構造（リスト、辞書）
# MAGIC - 関数、クラス、オブジェクト指向プログラミングの概念の理解
# MAGIC - Pythonパッケージ管理とインポートの経験
# MAGIC - JSONデータ処理とファイル操作の知識
# MAGIC - ラムダ関数とリスト内包表記の基本的な理解
# MAGIC
# MAGIC ### SQL固有のスキル
# MAGIC - 基本的なSQLクエリ構文（SELECT、FROM、WHERE）
# MAGIC - テーブル結合と集計の理解
# MAGIC - SQL関数とデータ型の知識
# MAGIC - Unity Catalog SQL関数とプロシージャの経験
# MAGIC
# MAGIC ### Databricks固有のスキル
# MAGIC - Databricks workspaceナビゲーションとノートブックインターフェースの理解
# MAGIC - Unity Catalog構造（カタログ、スキーマ、テーブル、ボリューム）の知識
# MAGIC - Databricksコンピュートリソースとサーバレスコンピューティングの経験
# MAGIC - MLflow実験追跡とモデルレジストリの知識
# MAGIC - Databricks model serving endpointsとデプロイメントの理解
# MAGIC - Deltaテーブルに関する知識の認識
# MAGIC
# MAGIC ### GenAI/エージェント固有のスキル
# MAGIC - 大規模言語モデル（LLM）とその機能の基本的な理解
# MAGIC - プロンプトエンジニアリングとシステムプロンプトの知識
# MAGIC - ツール呼び出しエージェントと関数呼び出し概念の理解
# MAGIC - AIシステムの評価メトリクス（正確性、安全性、関連性）にある程度精通
# MAGIC - MLflowトレースとエージェント評価frameworksの基本的な知識
# MAGIC - 人間のフィードバック収集と評価workflowsの概念にある程度精通
# MAGIC
# MAGIC ### その他/オプションのスキル
# MAGIC - YAML設定ファイルの経験があると役立ちます
# MAGIC - REST APIとHTTPリクエストの基本的な理解があると役立ちます
# MAGIC - MLモデルのバージョン管理とモデルライフサイクル管理の理解があると役立ちます
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## コースagenda
# MAGIC
# MAGIC 以下のモジュールは、**Databricks Academy** による **DatabricksにおけるMLflowを使用したAIエージェント評価** コースの一部です。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC | # | モジュール名 | レッスン名 |
# MAGIC |---|-------------|-------------|
# MAGIC | 1 | [モジュール1 - AIエージェント評価の基礎]($./Module 1 - AI Agent Evaluation Fundamentals) | • *講義:* [AIエージェント評価の課題]($./Module 1 - AI Agent Evaluation Fundamentals/1.1 Lecture - The Challenge of Evaluating AI Agents)  <br> • *デモ:* [エージェントセットアップ]($./Module 1 - AI Agent Evaluation Fundamentals/1.2 Demo - Agent Setup) <br> • *講義:* [MLflowの評価framework]($./Module 1 - AI Agent Evaluation Fundamentals/1.3 Lecture - MLflow's Evaluation Framework) |
# MAGIC | 2 | [モジュール2 - 組み込みジャッジとガイドラインジャッジ]($./Module 2 - Built-In and Guideline Judges) | • *講義:* [評価ジャッジの種類]($./Module 2 - Built-In and Guideline Judges/2.1 Lecture - Types of Evaluation Judges) <br> • *デモ:* [ MLflow組み込みジャッジの使用]($./Module 2 - Built-In and Guideline Judges/2.2 Demo - Using MLflow Built-In Judges) <br> • *デモ:* [ MLflowを使用したガイドラインジャッジ]($./Module 2 - Built-In and Guideline Judges/2.3 Demo - Guideline Judges with MLflow) <br> • *ラボ:* [エージェント評価の適用]($./Module 2 - Built-In and Guideline Judges/2.4 Lab - Applying Agent Evaluation) <br> • *デモ:* [ MLflowを使用したカスタムジャッジ]($./Module 2 - Built-In and Guideline Judges/2.5 Demo - Custom Judges with MLflow)|
# MAGIC | 3 | [モジュール3 - カスタムジャッジと人間のフィードバック]($./Module 3 - Custom Judges and Human Feedback) | • *講義:* [オフライン対オンライン評価戦略]($./Module 3 - Custom Judges and Human Feedback/3.1 Lecture - Offline vs. Online Evaluation Strategies)  <br> • *講義:* [ベストプラクティスと実践的応用]($./Module 3 - Custom Judges and Human Feedback/3.2 Lecture - Best Practices and Practical Application) <br> • *ラボ:* [ MLflowを使用した開発者とSMEのフィードバック]($./Module 3 - Custom Judges and Human Feedback/3.3 Lab - Developer and SME Feedback with MLflow) |

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 要件
# MAGIC
# MAGIC レッスンを開始する前に、以下の要件を確認してください：
# MAGIC
# MAGIC * デモとラボのノートブックを実行するには、デフォルトで有効になっている **サーバレスコンピュート（バージョン5）** を使用する必要があります。
# MAGIC * このコースでは、エージェント登録とガバナンスのためにMLflowの評価frameworkとUnity Catalogへのアクセスが必要です。
# MAGIC * 一部のデモンストレーションでは、エージェントのデプロイメントと評価のためにmodel serving endpointsが必要です。
# MAGIC
# MAGIC コースは3つの論理的なモジュールに構成されています：
# MAGIC
# MAGIC 1. **モジュール1** では、AIエージェント評価の基本的な課題とMLflowのframeworkを紹介します
# MAGIC 2. **モジュール2** では、組み込みジャッジとガイドラインジャッジを使用したコア評価アプローチをカバーします
# MAGIC 3. **モジュール3** では、カスタムジャッジ、人間のフィードバック、評価戦略などの高度なトピックを探索します
# MAGIC
# MAGIC 各モジュールでは、概念を理解するための講義と、実践的な実装に向けた実演や実習を組み合わせています。学習内容は基礎概念から高度なテクニックへと段階的に進み、受講生がDatabricks上のMLflowを用いたAIエージェントの評価について、包括的な理解を深められるよう構成されています。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>