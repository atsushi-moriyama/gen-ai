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
# MAGIC # デモ - 検索のためのVector searchの構築
# MAGIC
# MAGIC ## 概要
# MAGIC ようこそ！このデモでは、Databricksを使用してドキュメント検索のためのVector searchソリューションを構築する方法を探求します。ドキュメントチャンクをセマンティックVectorに変換し、Vector searchインデックスを作成し、高度な検索と再ランキング技術を活用して検索精度を向上させる手順を説明します。
# MAGIC
# MAGIC 実世界の検索シナリオでは、非構造化ドキュメントを検索可能なセマンティックVectorsに変換することで、より正確でコンテキストを考慮した結果を得ることができます。このワークフローにより、キーワードが完全に一致しない場合でも、関連する情報を効率的に見つけることができます。
# MAGIC
# MAGIC ## 学習目標
# MAGIC - Foundation Model APIのGTEモデルを使用してドキュメント埋め込みを計算する手順を **特定** する。
# MAGIC - SDKとUIの両方の方法を使用してVector searchインデックスを **設定** および作成する。
# MAGIC - ドキュメントパスによるフィルタリングを含む、クエリ、ハイブリッド、および全文検索方法を **実装** し比較する。
# MAGIC - 再ランキングによって検索精度を **向上** させ、検索品質への影響を理解する。
# MAGIC - 計算コスト、精度、およびインデックス更新戦略のバランスを取るためのベストプラクティスを **適用** する。
# MAGIC
# MAGIC ## 要件
# MAGIC - 事前に作成された **Vector search endpoint**。これはあらかじめ作成されています。
# MAGIC - **Serverless Compute (environment version 5)** 。適切な環境バージョンを選択するには、[こちら](https://docs.databricks.com/aws/en/compute/serverless/dependencies#-select-an-environment-version)の手順に従ってください。
# MAGIC - 必要なライブラリがサーバーレスコンピュート設定の **Dependencies** に追加されている。
# MAGIC - 埋め込み生成のためのFoundation Model APIへのアクセス。
# MAGIC - Vector searchインデックスを作成および管理するための適切な権限。

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ
# MAGIC
# MAGIC 以下のコードを実行して、必要なライブラリをインストールし、教室環境を設定します。この手順により、すべての依存関係が利用可能になり、デモのためにワークスペースが準備されます。
# MAGIC

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-03

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. ソーステーブルの準備
# MAGIC
# MAGIC Vector searchでは、ソーステーブルでチェンジデータフィード（CDF）が有効になっている必要があります。テーブルで既にこの機能が有効になっている場合は、変更を行う必要はありません。そうでない場合は、以下のように有効にできます。
# MAGIC
# MAGIC また、Vector searchインデックスを作成する際に必要となる、テーブル用の一意のIDが必要であることに注意してください。

# COMMAND ----------

