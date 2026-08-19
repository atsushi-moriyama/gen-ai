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
# MAGIC # デモ - エージェントセットアップ
# MAGIC **概要**
# MAGIC
# MAGIC このデモでは、ユーザー固有の環境変数と `./artifacts` フォルダーに配置されたPythonコードを使用したカスタムエージェントのセットアップに焦点を当てます。エージェントアプリケーションのライフサイクルのこの段階では、評価の準備が整っており、このノートブックはUnity Catalogに既に登録されたエージェントを持つチェックポイントとして機能します。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このデモの終了時には、以下ができるようになります：
# MAGIC - エージェント評価に必要なDatabricks環境とクラスルームアセットを設定する
# MAGIC - 名前とエイリアスでUnity Catalogに登録されたエージェントをロードする
# MAGIC - エージェントとやり取りしてトレースを生成し、Unity Catalogでそれらのトレースを特定する

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必須 - サーバーレスコンピュートを選択
# MAGIC
# MAGIC このノートブックでセルを実行する前に、ノートブックを **サーバーレスコンピュート** にアタッチしてください。
# MAGIC
# MAGIC **注意：** このデモは **サーバーレス（バージョン5）** でテストされています。  
# MAGIC サーバーレスバージョンを確認または変更するには、サーバーレス依存関係に関するDatabricksドキュメントを参照してください。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### コンピュート要件
# MAGIC
# MAGIC このコースはサーバーレスコンピュートで実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモではサーバーレスコンピュートはバージョン5である必要があります。** 正しいバージョンを使用していることを確認するには、[ノートブックのサーバーレスバージョンの表示と変更に関するこのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)を参照してください。
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">必須 - サーバーレスコンピュートを選択</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">続行する前に、このノートブックをサーバーレスコンピュートリソースにアタッチする必要があります。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### クラスルームセットアップ
# MAGIC
# MAGIC このコースの作業環境を設定するために、以下のセルを実行してください。
# MAGIC
# MAGIC このセットアップでは以下を行います：
# MAGIC - `DA` オブジェクト（Databricks Academyヘルパー）を初期化する
# MAGIC - **デフォルトカタログ** と **スキーマ** を設定する
# MAGIC - このデモに必要なサポート設定をプロビジョニングする
# MAGIC
# MAGIC **注意：** `DA` オブジェクトはDatabricks Academyコースでのみ利用可能です

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-1

# COMMAND ----------

# MAGIC %md
# MAGIC **その他の補足事項：**
# MAGIC
# MAGIC このデモ全体を通して、`DA` オブジェクトを参照します。Databricks Academyが提供するこのオブジェクトには、ユーザー名、カタログ名、スキーマ名、作業ディレクトリ、データセットの場所などの変数が含まれています。以下のコードブロックを実行して、これらの詳細を表示してください：

# COMMAND ----------

print(f"Username:          {DA.username}")
print(f"Catalog Name:      {DA.catalog_name}")
print(f"Schema Name:       {DA.schema_name}")
print(f"Working Directory: {DA.paths.working_dir}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1 - エージェントのインポートとMLflowトレースの表示
# MAGIC
# MAGIC このセクションでは、MLflowトレーシングでインストルメント化されたエージェントをインポートしてテストします。エージェントはSQL関数を組み合わせて、サンフランシスコのAirbnbリスティングに関する包括的な回答を提供します。
# MAGIC
# MAGIC MLflowトレーシングは、取得操作、関数呼び出し、LLMインタラクションを含むエージェントの実行フローを自動的にキャプチャします。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### エージェントのインポート
# MAGIC
# MAGIC ここでは、`demo_setup.load_agent()` を使用してこのデモのセットアップスクリプトの一部として作成されたUnity Catalogパスとエイリアスを使用してモデルをロードします。
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #0d47a1; font-size: 1.1em;">シンプルなエージェントを使用しています</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">このデモで構築され、他のデモ/ラボで使用されるカスタムエージェントは、実際にはUnity Catalogに登録されたUDFを使用する<strong>ツール呼び出しエージェント</strong>です。エージェントには様々なツールがありえますが、それは現在の目標ではありません。ここでは評価の基本を理解することに焦点を当てます。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

agent = demo_setup.load_agent("airbnb_eval_agent")

# COMMAND ----------

# MAGIC %md
# MAGIC ### サンプル質問
# MAGIC
# MAGIC エージェントが動作するようになったので、`airbnb_agent.py` で定義された `predict()` メソッドを使用していくつかの質問を渡してみましょう。まず、エージェントに期待されるペイロードを送信するために使用できるヘルパー関数を作成しましょう。

# COMMAND ----------

def agent_payload(question: str):
    return [{"input": [{"role": "user", "content": question}]}]

# COMMAND ----------

agent.predict(agent_payload("What tools do you have available?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### トレースの検査
# MAGIC
# MAGIC 上記の出力に基づいて、エージェントがアクセスできるツールを確認できます。次に、いくつかのツール呼び出しを呼び出す質問をしてみましょう。具体的には、次の質問はエージェントに以下の両方を使用するように促します：
# MAGIC
# MAGIC 1. `avg_neigh_price`
# MAGIC 2. `cnt_by_room_type`
# MAGIC
# MAGIC 以下のスクリーンショットは、次のセルを実行した際の出力の例であり、期待される内容を示しています。上記で定義されたツールが呼び出されていることに注意してください。
# MAGIC
# MAGIC ![mlflow-toolcall.png](../Includes/images/built-in agents with mlflow/mlflow-toolcall.png "mlflow-toolcall.png")

# COMMAND ----------

agent.predict(agent_payload("Can you tell me what the average price is in Mission? Also, what's the number of listings for that neighborhood that have private rooms?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート2 - Unity Catalogでのトレースの検査
# MAGIC
# MAGIC **Catalog Explorer** に移動し、**airbnb_eval_agent** を検索してください。そこで、エイリアス **@champion** を持つモデル（少なくとも **バージョン1**）を見つけることができます。それをクリックして **Traces** タブに移動してください。そこで、上記で送信した同じ2つのリクエストを見つけることができます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC - エージェントがUnity Catalogに登録され、`mlflow.pyfunc.load_model()` を使用してロードできるようになりました
# MAGIC - MLflowトレーシングがすべてのエージェントのやり取りを自動的にキャプチャし、評価のための貴重なデータを提供します
# MAGIC - エージェントは複数のツール（SQL関数）を正常に組み合わせて包括的な回答を提供します
# MAGIC - すべてのトレースは、モニタリングとデバッグのためにUnity Catalogインターフェースを通じてアクセス可能です
# MAGIC
# MAGIC ### 次のステップ
# MAGIC
# MAGIC エージェントが適切に設定され登録されたので、このシリーズの次のノートブックに進む準備が整いました。そこでは、エージェントのパフォーマンスを評価し、トレースから評価データセットを作成し、包括的なテスト戦略を実装する方法を学びます。
# MAGIC
# MAGIC 今後のノートブックでは、このデモで使用した `demo_setup()` ヘルパー関数ではなく、`mlflow.pyfunc.load_model()` を使用してエージェントを直接ロードすることを覚えておいてください。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>