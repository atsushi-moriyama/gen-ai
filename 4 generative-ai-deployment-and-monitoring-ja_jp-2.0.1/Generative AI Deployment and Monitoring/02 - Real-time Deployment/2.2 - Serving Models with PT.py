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
# MAGIC # プロビジョニングされたスループットを備えたサービスのモデル
# MAGIC
# MAGIC **このデモでは、プロビジョニングされたスループットを使用したGenAIアプリケーションのデプロイに焦点を当てます。**
# MAGIC
# MAGIC デプロイメントは、LLMベースのアプリケーションを運用化する上で重要な要素です。Databricks内でのデプロイメントオプションを検討し、本番環境対応のModel servingを実現する方法を実演します。
# MAGIC
# MAGIC ## なぜプロビジョニング済みスループットなのか？
# MAGIC
# MAGIC プロビジョニング済みスループットのデプロイメントは、以下の利点を提供するため、本番環境において不可欠です：
# MAGIC
# MAGIC * **Throughput Guarantees:** アプリケーションのSLA要件を満たす専用コンピューティングリソースにより、一貫性のある予測可能なパフォーマンスを確保します。
# MAGIC * **Compliance Requirements:** 規制対象業界および企業ガバナンス方針に必要なデータ分離とセキュリティ管理を維持する。
# MAGIC * **Production Reliability:** コールドスタートとリソース競合を排除し、変動する負荷条件下でも安定した応答時間を実現します。
# MAGIC * **Cost Predictability:** 固定容量課金により、生産ワークロードの正確な予算予測が可能になります。
# MAGIC
# MAGIC **Learning Objectives:**
# MAGIC
# MAGIC *このデモの終わりまでに、次のことができるようになります：*
# MAGIC
# MAGIC * モデルデプロイメントにおいてプロビジョニング済みスループットを使用すべきタイミングを理解する。
# MAGIC * `system.ai` カタログから外部モデルを、プロビジョニングされたスループットを備えた Databricks Model Serving endpointにデプロイします。
# MAGIC * 本番環境でデプロイされたモデルのクエリと検証を行う。
# MAGIC
# MAGIC **🚨 重要: プロビジョニングされたスループットを用いたモデルのデプロイには、膨大なコンピューティングリソースを必要とします。そのため、このデモは講師主導で実施されるように設計されており、トレーニングワークスペースではモデルはデプロイされません。**

# COMMAND ----------

