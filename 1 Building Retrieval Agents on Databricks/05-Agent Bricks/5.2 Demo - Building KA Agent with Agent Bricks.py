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
# MAGIC # デモ - Agent Bricksを使用したナレッジアシスタント（KA）エージェントの構築
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC このデモでは、**Agent Bricks: Knowledge Assistant** を使用して高品質なナレッジアシスタントエージェントを構築する方法を探ります。Databricksの宣言型エージェント作成ツールを使用してドキュメントに対する質問応答チャットボットを作成し、専門家のフィードバックとラベリングセッションを通じてその品質を向上させる方法を説明します。
# MAGIC
# MAGIC **Scenario：** **Orion Knowledge Assistant（OKA）** は、Orion A1ヒューマノイドプラットフォームで作業するエンジニアと技術者に、Databricksに保存された内部設計マニュアル、コンプライアンス文書、メンテナンスガイドから取得したコンテキストに基づく即座の回答を提供します。現場エンジニアがモーションコントローラーの再校正方法やファームウェアチェックサムの検証方法について質問すると、OKAは正確な手順を取得し、正しいセクションを参照するか、情報が利用できない場合は明確にその旨を伝えます。このアプローチにより、ミッションクリティカルな環境での信頼性と正確性が維持されます。
# MAGIC
# MAGIC
# MAGIC ## 学習目標
# MAGIC - Agent Bricksを使用したナレッジアシスタントエージェント作成の主要コンポーネントと要件を **特定** する。
# MAGIC - Unity Catalogファイルをナレッジソースとして使用するナレッジアシスタントエージェントを **構成** し作成する。
# MAGIC - 引用とソース検証を含むAI Playgroundを使用したエージェントテストと評価を **実装** する。
# MAGIC - ラベリングセッションと専門家フィードバック収集を通じてエージェントの品質を **改善** する。
# MAGIC - エージェント最適化とパフォーマンス監視のベストプラクティスを **適用** する。
# MAGIC
# MAGIC ## 要件
# MAGIC - Mosaic AI Agent Bricks プレビュー（ベータ）が有効になっているワークスペース。
# MAGIC - **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、教室環境を設定します。
# MAGIC
# MAGIC このステップにより、すべての依存関係が利用可能になり、ワークスペースがデモの準備が整います。
# MAGIC

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-05

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ## A. KAエージェントの作成
# MAGIC
# MAGIC **Agent Name：** **Orion Knowledge Assistant（OKA）**
# MAGIC
# MAGIC ドキュメントはUnity Catalog（UC）ボリュームに配置されています。Agent Bricksを使用してKAエージェントを作成します。
# MAGIC
# MAGIC **エージェントを作成する手順：**
# MAGIC
# MAGIC 1. Databricks workspaceで、左のナビゲーションペインの **Agents** に移動します
# MAGIC 1. **Create Agent** ボタンをクリックします
# MAGIC 1. **Knowledge Assistant** ボックスをクリックして、新しいKAエージェントの作成を開始します
# MAGIC 1. 以下の情報を入力します：
# MAGIC    - **Name**: `Orion_Knowledge_Assistant`
# MAGIC    - **Description**: 次のような説明を入力します：  
# MAGIC      `Orion Knowledge Assistant（OKA）は、エンジニアと技術者がOrionの内部マニュアル、メンテナンスガイド、安全文書から正確な回答を迅速に見つけるのを支援します。ソース参照付きの明確で検証済みの回答を提供し、検索時間を短縮し、チーム全体で一貫性のある信頼できる情報を確保します。`
# MAGIC    - **Knowledge source type**: ボリューム内のファイル
# MAGIC    - **Source**: 使用したカタログに基づいてUnity Catalogボリュームを選択します（ボリューム名については上記を参照）
# MAGIC    - **Confirm** をクリックします
# MAGIC    - **Knowledge source name**: `Company Documents`
# MAGIC    - **Content description**: 次のようなコンテンツ説明を入力します：  
# MAGIC      `Orionの技術文書、エンジニアリングノート、ハンドブック、よくある質問が含まれています。`
# MAGIC 1. *（オプション）* エージェントがどのように応答すべきかについての指示を追加します。以下の指示例を参照してください。
# MAGIC 1. **Create Agent** をクリックして作成プロセスを開始します
# MAGIC
# MAGIC サンプル指示プロンプト：  
# MAGIC `あなたはOrion Knowledge Assistant（OKA）です。エンジニアと技術スタッフに適した明確で専門的かつ事実に基づいたトーンで応答してください。Orionの内部文書からの検証済み情報のみを使用し、利用可能な場合はソース参照を含めてください。回答が見つからない場合は、その旨を明確に述べ、関連セクションや次のステップを提案してください。推測、仮定、または提供されたコンテキスト外の情報は提供しないでください。`
# MAGIC
# MAGIC **⏳ 注意：** エージェントの作成とナレッジソースの同期には最大10分かかる場合があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. エージェントのテスト
# MAGIC
# MAGIC エージェントの構築が完了したら、組み込みチャットインターフェースを使用してその機能をテストできます。チャットエリアはAgent Bricksインターフェースの右側に表示されます。
# MAGIC
# MAGIC **テスト用サンプル質問：**
# MAGIC
# MAGIC サンプル文書に基づいて、エージェントに以下の質問をしてみてください：
# MAGIC
# MAGIC 1. "OrionはISO 13849-1への準拠をどのように検証しますか？"
# MAGIC 1. "Orionモーションコントローラーは高速移動中の安定性をどのように維持しますか？"
# MAGIC 1. **"Orionの赤い点滅ライトは何を意味しますか？"** 
# MAGIC *注意：Orionドキュメントには赤い点滅ライトはありません。* 
# MAGIC
# MAGIC **確認すべき点：**
# MAGIC - ドキュメントに基づく正確な回答
# MAGIC - 適切な引用とソース参照
# MAGIC - ナレッジベース外の質問の適切な処理
# MAGIC - 専門的で有用なトーン
# MAGIC
# MAGIC **💡 最後の質問に対してエージェントがより良い回答を提供するようにしたい場合は、エージェントの品質を改善する必要があります。次にそれに進みましょう！**

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ## C. エージェント品質の改善
# MAGIC
# MAGIC Agent Bricks: ナレッジアシスタントでは、専門家のフィードバックとラベリングセッションを通じてエージェントの品質を向上させることができます。これらの機能により、主題専門家から自然言語フィードバックを収集し、それを使用してエージェントを再トレーニングし最適化することができます。
# MAGIC
# MAGIC **品質改善を使用するタイミング：**
# MAGIC - エージェントが不正確または不完全な回答を提供する場合
# MAGIC - エージェントのトーンとコミュニケーションスタイルを微調整する場合
# MAGIC - 新しいナレッジドメインやユースケースに拡張する場合
# MAGIC - ユーザーフィードバックに基づく継続的な最適化のため
# MAGIC - 異なる質問タイプ全体での一貫したパフォーマンスを確保するため
# MAGIC
# MAGIC
# MAGIC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. ラベル付きデータを使用した品質改善
# MAGIC
# MAGIC このステップでは、上記の質問に対するエージェントの回答を改善するためにラベル付きデータを提供します。
# MAGIC
# MAGIC **品質改善プロセス：**
# MAGIC 1. エージェントのインターフェースの **Examples** タブに移動します。
# MAGIC 1. **Add** ボタンをクリックします。
# MAGIC 1. 質問（`Orionの赤い点滅ライトは何を意味しますか？`）を入力し、*Add** を押して質問を追加します。
# MAGIC 1. 質問をクリックして詳細を開きます。
# MAGIC 1. 以下のような **Guidelines** を追加します：
# MAGIC   
# MAGIC     >Orionには点滅する赤いライトがないことをユーザーに知らせる
# MAGIC
# MAGIC     >バッテリーを取り外して再挿入することでOrionを再起動するようユーザーに依頼する
# MAGIC       
# MAGIC     >ライトの色を確認する
# MAGIC       
# MAGIC     >ライトが点滅するかどうか再度確認する
# MAGIC   
# MAGIC
# MAGIC エージェントのナレッジのさまざまな側面をテストする評価質問を追加します。
# MAGIC
# MAGIC **エージェントをテスト：**
# MAGIC 1. エージェントに戻り、同じ質問をして **回答が改善されたかどうかを確認** します。また、**別の色について質問して回答がどのように適応するかを確認** することもできます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 専門家レビューを使用した品質改善
# MAGIC
# MAGIC **ラベリングセッションと専門家レビュー：**
# MAGIC
# MAGIC ラベリングセッション機能により、専門家は以下を行うことができます：
# MAGIC - 評価質問に対するエージェントの回答をレビューする
# MAGIC - 回答品質について自然言語フィードバックを提供する
# MAGIC - エージェントの動作に関するガイドラインと期待値を追加する
# MAGIC - 正確性、完全性、トーンについて回答を評価する
# MAGIC
# MAGIC 専門家レビュープロセスの詳細な手順については、[Agent Bricks: ナレッジアシスタント ドキュメント – ステップ3：品質の改善](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant#step-3-improve-quality)を参照してください。
# MAGIC
# MAGIC **ベストプラクティス：** 品質改善は反復的なプロセスです。最適なエージェントパフォーマンスを達成するために、複数ラウンドのフィードバック収集と改良を計画してください。
# MAGIC
# MAGIC **💡 質問：** ガイドラインは品質改善にどのように使用されますか？これに関してエージェントトレースで何を観察しますか？

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ## D. リソースのクリーンアップ
# MAGIC
# MAGIC このデモを完了した後、不要なコストの発生を避けるために作成したリソースをクリーンアップすることが重要です。**KAエージェントは、ドキュメントに対するセマンティック検索を可能にするために、バックグラウンドでvector search endpointとサービングendpointを作成します**。これらのendpointsは、アクティブに使用されていない場合でも課金が継続されます。
# MAGIC
# MAGIC **エージェントを削除するには：**
# MAGIC 1. 左のナビゲーションペインの **Agents** に移動します
# MAGIC 1. **Orion_Knowledge_Assistant** エージェントを見つけます
# MAGIC 1. エージェントをクリックして詳細を開きます
# MAGIC 1. エージェントオプションメニュー（右上）から **Delete** を選択します
# MAGIC 1. プロンプトが表示されたら削除を確認します
# MAGIC
# MAGIC エージェントを削除すると、関連するvector search endpointとサービングendpointも削除されます。