# Vector search同期のためのChange Data Feedを有効化
spark.sql(f"ALTER TABLE {docs_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# テーブル構造を理解するためのサンプルデータを表示
display(spark.sql(f"SELECT * FROM {docs_table} LIMIT 5"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. ドキュメントチャンクの埋め込み計算
# MAGIC
# MAGIC 埋め込みは、セマンティックな意味を捉えるテキストの高次元vector表現であり、強力な類似性検索と検索を可能にします。Databricksでは、埋め込みにより、キーワードが正確に一致しない場合でも、コンテキスト的に関連するドキュメントチャンクを見つけることができます。
# MAGIC
# MAGIC Databricksは、埋め込み生成のために2つの主要なアプローチをサポートしています：
# MAGIC * **Managed embeddings：** Vector searchが自動的に埋め込みを計算し管理するため、セットアップとメンテナンスが簡素化されます。これはほとんどのユースケースで推奨されるアプローチです。
# MAGIC * **Manual embeddings：** 外部で埋め込みを生成し（MLflowデプロイメント、Hugging Face、OpenAI等を使用）、カラムに保存できます。大規模なデータセットの場合、Spark UDFを使用してテキストカラムの各行の埋め込みを計算できます。
# MAGIC
# MAGIC このデモでは、**managed embeddings** を使用し、Vector searchに埋め込みの計算と維持を任せます。このアプローチはワークフローを合理化し、DatabricksのVector search機能との互換性を保証します。

# COMMAND ----------

# DBTITLE 1,埋め込みの計算と表示
import mlflow.deployments

# 埋め込みモデルにアクセスするためのデプロイメントクライアントを初期化
deploy_client = mlflow.deployments.get_deploy_client("databricks")

# サンプル質問の埋め込みを生成
question = "How Generative AI impacts humans?"
response = deploy_client.predict(endpoint="databricks-gte-large-en", inputs={"input": [question]})
embeddings = [e["embedding"] for e in response.data]

# 埋め込み情報を表示
print("Embedding for question:", embeddings[0])
print("Embedding shape:", len(embeddings[0]))

# COMMAND ----------

# MAGIC %md
# MAGIC **💡 質問:** `1024`の埋め込み形状は何を意味しますか？使用している埋め込みモデルでこれを変更できますか？

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. Vector searchインデックスの作成
# MAGIC
# MAGIC 埋め込みができたので、高速で正確な検索を可能にするVector searchインデックスを作成します。Databricksは2つの主要なアプローチをサポートしています：
# MAGIC
# MAGIC - **SDK方法：** databricks-vectorsearch SDKを使用して、計算された埋め込みでインデックスを作成します。
# MAGIC - **UI方法：** Databricks UIを使用して、マネージドまたは計算された埋め込みでインデックスを作成します。
# MAGIC
# MAGIC セットアップセクションで定義された事前作成されたVector search endpointを使用します。endpoint作成の手順については、[endpointドキュメント](https://docs.databricks.com/aws/en/vector-search/create-vector-search#create-a-vector-search-endpoint-using-the-ui)を参照してください。
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. SDKによるインデックス作成
# MAGIC
# MAGIC この手順では、Databricks SDKを使用してvector searchインデックスを作成します。マネージド埋め込みを使用し、Databricksが各チャンクのvector表現を自動的に計算し維持できるようにします。
# MAGIC
# MAGIC 詳細については、[Vector Search SDKドキュメント](https://api-docs.databricks.com/python/vector-search/index.html)を参照してください。
# MAGIC
# MAGIC **注意：** インデックス更新モードは、更新要件に応じて手動または同期に設定できます。

# COMMAND ----------

# DBTITLE 1,コード: SDKを使用したインデックス作成
from databricks.vector_search.client import VectorSearchClient

# vector searchクライアントを初期化
vsc = VectorSearchClient(disable_notice=True)

# 三層命名規則を使用してインデックス名を定義
index_name = f"{catalog}.{schema}.docs_chunked_index"

# Delta Syncでマネージド埋め込みを使用してインデックスを作成
vsc.create_delta_sync_index_and_wait(
    endpoint_name=vector_search_endpoint,
    index_name=index_name,
    source_table_name=docs_table,
    primary_key='id',
    embedding_source_column="chunk",
    embedding_model_endpoint_name="databricks-gte-large-en",
    pipeline_type="TRIGGERED",
)
print(f"Index '{index_name}' created for table '{docs_table}' using endpoint '{vector_search_endpoint}'.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. UIによるインデックス作成（オプション）
# MAGIC
# MAGIC Databricks UIを使用してvector searchインデックスを作成することもできます。これはマネージドと計算された埋め込みの両方をサポートします。この方法は、グラフィカルインターフェースを好むユーザーや、マネージド埋め込みworkflowsを活用したいユーザーに推奨されます。
# MAGIC
# MAGIC 手順については、[Vector Search UIドキュメント](https://docs.databricks.com/aws/en/vector-search/create-vector-search#create-index-using-the-ui)を参照してください。
# MAGIC
# MAGIC 1. 左サイドバーで **Catalog** をクリックしてCatalog Explorerを開きます。
# MAGIC 2. Deltaテーブルを見つけて選択します。
# MAGIC 3. **Create**（右上）をクリックし、**Vector search index** を選択します。
# MAGIC 4. ダイアログで以下を設定します：
# MAGIC    * **Name：** 三層名（`<catalog>.<schema>.<name>`）を入力します。ドロップダウンからカタログとスキーマを選択し、テキストボックスに名前を入力します。
# MAGIC    * **Primary key：** 一意のIDカラムを選択します。
# MAGIC    * **Columns to sync：** （標準endpointsのみ）含めるカラムを選択するか、空白のままですべてを同期します。
# MAGIC    * **Embedding source：** 埋め込みを計算する（テキストカラムとモデルを選択）か、既存の埋め込みカラムを使用するかを選択します。
# MAGIC    * **Sync computed embeddings：** 生成された埋め込みをテーブルに保存するかを切り替えます。
# MAGIC    * **Vector search endpoint：** endpointを選択します。
# MAGIC    * **Sync mode：** *継続的*（自動同期）または *トリガー*（手動同期）を選択します。ストレージ最適化エンドポイントは*トリガー*のみをサポートします。
# MAGIC 5. **Create** をクリックし、インデックス作成の進行状況を監視します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. 検索方法：クエリ、ハイブリッド、および全文
# MAGIC
# MAGIC インデックスが配置されたので、さまざまな方法を使用して検索を実行できます：
# MAGIC
# MAGIC - **Query Search：** 埋め込みを使用してセマンティックに類似したチャンクを見つけます。
# MAGIC - **Hybrid Search：** セマンティックとキーワードベースの検索を組み合わせて関連性を向上させます。
# MAGIC - **Full-Text Search：** 正確なキーワードマッチに基づいてチャンクを取得します。
# MAGIC
# MAGIC また、`path` フィールドで結果をフィルタリングして特定のドキュメントをターゲットにする方法も実演します。

# COMMAND ----------

# 検索を実行するためのVector searchインデックスを取得
index = vsc.get_index(index_name=index_name)
print(index.describe())

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. クエリ検索：類似性検索
# MAGIC
# MAGIC この手順では、vector searchインデックスを使用してセマンティック検索を実行します。この方法は、正確なキーワードが一致しない場合でも、クエリとコンテキスト的に類似したドキュメントチャンクを取得します。キーワードではなく意味に基づいて関連情報を見つけるためにこのアプローチを使用します。

# COMMAND ----------

# DBTITLE 1,コード: クエリ検索：セマンティック検索（Python）
query_text = "How does the Orion system prevent overheating during continuous operation?"
results = index.similarity_search(
    query_text=query_text,
    columns=["path", "chunk"],
    num_results=3
)
display(results)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. ハイブリッド検索：セマンティック + キーワード
# MAGIC
# MAGIC ハイブリッド検索は、セマンティック類似性とキーワードマッチングを組み合わせます。このアプローチは、コンテキスト的な関連性と正確なキーワードヒットのバランスを取り、検索結果の精度を向上させたい場合に有用です。

# COMMAND ----------

# DBTITLE 1,コード: ハイブリッド検索：セマンティック + キーワード（Python）
query_text = "Explain safety verification under ISO 13849-1."
results_hybrid = index.similarity_search(
    query_text=query_text,
    columns=["path", "chunk"],
    query_type="hybrid",
    num_results=5
)
display(results_hybrid)

# COMMAND ----------

# MAGIC %md
# MAGIC モデルの埋め込みは、安全性と検証にセマンティックに焦点を当てる可能性がありますが、埋め込みが主に一般的な英語テキストでトレーニングされている場合、特定の標準参照を見逃す可能性があります。
# MAGIC
# MAGIC **"ISO 13849-1"** でのキーワードフィルタリングにより、コンプライアンス標準に言及するチャンクのみが確実に取得されます。最初の結果には **"ISO 13849-1"** が含まれているが、他の結果には含まれていないことに注意してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 全文検索：キーワードのみ
# MAGIC
# MAGIC 全文検索は、正確なキーワードマッチのみに基づいてドキュメントチャンクを取得します。検索用語に対して非常に正確で文字通りの結果が必要な場合にこの方法を使用します。
# MAGIC
# MAGIC **🚨 重要：** 全文検索は **現在ベータ版** であり、使用前にワークスペースで有効にする必要があります。この機能を有効にした後、以下のコードセルを**unskip** できます。**プレビュー** 機能を有効にする手順については、[このドキュメントページ](https://docs.databricks.com/aws/en/admin/workspace-settings/manage-previews#-manage-account-level-previews)を確認してください。

# COMMAND ----------

# DBTITLE 1,コード: 全文検索
# MAGIC %skip
# MAGIC query_text = "PID coefficients"
# MAGIC results_fulltext = index.similarity_search(
# MAGIC     query_text=query_text,
# MAGIC     columns=["path", "chunk"],
# MAGIC     query_type="FULL_TEXT",
# MAGIC     num_results=5
# MAGIC )
# MAGIC display(results_fulltext)
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. パスによるフィルター：特定のドキュメントをターゲット
# MAGIC
# MAGIC フィルタリングを使用して、特定のドキュメントの結果を返すことができます。例えば、`path` フィールドで検索結果をフィルタリングして、特定のドキュメントのみをターゲットにできます。これは、データセット内の特定のファイルやドキュメントに検索を制限したい場合に有用です。
# MAGIC
# MAGIC ここでは `LIKE` フィルターを使用します。フィルタリングは文字列内の空白で区切られたトークンに一致することに注意してください。サポートされている他のフィルターについては、[ドキュメント](https://docs.databricks.com/aws/en/vector-search/query-vector-search)を確認してください。

# COMMAND ----------

# DBTITLE 1,コード: パスによるフィルター
query_text = "How does the Orion system prevent overheating during continuous operation?"
filtered_results = index.similarity_search(
    query_text=query_text,
    columns=["path", "chunk"],
    filters={"path LIKE" : "dbfs:/Volumes/main/default/documents/03_Orion_Motion_Controller_Firmware_Guide_v6.pdf"}, # TODO: 異なるカタログとスキーマを使用した場合はパスを変更してください
    num_results=3
)

display(filtered_results)

# COMMAND ----------

# MAGIC %md
# MAGIC **💡 追加のフィルター例：**
# MAGIC
# MAGIC Vector searchでは様々なフィルタータイプを使用できます：
# MAGIC
# MAGIC ```python
# MAGIC # 正確なパスマッチによるフィルター
# MAGIC filters={"path NOT": "specific/document/path.pdf"}
# MAGIC
# MAGIC # 数値範囲によるフィルター（数値メタデータがある場合）
# MAGIC filters={"page_number >": 10, "page_number <": 50}
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. 再ランキングによる精度の向上
# MAGIC
# MAGIC 埋め込みは意味的に類似したコンテンツを見つけるのに強力ですが、時には意味は近いがコンテキストが弱い結果を返すことがあります。再ランキングは、よりコンテキストを考慮したモデルや追加のシグナルを使用してトップ結果を再評価することで精度を向上させるのに役立ちます。
# MAGIC
# MAGIC **なぜ再ランキングするのか？**
# MAGIC - 埋め込みベースの検索は、意味的に類似しているがコンテキスト的に無関係なチャンクを表面化する可能性があります。
# MAGIC - 再ランキングは、しばしばクロスエンコーダーやLLMを使用して、二次スコアリング手順を適用し、最も関連性の高い結果を優先します。
# MAGIC - Databricksでは、組み込みの再ランカーを使用して類似性検索からのトップN結果を再スコアリングし並び替えることができ、より深いコンテキスト理解を活用します。
# MAGIC - これにより、特に微妙なクエリや重要なユースケースにおいて、最終出力の品質が向上します。
# MAGIC
# MAGIC **トレードオフ：** 再ランキングは計算コストを増加させますが、高価値クエリの精度を大幅に向上させることができます。パフォーマンスと精度のバランスを取るために、再ランキングを選択的に使用してください。

# COMMAND ----------

# DBTITLE 1,コード: 検索結果の再ランキング例
# 例：DatabricksRerankerを使用してセマンティック検索からのトップN結果を再ランキング

from databricks.vector_search.reranker import DatabricksReranker

query_text = "How does the Orion system prevent overheating during continuous operation?"
results_reranked = index.similarity_search(
    query_text=query_text,
    columns=["path", "chunk"],
    num_results=5,
    reranker=DatabricksReranker(columns_to_rerank=["chunk"])
)

display(results_reranked)

# COMMAND ----------

# MAGIC %md
# MAGIC **💡 質問：** これらの結果をこのセクションの最初の類似性検索で返された結果と比較してください。改善が見られますか？

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. Vector searchのベストプラクティス
# MAGIC
# MAGIC 1. **可能な限り埋め込み次元数を最小化する**
# MAGIC    高次元の埋め込み（例：1024-1536）はより多くのニュアンスを捉える可能性がありますが、レイテンシを増加させ、スループットを減少させます。検索品質を保持する最低次元を選択してください。
# MAGIC    *例：* 768次元モデルと384次元モデルをテストし、類似した検索精度を見つけた場合、より高速なクエリのために384次元バリアントを選択すべきです。
# MAGIC
# MAGIC 2. **クエリごとの`num_results`を適度に保つ（例：10-100）**
# MAGIC    あまりに多くの結果を要求すると、スキャンとレイテンシが増加します；ドキュメントではユースケースが正当化しない限り、この範囲に留まることを推奨しています。
# MAGIC    *例：* `num_results=5000` ではなく、デフォルトで `num_results=50` を使用してください。
# MAGIC
# MAGIC 3. **正しいendpointSKUを選択し、インデックスサイズを適切に設定する**
# MAGIC    Vector数、次元、クエリレイテンシ、およびコストに基づいて「標準」と「ストレージ最適化」endpointsから選択します。また、最適なレイテンシのために、インデックスサイズがVector searchユニットの能力内に留まることを確認してください。
# MAGIC    *例：* <768次元のVectorが200万未満の場合は標準SKUを使用し、> 1,000万を超える場合はストレージ最適化SKUをご検討ください。
# MAGIC
# MAGIC 4. **フィルターとメタデータを使用して検索範囲を狭める**
# MAGIC    メタデータ（例：ドキュメントタイプ、パスプレフィックス、ソース）を付加することで、`filters` を介して検索を制限し、無関係なチャンクの取得を避け、関連性とパフォーマンスを向上させることができます。
# MAGIC    *例：* 「メンテナンス間隔」クエリでマニュアルのみが検索されるように `"document_type":"manual"` でフィルタリングします。
# MAGIC
# MAGIC 5. **速度のためにANN検索を優先し、ドメインキーワードが重要な場合はハイブリッド（Vector + キーワード）を使用する**
# MAGIC    Approximate Nearest Neighbor（ANN）検索は最高のQPSと最低のレイテンシを提供します；ハイブリッド検索は、キーワード関連性（例：法的標準コード）が重要な場合にのみ使用すべきです。
# MAGIC    *例：* 一般的な「センサーの再校正方法」クエリにはANNを使用し、「ISO 13849-1」のような特定の標準に一致する必要があるクエリにはハイブリッドを使用します。
# MAGIC
# MAGIC その他のベストプラクティスについては、[Databricks Vector Searchドキュメント](https://docs.databricks.com/aws/en/generative-ai/vector-search-best-practices)を参照してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## G. まとめ
# MAGIC
# MAGIC このデモでは、Databricksでドキュメント検索のためのVector searchソリューションを構築するエンドツーエンドのプロセスを探求しました：
# MAGIC
# MAGIC * Foundation Model APIのGTEモデルを使用してドキュメントチャンクのセマンティック埋め込みを計算しました。
# MAGIC * 事前作成されたendpointを活用して、SDKとUIの両方の方法を使用してVector searchインデックスを作成しました。
# MAGIC * ドキュメントパスによるフィルタリングを含む、クエリ、ハイブリッド、および全文検索方法を実演しました。
# MAGIC * 再ランキングによって検索精度を向上させ、埋め込みが意味的に近いがコンテキスト的に弱いマッチを返す場合のその価値を強調しました。
# MAGIC * 計算コスト、精度、埋め込み次元数、チャンキング戦略、およびインデックス更新モードのバランスを取るためのベストプラクティスを確認しました。
# MAGIC
# MAGIC これらの手順とベストプラクティスに従うことで、データとビジネスニーズに合わせてスケールする堅牢で高精度な検索システムを実装できます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>