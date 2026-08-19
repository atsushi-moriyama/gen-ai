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
# MAGIC # Agent Bricksによるナレッジアシスタント
# MAGIC
# MAGIC ## はじめに
# MAGIC
# MAGIC この講義では、Databricks Mosaic AI内の宣言型frameworkである **Agent Bricks** を紹介します。これは本番環境対応のAIエージェントの作成を簡素化するものです。特に、企業ドキュメントに基づく専門的な対話エージェントを構築するための特殊なパターンである **Knowledge Assistant** に焦点を当てます。Agent Bricksが手動チューニングから成果指向の宣言へと開発パラダイムをどのように変化させ、自動最適化ループを活用して効率性を向上させるかを学習します。最後に、これらのエージェントを支える基盤アーキテクチャを探求し、堅牢性、スケーラビリティ、ガバナンスを確保する方法を理解します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このレッスンの終了時には、以下ができるようになります：
# MAGIC
# MAGIC * 従来の手動開発手法と比較したAgent Bricksの **核心的価値提案を定義** する。  
# MAGIC * 情報抽出やカスタムLLMを含む、Agent Bricksの **主要なユースケースを特定** する。  
# MAGIC * 解析、Vector Search、model servingなど、ナレッジアシスタントの **アーキテクチャコンポーネントを説明** する。  
# MAGIC * 「品質ループ」を説明し、人間のフィードバックからのエージェント学習（ALHF）がエージェントのパフォーマンスを最適化する仕組みを **説明** してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. Agent Bricksとは何か？
# MAGIC
# MAGIC **Agent Bricks** は、Databricks Mosaic AI内の **declarative** frameworkであり、本番品質のAIエージェントの作成、デプロイ、最適化を加速するように設計されています。エンジニアが手動でモデルを選択し、チャンク戦略を設定し、プロンプトを手動でチューニングしなければならない従来の「DIY」アプローチとは異なり、Agent Bricksは提供されたデータとタスクに基づいてこれらの設定決定を自動化します。
# MAGIC
# MAGIC ### A1. 本番環境AIの課題
# MAGIC
# MAGIC Generative AIを概念実証（PoC）から本番環境に移行する際、3つの主要な摩擦点に直面します：
# MAGIC
# MAGIC 1. **Optimization Complexity：** AIシステムには、LLMの選択（例：Llama 4 vs. GPT-4o）、検索戦略（チャンクサイズや埋め込みモデルなど）、プロンプトエンジニアリング技術など、多数の「調整項目」があります。特定の企業データセットに対する最適な組み合わせを見つけることは時間がかかります。  
# MAGIC 2. **Evaluation Difficulty：** エージェントが本番環境に「十分良い」かどうかを判断するには厳密なテストが必要です。チームはしばしばラベル付きの「ゴールデンデータセット」や検証可能なメトリクスを欠き、代わりに主観的な「雰囲気チェック」に頼っています。  
# MAGIC 3. **Cost vs. Quality Trade-off：** 高品質を達成するには、しばしば高価で大きなモデルが必要です。コストを削減すると通常パフォーマンスが低下します。チームは、最低コストで品質を最大化する最適なバランスを見つけるのに苦労します。
# MAGIC
# MAGIC ### A2. Agent Bricksソリューション
# MAGIC
# MAGIC Agent Bricksは、エージェント定義を **declarative** として扱うことで、これらの課題を解決します。データを提供してタスクを選択すると、Agent Bricksエンジンがシステムを反復的に最適化します。
# MAGIC
# MAGIC これを駆動する中核的なメカニズムは **人間からのフィードバックに基づくエージェント学習（ALHF）** である。システムは：
# MAGIC
# MAGIC 1. ベースラインエージェントを **即座にデプロイ** します。  
# MAGIC 2. レビューアプリ（いいね/だめ、修正された回答）を通じて **フィードバックを収集** します。  
# MAGIC 3. このフィードバックを **合成** して、手動コード変更を必要とせずに、評価ベンチマークを自動生成し、基盤となるプロンプトと設定を最適化します。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/05-agent-bricks-workflow.png" width="400"/> -->
# MAGIC
# MAGIC ![05-agent-bricks-workflow](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/05-agent-bricks-workflow.png)
# MAGIC
# MAGIC *図1: Agent Bricksの最適化サイクル。システムはタスク宣言からデプロイメントへと移行し、その後フィードバックを活用して最適化を推進し、継続的な改善のループを形成します。*

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## B. Agent Bricksのユースケース
# MAGIC
# MAGIC Agent Bricksは、一般的な企業パターン向けに事前設定されたアーキテクチャ（「ブリック」）を提供します。各ブリックは、特定の相互作用モードとデータ処理に特化されています。
# MAGIC
# MAGIC ### B1. ナレッジアシスタント
# MAGIC
# MAGIC これがこの講義の焦点です。**ナレッジアシスタントは企業ドキュメントを専門的な対話エージェントに変換します**。
# MAGIC
# MAGIC * **function：** 指定されたファイルに対して検索拡張生成 (RAG)を実行します。解析、チャンク化、埋め込み、引用生成を自動的に処理します。  
# MAGIC * **Use case：** ハンドブックに基づいて人事ポリシーの質問に答えるHRボット、または製品マニュアルに基づいてチケットを解決する技術サポートボット。
# MAGIC
# MAGIC ### B2. 情報抽出
# MAGIC
# MAGIC このエージェントタイプは、非構造化ドキュメント（PDF、画像、テキストファイルなど）を構造化データに変換します。
# MAGIC
# MAGIC * **Function：** JSONスキーマで定義された特定のフィールドを抽出します。  
# MAGIC * **Use case：** 請求書のリポジトリを「ベンダー名」、「合計金額」、「日付」を含む構造化Deltaテーブルに変換する、または法的契約から条項を抽出する。
# MAGIC
# MAGIC ### B3. マルチエージェント・スーパーバイザー
# MAGIC
# MAGIC この高度なパターンは、複雑な多段階問題を解決するために複数のエージェントとツールを調整します。
# MAGIC
# MAGIC * **Function：** 「スーパーバイザー」エージェントがユーザークエリを適切なサブエージェントまたはツール（例：Unity Catalog 関数）にルーティングします。  
# MAGIC * **Use case：** 請求に関する質問を **Genie** space（構造化データ）に、技術トラブルシューティングの質問を **Knowledge Assistant**（非構造化データ）にルーティングするカスタマーサポートシステム。
# MAGIC
# MAGIC ### B4. カスタムLLM
# MAGIC
# MAGIC このエージェントは、特定の企業ガイドラインとタスクに合わせた特殊なLLM endpointを作成します。
# MAGIC
# MAGIC * **Function：** 特定のトーン、フォーマット、またはコンプライアンス規則に従うようにモデルを最適化します。  
# MAGIC * **Use case：** ブランドのスタイルガイドに厳密に従ってソーシャルメディア投稿を書くマーケティングジェネレーター、または役員レポート用の特定フォーマットを出力する要約ツール。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 宣言型アプローチvsコードファーストアプローチ
# MAGIC
# MAGIC Databricks上でAIエージェントを構築する際、開発者は通常、2つの主要な抽象化レベルから選択します：コードファーストと宣言型です。
# MAGIC
# MAGIC ### C1. コードファースト（Mosaic AI Agent Framework）
# MAGIC
# MAGIC この手法は最大限の制御を提供しますが、より多くの努力が必要です。開発者はコア エージェント ロジックをコード（LangChain、LlamaIndex、OpenAI SDKなどのPythonライブラリを使用）で書き、スキャフォールディング、トレーシング、ガバナンスに **Mosaic AI Agent Framework** を使用します。
# MAGIC
# MAGIC * **workflow：** 開発者は検索ロジックを手動で書き、プロンプトテンプレートを定義し、埋め込みモデルを選択し、Vector searchインデックスの同期を管理します。Agent Frameworkを使用してMLflowにトレースをログし、エージェントをModel Serving endpointとしてデプロイします。  
# MAGIC * **pros：** 無限のカスタマイズ性。新しい推論ループや非常に特殊なツール使用を実装できます。  
# MAGIC * **cons：** 開発者が技術的負債を負います。最適化（チャンク化、プロンプティング）は手動で、検索戦略を変更する必要がある場合（例：チャンクサイズの変更）、コードを書き直してデプロイし直す必要があります。
# MAGIC
# MAGIC ### C2. 宣言型（Agent Bricks）
# MAGIC
# MAGIC これは「成果指向」アプローチです。開発者はエージェントが *何を* すべきかを宣言し、*どのように* するかは宣言しません。
# MAGIC
# MAGIC * **workflow：** 開発者は「ナレッジアシスタント」を選択し、PDFを含むUnity Catalogボリュームを指定し、ペルソナのテキスト説明を提供します。Agent Bricksが解析、インデックス作成、プロンプトエンジニアリングを処理します。
# MAGIC * **pros：** 最速の価値実現時間。システムは自身をテストするための合成データを作成し、フィードバックに基づいて自動最適化します。  
# MAGIC * **cons：** 純粋なコードと比較して、低レベルの実行ロジックに対する細かい制御が少ない。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. ナレッジアシスタントコンポーネント
# MAGIC
# MAGIC Agent Bricksで構築されたナレッジアシスタントは「ブラックボックス」ではありません。それはネイティブDatabricksアーキテクチャの構成システムです。これらのコンポーネントを理解することは、デバッグとガバナンスにとって重要です。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/05-agent-bricks-components.png"/> -->
# MAGIC {{'05-agent-bricks-components.png" | image}}
# MAGIC
# MAGIC *図2: Agent Bricks ナレッジアシスタントコンポーネント。これらのコンポーネントは舞台裏で動作し、ユーザーは管理する必要がありません。*
# MAGIC
# MAGIC
# MAGIC ### D1. データ取り込みと解析
# MAGIC
# MAGIC ナレッジアシスタントの基盤は **Unity Catalog Volumes** に保存されたデータです。
# MAGIC
# MAGIC * **source：** ユーザーはファイル（PDF、DOCX、HTML）を含むボリュームを選択します。
# MAGIC * **parsing：** システムは **ai\_parse\_document** を利用します。これは複雑なドキュメントからテキスト、テーブル、画像を抽出するように設計されたMosaic AI機能です。これにより、PDF内の視覚的要素（チャートなど）がLLMが理解できるコンテキストに変換されます。
# MAGIC
# MAGIC ### D2. Mosaic AI Vector Search
# MAGIC
# MAGIC 解析後、データは検索用にインデックス化される必要があります。
# MAGIC
# MAGIC * **Managed Embeddings：** Agent Bricksは自動的に埋め込みモデル（例：GTE）を選択し、**Mosaic AI Vector Search** インデックスをプロビジョニングします。  
# MAGIC * **Synchronization：** インデックスは完全に管理されています。ソースボリュームに新しいファイルが追加されると、Vector searchインデックスが自動的に更新され、手動での再インデックス処理なしにエージェントが常に最新の知識を保持できるよう保証します。
# MAGIC
# MAGIC ### D3. 推論エンジンとModel Serving
# MAGIC
# MAGIC エージェントロジックは **Model Serving** でホストされます。
# MAGIC
# MAGIC * **Inference:** ユーザーが質問すると、システムはクエリをVectorsに変換し、Vector Searchから関連チャンクを取得し、LLMに渡します。  
# MAGIC * **Citation：** 重要なことに、ナレッジアシスタントは引用を提供するように設計されています。回答をUnity Catalog ボリューム内の特定のソースファイルにマッピングし、ユーザーが精度を検証できるようにします。
# MAGIC
# MAGIC ### D4. 品質ループ（レビューアプリと評価）
# MAGIC
# MAGIC これがAgent Bricksの差別化要因です。
# MAGIC
# MAGIC * **Review App：** ステークホルダー（SME）がエージェントとチャットし、フィードバック（いいね/だめ/編集）を提供できる組み込みUI。  
# MAGIC * **LLM judges：** システムは **Mosaic AI Agent Evaluation** を使用して、相互作用トレースに対して「LLMジャッジ」を実行します。これらのジャッジは「忠実性」（モデルが幻覚したか？）や「正確性」などのメトリクスを評価します。  
# MAGIC * **Optimization：** Agent Bricksは収集されたフィードバックを使用して、パフォーマンスメトリクスを改善するためのシステム指示や設定の更新を提案します。
# MAGIC
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. まとめ
# MAGIC
# MAGIC **Agent Bricksによるナレッジアシスタント** は、AIコンポーネントの手動エンジニアリングからAI成果の管理への移行を表しています。宣言型アプローチを活用することで、チームは数分以内に企業データに基づいたRAG（検索拡張生成）システムをデプロイできます。
# MAGIC
# MAGIC **主要なポイント：**
# MAGIC
# MAGIC 1. **Optimization over Configuration：** Agent Bricksは、コストと品質のバランスを取るためにモデルと検索パラメータの選択を自動化します。  
# MAGIC 2. **Integrated Architecture：** Unity Catalog ボリューム、ai\_parse\_document、Vector Searchを自動的に調整します。  
# MAGIC 3. **Feedback-Driven：** システムは、レビューアプリと人間のフィードバックからのエージェント学習（ALHF）を活用することで、時間の経過とともに継続的に改善され、専門家のフィードバックをシステム強化へと変換します。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>