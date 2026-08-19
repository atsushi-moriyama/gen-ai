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
# MAGIC ## Databricks でのシングルエージェントアプリケーションの構築
# MAGIC
# MAGIC このコースでは、Databricks Data Intelligence Platform上でシングルエージェントアプリケーションを構築するための実践的なトレーニングを提供します。学習者は、Unity Catalog 関数をツールとして活用する AI エージェントの作成、MLflow による包括的なトレーシングとモニタリングの実装、LangChain などの従来のframeworksや Agent Bricks などの最新ソリューションを使用したエージェントのデプロイメントを学習します。このコースでは、AI Playground での初期ツール作成とテストから、ガバナンス、評価、継続的改善機能を備えた本番環境でのデプロイメントまで、エージェントの完全なライフサイクルをカバーします。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 前提条件
# MAGIC
# MAGIC - デコレータ、オブジェクト指向プログラミング、パッケージ管理に精通した中級レベルの Python プログラミング経験
# MAGIC - データベースのクエリとユーザー定義関数の作成のための基本的な SQL 知識
# MAGIC - Jupyter スタイルのノートブックまたは類似のインタラクティブ開発環境での経験
# MAGIC - Databricks workspaceのナビゲーションと基本的なコンピュート設定に関する知識
# MAGIC - カタログ、スキーマ、基本的なガバナンス原則を含む Unity Catalog の概念の理解
# MAGIC - Delta Lake テーブルと Databricks での基本的なデータクエリの経験
# MAGIC - 大規模言語モデル (LLM) とその機能の基本的な理解
# MAGIC - プロンプトエンジニアリングの概念と自然言語処理に関する知識
# MAGIC - 実験トラッキングとモデル管理のための MLflow の基本知識
# MAGIC
# MAGIC ---
# MAGIC ## コースAgenda
# MAGIC 以下のモジュールは、**Databricks Academy** による **Databricks でのシングルエージェントアプリケーションの構築** コースの一部です。
# MAGIC
# MAGIC | # | モジュール名                               |
# MAGIC | - | ----------------------------------------- |
# MAGIC | 1 | [エージェントの基礎]($./M01 - Foundations of Agents)                     |
# MAGIC | 2 | [シングルエージェントの構築]($./M02 - Building Single Agents)                    |
# MAGIC | 3 | [再現可能なエージェント]($./M03 - Reproducible Agents)                       |
# MAGIC | 4 | [Agent Bricks による本番環境対応エージェント]($./M04 - Production-Ready Agents with Agent Bricks) |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 要件
# MAGIC
# MAGIC レッスンを開始する前に、以下の要件を確認してください：
# MAGIC
# MAGIC - すべてのデモとラボのノートブックを実行するために、Databricks Runtime バージョン： **`Serverless`**  を使用してください。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>