# COMMAND ----------

# MAGIC %md
# MAGIC    
# MAGIC ## まとめ
# MAGIC
# MAGIC Agent Bricks: ナレッジアシスタントを使用してKAエージェントを正常に構築し改善しました。達成したことの簡潔な要約は以下の通りです：
# MAGIC
# MAGIC **構築したもの：**
# MAGIC - 宣言型Agent Bricksインターフェースを使用したKAエージェントの作成
# MAGIC - Unity Catalogファイルをナレッジソースとしてエージェントを構成
# MAGIC - 組み込みチャットインターフェースを使用したエージェントのテスト
# MAGIC - 専門家フィードバックとラベリングセッションを通じたエージェント品質の向上
# MAGIC
# MAGIC **次のステップ（オプション）：**
# MAGIC
# MAGIC KAエージェントが動作するようになったので、以下の次のステップを検討してください：
# MAGIC
# MAGIC 1. **Expand knowledge sources**: 追加のドキュメントタイプとデータソースを追加して、エージェントのカバレッジを広げる
# MAGIC 1. **Quality optimization**: ラベリングセッションと専門家レビューを使用してエージェントのパフォーマンスを継続的に改善する
# MAGIC 1. **Production deployment**: 適切なガバナンスと監視を備えた本番環境でエージェントを展開する
# MAGIC
# MAGIC **additional resources：**
# MAGIC - [Agent Bricks ドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant)
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>