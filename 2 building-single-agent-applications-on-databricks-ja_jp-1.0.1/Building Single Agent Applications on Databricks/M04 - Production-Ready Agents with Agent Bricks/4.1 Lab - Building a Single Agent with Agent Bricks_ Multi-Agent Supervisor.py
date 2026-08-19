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
# MAGIC # ラボ - Agent bricksによる単一エージェントの構築：Supervisor agent
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC Agent bricks supervisor agentは、複雑なタスクにおいてAIエージェントとツールが連携して動作するよう調整する協調型マルチエージェントシステムを構築します。このシステムは、ジーニースペース、エージェントエンドポイント、Unity Catalog機能、MCPサーバーを連携させ、専門分野にまたがる包括的なソリューションを提供します。
# MAGIC
# MAGIC supervisorシステムは、高度なAIオーケストレーションパターンを使用してエージェントの相互作用、タスクの委任、結果の統合を管理します。専門家からの自然言語フィードバックを使用して、時間の経過とともに調整品質を向上させることができます。
# MAGIC
# MAGIC ## 学習目標
# MAGIC _このラボの終了時には、以下のことができるようになります：_
# MAGIC
# MAGIC - Agent Bricksを使用してsupervisor agentシステムを設定および展開する
# MAGIC - Unity Catalog関数を supervisor framework内のツールとして統合する
# MAGIC - AI Playgroundを通じてsupervisorの調整機能をテストする
# MAGIC - 時間の経過とともにエージェントのパフォーマンスを向上させるフィードバックメカニズムを実装する
# MAGIC - デプロイされたAgent Bricksリソースをクリーンアップする

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 教室の設定
# MAGIC
# MAGIC このノートブックの作業環境を設定するには、次のセルを実行してください。このデモではプレビュー機能が有効になっている場合があります。プレビュー機能の有効化については[こちら](https://docs.databricks.com/aws/en/release-notes/release-types)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバーレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバーレスコンピュート上で実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレス上で実行されています。
# MAGIC
# MAGIC **このデモはサーバーレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバーレスを使用していることを確認するために、[ノートブックのサーバーレスバージョンの表示と変更に関するドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC ワークスペースの設定の一部として、いくつかのPythonライブラリがインストールされています。ノートブックスコープのライブラリのリストを確認するには、[このドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies#configure-environment-for-job-tasks)をお読みください。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-4.1

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. AIエージェントツールの検査
# MAGIC
# MAGIC 教室設定の一部として、UC関数は適切な権限で既に設定されています。Catalog Explorerに移動し、`avg_neigh_price` と `airbnb_posting_info` を検索してください。次のセクションに進む前に、ツールを検査し、その説明を読んでください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. supervisor agentの設定
# MAGIC
# MAGIC Unity Catalogの機能が準備できたので、supervisor agentシステムを作成し設定できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. Agent Bricksインターフェースへのアクセス
# MAGIC
# MAGIC 1. ワークスペースの左側のナビゲーションペインで **Agents** に移動します
# MAGIC 2. **Supervisor agent** タイルから、**build** をクリックします
# MAGIC 3. 設定インターフェースに移動します

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. supervisor設定の構成
# MAGIC
# MAGIC **Configure** タブで、以下の情報を使用してsupervisorを設定します：
# MAGIC
# MAGIC - **Name**: エージェントにラボユーザー名 + MAS_single_agentという名前を付けます。例： `labuser_123_abc_MAS_single_agent`
# MAGIC - **Description**: 以下の説明をコピーして貼り付けます：_これは、Airbnbサンプルデータセットに関する質問に答えるためにツール呼び出しを使用するエージェントです。_

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. Unity Catalog関数をツールとして追加
# MAGIC
# MAGIC **Configure Agents** の下で、Unity Catalog関数を追加します：
# MAGIC
# MAGIC 1. **+ Add** をクリックして新しいエージェント/ツールを追加します
# MAGIC 1. **Type** フィールドで **Unity Catalog Function** を選択します
# MAGIC 1. **Unity Catalog Function** ドロップダウンメニューから以下の関数を選択します（検索ボックスを使用できます）
# MAGIC    - `avg_neigh_price`
# MAGIC 1. **Confirm** をクリックし、同じ手順を繰り返してUC関数 `airbnb_posting_info` を追加します
# MAGIC 1. このツールに **Agent name** を指定するか、ツール選択後に自動生成されるエージェント名を使用できます。
# MAGIC 1. 通常、**Describe the content** の下で、この関数が何をするか、いつ使用すべきかの詳細な説明を提供する必要があります。ただし、関数に説明を事前設定しているため、UCから取り込まれています。
# MAGIC
# MAGIC **注意：** 単一のsupervisorシステムに最大10個のエージェント/ツールを追加できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C4. supervisor作成の完了
# MAGIC
# MAGIC すべての設定を構成し、ツールを追加した後：
# MAGIC
# MAGIC 1. 設定の正確性を確認します
# MAGIC 2. **Create Agent** をクリックします
# MAGIC 3. システムがsupervisor agentを構築するまでお待ちください（数分かかります）

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. テストと検証
# MAGIC
# MAGIC supervisorが構築されたら、Agent Bricksメニューでテストするか、AI Playgroundでエージェントを開いてテストする準備が整います（スクリーンショット参照）。AI Playgroundを使用しましょう。
# MAGIC
# MAGIC ![mas-creation.png](../Includes/images/mas-creation.png "mas-creation.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. AI Playgroundテスト
# MAGIC **Open in Playground** をクリックすると、**機能を確認** する以下のボタンが表示されます： 
# MAGIC ![review-capabilities.png](../Includes/images/review-capabilities.png)
# MAGIC 次に、**permission requested** 画面で **authorize** をクリックしてください。
# MAGIC ![permission-requested.png](../Includes/images/permission-requested.png)
# MAGIC 以下のクエリを実行し、エージェントが適切なツールを使用しているかテストしてください：
# MAGIC - _ミッション地区の平均価格はいくらですか？また、物件番号958の詳細はどのようなものですか？_
# MAGIC
# MAGIC **Note:** endpointがクエリを受け付ける準備が整うまで、4～5分待つ必要がある場合があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ![mas-ai-playground-results.png](../Includes/images/mas-ai-playground-results.png "mas-ai-playground-results.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. （オプション）フィードバックと改善の実装
# MAGIC
# MAGIC Agent bricks supervisor agentは、専門家の自然言語フィードバックに基づいて調整の質を向上させることができます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. ラベル付けセッションを作成する
# MAGIC _エージェントのendpointが作成されてから、SMEセッションの準備が整うまで通常約15分かかります。_
# MAGIC
# MAGIC supervisorの改善に向けたフィードバックを収集するため：
# MAGIC
# MAGIC 1. エージェントの設定メニューに戻り、**examples** タブに移動してください
# MAGIC 2. **+ Add** をクリックして評価用のタスクシナリオを追加します
# MAGIC 3. supervisorの調整能力をテストする質問やタスクを入力してください。例：_アッパーマーケットの平均価格はいくらですか？_
# MAGIC 4. **add** をクリック

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. 模擬専門家フィードバック
# MAGIC
# MAGIC 専門知識を持つ担当者向けのラベル付けセッションを設定する：
# MAGIC
# MAGIC 1. 質問をクリックすると、**input** と **guidelines** が表示されます。**guidelines** をクリックしてください。
# MAGIC 2. ガイドラインに追加：_アッパーマーケットは「カストロ/アッパーマーケット」とも呼ばれるため、検索クエリではその名称を使用してください
# MAGIC 3. **save** をクリック

