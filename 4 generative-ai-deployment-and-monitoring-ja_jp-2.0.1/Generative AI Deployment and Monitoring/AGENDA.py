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
# MAGIC
# MAGIC
# MAGIC ## Gen AIの導入と監視
# MAGIC
# MAGIC 本コースでは、生成型人工知能（AI）アプリケーションの運用化、展開、監視について学びます。まず、Model Servingなどのツールを用いたGen AIアプリケーションの展開に関する知識とスキルを習得します。次に、現代的なLLMOpsのベストプラクティスと推奨アーキテクチャに沿ったGen AIアプリケーションの運用化について議論します。最後に、Lakehouse Monitoringを用いたGen AIアプリケーションとそのコンポーネントの監視手法について紹介します。
# MAGIC
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 前提条件
# MAGIC
# MAGIC このコンテンツは、以下のスキル・知識・能力を持つ参加者を対象に開発されました： 
# MAGIC - 自然言語処理の概念に関する知識
# MAGIC - プロンプトエンジニアリング/プロンプトエンジニアリングのベストプラクティスに関する知識 
# MAGIC - Databricks Data Intelligence Platformに関する知識
# MAGIC - RAGに関する知識（データ準備、RAGアーキテクチャ構築、埋め込み、vector、vectorデータベースなどの概念）
# MAGIC - 多段階推論LLMチェーンとエージェントを用いたLLMアプリケーション構築の経験
# MAGIC - 評価およびガバナンスのためのDatabricks Data Intelligence Platformツールに関する知識。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## コースAgenda
# MAGIC 以下のモジュールは、**Databricks Academy**による **Gen AIのデプロイとモニタリング** コースの一部です。
# MAGIC
# MAGIC | # | モジュール名 | レッスン名 |
# MAGIC |---|-------------|-------------|
# MAGIC | 1 | **Model Deployment Fundamentals** | • *講義:* モデルマネジメント <br> • *講義:* デプロイ方法 |
# MAGIC | 2 | [バッチデプロイメント]($./01 - Batch Deployment) | • *講義:* バッチデプロイメント入門 <br> • [**デモ:** SLMを用いたバッチ推論]($./01 - Batch Deployment/1.0 - Batch Inference using SLM) <br> • [**ラボ:** SLMを用いたバッチ推論]($./01 - Batch Deployment/1.LAB - Batch Inference using SLM) |
# MAGIC | 3 | [リアルタイムデプロイメント]($./02 - Real-time Deployment) | • *講義:* リアルタイムデプロイメント入門 <br> • *講義:* Databricks Model Serving <br> • [**デモ:** Databricks Model servingへのLLMチェーンのデプロイ]($./02 - Real-time Deployment/2.1 - Deploying an LLM Chain to Databricks Model Serving) <br> • [**デモ:** プロビジョニングされたスループットを備えたモデルの提供]($./02 - Real-time Deployment/2.2 - Serving Models with PT) <br> • [**ラボ:** カスタムモデルのデプロイとA/Bテスト]($./02 - Real-time Deployment/2.LAB - Custom Model Deployment and A-B Testing) |
# MAGIC | 4 | [AIシステム監視]($./03 - AI System Monitoring) | • *講義:* AIアプリケーション監視 <br> • [**デモ:** LLM RAGチェーンのオンライン監視]($./03 - AI System Monitoring/3.1 - Online Monitoring an LLM RAG Chain) <br> • [**ラボ:** オンライン監視]($./03 - AI System Monitoring/3.LAB - Online Monitoring) |
# MAGIC | 5 | **LLMOps concepts** | • *講義:* MLOps入門 <br> • *講義:* デプロイ方法 |
# MAGIC
# MAGIC
# MAGIC ---
# MAGIC ## 要件
# MAGIC
# MAGIC レッスンを開始する前に、以下の要件をご確認ください：
# MAGIC
# MAGIC * すべてのデモおよびラボノートブックの実行には、Databricks Runtime バージョン **`17.3.x-cpu-ml-scala2.13`** を使用してください。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>