# MAGIC %md
# MAGIC ## 要件
# MAGIC
# MAGIC レッスンを開始する前に、以下の要件をご確認ください：
# MAGIC
# MAGIC * このノートブックを実行するには、以下のいずれかのDatabricks runtimeを使用する必要があります：  **`17.3.x-cpu-ml-scala2.13`**
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## デモ概要
# MAGIC
# MAGIC このデモでは、Databricksでプロビジョニングされたスループットを用いたモデルのデプロイ手順を順を追って説明します。以下のステップで解説します：
# MAGIC
# MAGIC 1. **`system.ai` Catalog** 内のモデルにアクセスする。
# MAGIC
# MAGIC 1. **`gpt-oss-20b`Model** をプロビジョニング済みスループットを備えたDatabricks Model Serving endpointにデプロイします。
# MAGIC
# MAGIC 1. デプロイされたモデルをクエリし、検証する。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## プロビジョニング済みスループットでモデルをデプロイする
# MAGIC
# MAGIC AI PlaygroundやFoundation Model APIといったツールを用いて一般的なLLMをクエリする手法を説明・利用してきましたが、本番アプリケーションでは保証されたスループットとパフォーマンスSLAを備えた専用コンピューティングリソースが必要となる場合が多くあります。
# MAGIC
# MAGIC これを実現するため、**Databricks Model Serving with Provisioned Throughput** を利用します。このデプロイメントオプションは、一貫したパフォーマンスを保証し、コンプライアンス要件を満たし、本番ワークロードに対して予測可能なコストを提供する専用インフラストラクチャを提供します。
# MAGIC
# MAGIC 次に、`system.ai` カタログからプロビジョニングされたスループットでモデルをデプロイする方法を実演します。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### `system.ai` カタログからモデルを取得する
# MAGIC
# MAGIC Databricksの **`system.ai`Catalog** は、Databricks GenAIおよびUnity Catalogサービスの一部です。これはUnity Catalogで管理される、厳選された最先端のオープンソースモデルのリストです。これらのモデルは、プロビジョニングされたスループットを備えたModel Servingを使用して簡単にデプロイしたり、モデルトレーニングで微調整したりできます。
# MAGIC
# MAGIC このデモでは、本番環境での使用に適した強力なオープンソース言語モデルである **`gpt-oss-20b`** モデルのデプロイ方法を紹介します。
# MAGIC
# MAGIC モデルを表示およびアクセスするには：
# MAGIC
# MAGIC 1. 左側のパネルから **Catalog** を選択してください。
# MAGIC 1. **System** カタログを選択してください。
# MAGIC 1. **ai** スキーマを選択してください。これにより、提供可能なモデルのリストが表示されます。
# MAGIC 1. リスト内で **`gpt-oss-20b`** モデルを探してください。
# MAGIC
# MAGIC <!--  -->
# MAGIC
# MAGIC ![genai-as-04-system-ai-catalog](../Includes/images/genai-as-04-system-ai-catalog-v2.png)
# MAGIC
# MAGIC **注記:** `system.ai` カタログ内のモデルは Unity Catalog によって管理され、安全なアクセス制御と組織のデータガバナンスポリシーへの準拠が保証されます。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### プロビジョニング済みスループットによるモデルのデプロイ
# MAGIC
# MAGIC `system.ai` カタログ内で `gpt-oss-20b` モデルを特定したら、以下の手順に従って Databricks Model Serving にプロビジョニング済みスループットでデプロイできます：
# MAGIC
# MAGIC 1. カタログ内の **`system.ai.gpt_oss_20b`** モデルページに移動します。
# MAGIC
# MAGIC 1. **Serve this model** ボタンをクリックしてください。
# MAGIC
# MAGIC 1. 提供されるエンティティを設定します：
# MAGIC     * 名前: `gpt_oss_20b_endpoint`.
# MAGIC     * 提供対象エンティティについては、`gpt-oss-20b`モデルを選択してください。
# MAGIC
# MAGIC 1. **Confirm** ボタンをクリックしてください。
# MAGIC
# MAGIC 1. モデル提供エンドポイントを**プロビジョニング済みスループット**で構成します：
# MAGIC     * コンピューティングタイプとして**プロビジョニング済みスループット**を選択してください。
# MAGIC     * スループット要件に基づいて適切なワークロードサイズを選択してください（例：Small、Medium、Large）。
# MAGIC     * SLA要件を満たすようにスケーリングパラメータを設定してください。
# MAGIC     * セキュリxティおよびアクセス制御の設定を確認する。
# MAGIC
# MAGIC 1. **🚨 お知らせ：関連コストのため、モデルはデプロイしません。実際の使用例では、[作成]ボタンをクリックしてendpointをプロビジョニングします。**
# MAGIC
# MAGIC **注記:** プロビジョニング済みスループットデプロイメントは、専用コンピューティングリソースがendpointに割り当てられるため、初期化に通常10～15分かかります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## デプロイ済みモデルのクエリ
# MAGIC
# MAGIC より現実的には、サービングアプリケーションから直接デプロイされたモデルをクエリできます。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### オプション1 - UI経由でのクエリ
# MAGIC
# MAGIC Databricks内でモデルを直接クエリし、**query endpoint** 機能を使用してすべてが正常に動作していることを確認できます。
# MAGIC
# MAGIC サンプルクエリ：
# MAGIC `{"messages": [{"role": "user", "content": "What are the key benefits of using Databricks for data engineering?"}]}`

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### オプション2 - AI Playgroundでデプロイ済みモデルをクエリする
# MAGIC
# MAGIC AI Playgroundでモデルをテストするには、デプロイされた`gpt_oss_20b_endpoint`モデルを選択し、チャットボックスを使用してクエリを送信します。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### オプション3 - SDKを使用してデプロイ済みモデルをクエリする
# MAGIC
# MAGIC
# MAGIC ```
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC
# MAGIC w = WorkspaceClient()
# MAGIC
# MAGIC # Sample messages to send to the model
# MAGIC messages = [
# MAGIC     {"role": "system", "content": "You are a helpful assistant."},
# MAGIC     {"role": "user", "content": "Explain the benefits of using provisioned throughput for production ML deployments."}
# MAGIC ]
# MAGIC
# MAGIC response = w.serving_endpoints.query(
# MAGIC     name="gpt_oss_20b_endpoint",  # name of the model serving endpoint
# MAGIC     messages=messages,
# MAGIC     max_tokens=200,
# MAGIC     temperature=0.7
# MAGIC )
# MAGIC
# MAGIC print(response.choices[0].message.content)
# MAGIC ```
# MAGIC
# MAGIC **💡 ヒント:** `max_tokens` および `temperature` パラメータを調整して、応答の長さと創造性を制御してください。プロビジョニングされたスループットにより、同時リクエスト量に関係なく一貫した応答時間を実現します。

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC
# MAGIC ## 結論
# MAGIC
# MAGIC この時点で、あなたは次のことができるはずです：
# MAGIC
# MAGIC * モデルデプロイメントにおいてプロビジョニング済みスループットを使用すべきタイミングを理解する。
# MAGIC * `system.ai` カタログから外部モデルを、プロビジョニングされたスループットを備えた Databricks Model Serving endpointにデプロイします。
# MAGIC * 本番環境でデプロイされたモデルのクエリと検証を行う。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>