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
# MAGIC ## Databricks上でのリトリーバルエージェントの構築
# MAGIC
# MAGIC このコースでは、Databricks Data Intelligence Platform上でリトリーバルエージェントを構築するための実践的なトレーニングを提供します。参加者は、非構造化ドキュメントを構造化データに解析し、リトリーバルworkflowsのためにコンテンツを変換・チャンク化し、ドキュメント検索のためのVector searchソリューションを構築し、MLflowとAgent Bricksを使用して本番対応のエージェントを開発する方法を学習します。このコースでは、ドキュメント処理から埋め込み生成、vectorインデックス化、ガバナンス機能を備えたエージェントのデプロイメントまで、エージェントの完全なライフサイクルをカバーします。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 前提条件
# MAGIC
# MAGIC - 中級レベルのPythonプログラミング経験
# MAGIC - クエリと関数作成のための基本的なSQL知識
# MAGIC - Databricks Data Intelligence Platformに関する知識
# MAGIC - カタログとスキーマを含むUnity Catalogの概念の理解
# MAGIC - 大規模言語モデル（LLM）とプロンプトエンジニアリングの基本的な理解
# MAGIC - エクスペリメント追跡のためのMLflowの基本知識
# MAGIC
# MAGIC ---
# MAGIC ## コースAgenda
# MAGIC 以下のモジュールは、**Databricks Academy** による **Databricks上でのリトリーバルエージェントの構築** コースの一部です。
# MAGIC
# MAGIC | # | モジュール名 | レッスン |
# MAGIC | - | ----------- | ------- |
# MAGIC | 1 | [リトリーバルエージェントの基礎]($./01-Foundations of Retrieval Agents) | [1.1 講義 - プロンプトを超えて – リトリーバルエージェントとコンテキストエンジニアリング]($./01-Foundations of Retrieval Agents/1.1 Lecture - Beyond Prompts – Retrieval Agents and Context Engineering) |
# MAGIC | 2 | [ドキュメント解析とチャンク化]($./02-Document Parsing and Chunking) | [2.1 講義 - ドキュメント解析とチャンク化]($./02-Document Parsing and Chunking/2.1 Lecture - Document Parsing and Chunking) |
# MAGIC | | | [2.2 デモ - ドキュメントを構造化データに解析]($./02-Document Parsing and Chunking/2.2 Demo - Parse Documents to Structured Data) |
# MAGIC | | | [2.3 デモ - 解析されたコンテンツの変換とチャンク化]($./02-Document Parsing and Chunking/2.3 Demo - Transform and Chunk Parsed Content) |
# MAGIC | | | [2.4 ラボ - ドキュメントの解析、変換、チャンク化]($./02-Document Parsing and Chunking/2.4 Lab - Parse Transform and Chunk Documents) |
# MAGIC | 3 | [リトリーバルのためのVector search]($./03-Vector Search for Retrieval) | [3.1 講義 - 埋め込みとVector search]($./03-Vector Search for Retrieval/3.1 Lecture - Embeddings and Vector Search) |
# MAGIC | | | [3.2 デモ - リトリーバルのためのVector searchの構築]($./03-Vector Search for Retrieval/3.2 Demo - Building Vector Search for Retrieval) |
# MAGIC | | | [3.3 ラボ - リトリーバルのためのVector searchの構築]($./03-Vector Search for Retrieval/3.3 Lab - Building Vector Search for Retrieval) |
# MAGIC | 4 | [リトリーバルエージェントの構築とロギング]($./04-Building and Logging Retrieval Agents) | [4.1 講義 - MLflowとエージェント開発]($./04-Building and Logging Retrieval Agents/4.1 Lecture - MLflow and Agent Development) |
# MAGIC | | | [4.2 デモ - リトリーバルエージェントの構築とロギング]($./04-Building and Logging Retrieval Agents/4.2 Demo - Building and Logging a Retrieval Agent) |
# MAGIC | | | [4.3 ラボ - リトリーバルエージェントの構築と登録]($./04-Building and Logging Retrieval Agents/4.3 Lab - Building and Registering Retrieval Agent) |
# MAGIC | 5 | [Agent Bricks]($./05-Agent Bricks) | [5.1 講義 - Agent Bricksを使用したナレッジアシスタント]($./05-Agent Bricks/5.1 Lecture - Knowledge Assistant with Agent Bricks) |
# MAGIC | | | [5.2 デモ - Agent Bricksを使用したKAエージェントの構築]($./05-Agent Bricks/5.2 Demo - Building KA Agent with Agent Bricks) |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 技術要件
# MAGIC
# MAGIC レッスンを開始する前に、以下の要件を確認してください：
# MAGIC
# MAGIC - すべてのデモとラボノートブックを実行するための **Serverless Compute (environment version 5)** の使用
# MAGIC - **`ai_parse_document()`** 関数へのアクセス（ベータ機能）
# MAGIC - **Mosaic AI Agent Bricks** へのアクセス（ベータ機能）
# MAGIC - 事前に作成された **Vector search endpoint**
# MAGIC - 埋め込み生成のための **Foundation Model APIs** へのアクセス

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>