# COMMAND ----------

# MAGIC %md
# MAGIC ### E3. フィードバックを適用し、再トレーニングを実施する
# MAGIC
# MAGIC 専門家がレビューを完了した後：
# MAGIC
# MAGIC 1. **build** タブに戻る
# MAGIC 2. 改善を確認するため、以前合格したのと同じ質問でsupervisorを再度テストしてください：_アッパーマーケットの平均価格はいくらですか？_

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. クリーンアップ
# MAGIC MASの設定中にデプロイしたリソースをクリーンアップしてください。
# MAGIC 1. **Agents** に移動し、先ほどデプロイしたエージェントを選択します。
# MAGIC 1. 右上の3つの縦の点を選択し、削除をクリックします（スクリーンショット参照）。削除を元に戻すことができないという詳細メッセージが表示されます。再度 **Delete** をクリックします。
# MAGIC
# MAGIC ![delete-mas.png](../Includes/images/delete-mas.png "delete-mas.png")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このラボでは、Agent Bricksを使用してsupervisor agentシステムを構築・デプロイし、Airbnbデータのクエリ用専用ツールとしてUnity Catalog機能を統合することに成功しました。AI Playgroundを通じてsupervisorの調整機能をテストし、エージェントのパフォーマンスを時間経過とともに改善するためのフィードバックメカニズムの実装方法を検討しました。最後に、クリーンなワークスペース環境を維持するための適切なリソースクリーンアップ手順を学びました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>