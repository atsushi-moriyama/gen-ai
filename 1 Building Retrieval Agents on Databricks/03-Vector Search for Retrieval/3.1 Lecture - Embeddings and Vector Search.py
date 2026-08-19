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
# MAGIC # エンベディングとVector Search
# MAGIC
# MAGIC ## はじめに
# MAGIC
# MAGIC 検索拡張生成（RAG）システムの効果は、一つの重要な要因に依存します：検索パイプラインの品質です。関連する情報を検索する前に、まず非構造化テキストを **embedding** と呼ばれる数値表現に変換し、それらを専用の **vector database** に保存する必要があります。このレッスンでは、**embedding model** がテキストをvectorsに変換する方法の理解から、効率的な検索のための **vector類似性アルゴリズム** の活用まで、完全なデータ準備ライフサイクルを探索します。また、ハイブリッド検索やリランキングなど、結果の品質を大幅に改善する高度な検索技術についても検討します。最後に、**Mosaic AI Vector Search** がDatabricks Data Intelligence Platform内でこれらのコンポーネントをどのように統合し、安全でサーバーレスなvectorデータベースソリューションを提供するかを発見します。
# MAGIC
# MAGIC ## レッスンの目標
# MAGIC
# MAGIC このレッスンの終了時には、以下のことができるようになります：
# MAGIC
# MAGIC * エンベディングvectorの主要特性を特定し、適切なエンベディングモデルを選択するための基準を評価する。
# MAGIC * 類似性検索、全文検索、ハイブリッド検索の手法を比較し、最適な検索戦略を決定する。
# MAGIC * 本番環境における完全検索と近似検索アルゴリズムのトレードオフを分析する。
# MAGIC * リランキングがRAGアプリケーションにおいてコンテキストの精度を向上させ、幻覚を減少させる方法を説明する。
# MAGIC * Mosaic AI Vector Searchの取り込みモード、ガバナンスモデル、アーキテクチャ上の利点を説明する。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. エンベディングの基本概念
# MAGIC
# MAGIC このセクションでは、エンベディング（現代の情報検索の数学的基盤）を扱うために必要な基礎知識を確立します。**非構造化テキストがvector表現にどのように変換されるか** を探索し、特定のドメインに適したモデルを選択することがなぜ重要なのかを検討し、クエリとドキュメント空間の間の整合性の重要性を理解します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. エンベディングの定義
# MAGIC
# MAGIC エンベディングは、通常ディープラーニングモデルによって生成されるコンテンツの数値表現です。これらのモデルは、高次元の非構造化データ（テキストなど）を低次元のvector（意味的意味を捉える浮動小数点数の配列）に変換します。エンベディングを強力にする主要な特性は、類似した概念をvector空間内で近くにマッピングする能力です。関連する意味を持つ単語やフレーズは互いに近くにクラスタ化され、システムが正確なキーワードマッチがなくても概念的関係を特定できるようになります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. マルチモーダルコンテキスト
# MAGIC
# MAGIC **このレッスンは非構造化テキストに焦点を当てていますが**、エンベディングは単語をはるかに超えて拡張されることは言及する価値があります。GPT-4oやGemini 1.5などのマルチモーダルモデルは、画像、音声、テキストを統一されたvector空間に処理・エンベディングできます。この機能により、クロスモーダル検索シナリオが可能になります。テキストクエリを使用して意味的に関連する画像を見つけたり、書面での説明で音声コンテンツを検索したりすることを想像してみてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. エンベディングモデル
# MAGIC
# MAGIC エンベディングモデルは、高次元の非構造化データ（テキスト、画像、音声など）を低次元の数値vectorsに変換するように設計された専用の機械学習モデル（通常はディープニューラルネットワーク）です。**これを、人間が読める内容を機械が読める浮動小数点数のリストに変換する翻訳者として考えてください。類似した意味を持つ入力が数学的に近いベクトルを生成するようにします。**
# MAGIC
# MAGIC 適切なエンベディングモデルの選択は、検索品質に影響を与える重要なアーキテクチャ上の決定です。以下の主要な要因を考慮してください：
# MAGIC
# MAGIC - **語彙サイズとドメイン：** 一部のモデルは一般的なウェブテキストで訓練されていますが、他のモデルは金融、医学、法的文書などの特定のドメインに特化しています。ドメイン特化モデルは、専門コンテンツに対してしばしば優れた結果を提供します。
# MAGIC - **コンテキストウィンドウ：** すべてのモデルには最大入力トークン制限があります。この制限を超えるテキストは切り捨てられるか無視されるため、長いドキュメントには効果的なチャンキング戦略が不可欠です。
# MAGIC - **次元数：** 高次元ベクトル（より大きな配列）はより多くのニュアンスと意味的詳細を捉えますが、ストレージコストと検索レイテンシが増加します。精度のニーズと運用上の制約のバランスを取ってください。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/03-vectorization.png" alt="Vectorization process illustrated" /> -->
# MAGIC ![03-vectorization](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/03-vectorization.png)
# MAGIC
# MAGIC *図1. この図は、データチャンクがエンベディングモデルによって処理されてvectorsを生成する方法を示しています。入力データがモデルのコンテキストウィンドウ制限を超える場合、超過したコンテンツは省略され、結果として得られるエンベディングの完全性に影響を与える可能性があります。*

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. エンベディングの整合性
# MAGIC
# MAGIC 検索が効果的に機能するためには、エンベディングモデルがソースドキュメントとユーザークエリの両方を同じvector空間で表現する必要があります。モデルが主に長文ドキュメントで訓練されているが、アプリケーションが短い非公式なクエリを使用している場合、vector表現がうまく整合せず、検索結果が悪くなる可能性があります。ベストプラクティスは簡単です：**ドキュメントのインデックス化とクエリの処理の両方に同じエンベディングモデルを使用してください**。これにより、それらが同じ数学的空間に存在し、意味のある比較ができることが保証されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. Vectorストアと検索メカニズム
# MAGIC
# MAGIC 非構造化データをエンベディングに変換したら、高次元vectorを処理し、効率的な類似性クエリを実行できる専用ストレージが必要です。このセクションでは、vectorデータベースの特徴的なアーキテクチャと、従来のリレーショナルシステムとの違いを検討します。また、大規模で意味的に関連する情報を検索するために使用される検索アルゴリズムとメトリクスについても探索します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. Vectorデータベースの役割
# MAGIC
# MAGIC Vectorデータベースは、高次元Vectorを効率的に保存・検索するために特別に構築されています。完全一致を目的とした従来のデータベース（SQL WHERE句を考えてください）とは異なり、Vectorデータベースは類似性検索に優れています。つまり、同一ではなく概念的に関連するアイテムを見つけることです。Vector操作に最適化された専用のインデックス構造を導入しながら、作成・読み取り・更新・削除（CRUD）操作などの標準的なデータベース機能を維持しています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 検索手法
# MAGIC
# MAGIC 異なる検索手法は、異なる検索ニーズに対応します：
# MAGIC
# MAGIC - **類似性検索：** この手法は、正確な単語マッチングではなく意味的相関に基づいてコンテンツを検索します。「不安への対処方法」のような自然言語クエリが、「PTSDへの対処」や「ストレス管理」などの異なる用語を使用している可能性がある関連結果を表示することを可能にします。
# MAGIC - **全文検索：** この従来のアプローチはキーワードマッチングに依存します。部品番号、製品コード、固有名詞などの特定の用語を見つけるのに優れていますが、意味的意図を捉えたり同義語を認識したりすることはできません。
# MAGIC - **ハイブリッド検索：** この強力なアプローチは、Vector類似性検索とキーワードベース検索を組み合わせます。意味的理解と正確なキーワードマッチングの両方を活用することで、ハイブリッド検索は通常、どちらの手法単独よりも高い検索精度を提供します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 距離と類似性メトリクス
# MAGIC
# MAGIC 2つのVectorsがどの程度「類似している」かを判定するために、2つの主要なタイプのメトリクス（**distance metrics** と **similarity metrics**）を使用します。それぞれ異なる検索シナリオに適しています。**Distance metrics** は、Vectors空間内で2つのベクトルがどの程度離れているかを定量化したい場合に使用されます。クラスタリング、外れ値検出、または大きさが重要な場合に理想的です。**similarity metrics** は、2つのvectorsが方向的にどの程度密接に整合しているかを知りたい場合に使用されます。意味検索、ドキュメント検索、および意味がスケールよりも重要なほとんどのNLPアプリケーションに理想的です。
# MAGIC
# MAGIC **distance metrics**  
# MAGIC - **Euclidean Distance（L2）：** Vector空間内の2点間の直線距離を測定します。*低い*値は、Vectorsがより類似していることを意味します。クラスタリングや異常検出など、すべての次元における絶対的な差異を重視する場合に使用します。
# MAGIC - **Manhattan Distance（L1）：** すべての次元における絶対差の合計です。*低い*値は、Vectorがより近いことを意味します。グリッドベースやスパースデータなど、各軸に沿った差異が等しく重要な場合に有用です。
# MAGIC
# MAGIC **Similarity Metrics**  
# MAGIC - **Cosine Similarity：** 2つのVectors間の角度のコサインを測定します。*高い*スコアは、より大きな類似性を意味します。これは、方向（意味的意味）に焦点を当て、大きさではないため、テキストエンベディングで最も人気のあるメトリクスです。ドキュメントの長さやスケールの違いに対して堅牢です。
# MAGIC
# MAGIC
# MAGIC <!-- <img src="../Includes/images/03-vector-similarities.png" alt="Distance and similarity metrics" /> -->
# MAGIC ![03-vector-similarities](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/03-vector-similarities.png)
# MAGIC
# MAGIC *図2. この図は、上記にリストされた距離メトリクスと類似性メトリクスを視覚化しています*

# COMMAND ----------

# MAGIC %md
# MAGIC ### B4. 検索戦略
# MAGIC
# MAGIC 2つの主要な戦略が精度とパフォーマンスのバランスを取ります：
# MAGIC
# MAGIC - **K-Nearest Neighbors (KNN)：** クエリvectorとデータベース内の *すべての* vector間の距離を計算する完全検索手法です。高精度ですが、計算コストが高く、大規模なデータセットにはスケールしません。数百万のドキュメントに対してクエリを一つずつ比較することを想像してみてください。
# MAGIC - **Approximate Nearest Neighbors (ANN)：** 劇的な速度向上のために少量の精度を犠牲にする戦略です。ANNは、**HNSW**（階層ナビゲート可能スモールワールド）や **FAISS**（Facebook AI類似性検索）などの洗練されたインデックスアルゴリズムを使用してvector空間を効率的にナビゲートし、高度に関連する結果を見つけながらvectorsのサブセットのみをチェックします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 精度、品質、リランキング
# MAGIC
# MAGIC Vectorデータベースは意味的に類似したコンテンツを見つけるための強力なメカニズムを提供しますが、限界がないわけではありません。このセクションでは、エンベディング品質のニュアンスと、数学的類似性と真の意味的関連性の間の潜在的なギャップについて説明します。また、検索後の重要なステップとして結果を洗練し、言語モデルに提供されるコンテキストの精度を向上させるリランキングについても紹介します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. エンベディング品質と限界
# MAGIC
# MAGIC ここに重要な洞察があります：**類似性は意味的関連性と等しくありません**。ドキュメントは、vector空間内でクエリに数学的に近くても、事実的に無関係または文脈的に不適切である可能性があります。エンベディング品質は、モデル、その訓練データ、および特定のドメインとの整合性に大きく依存します。不適切に準備されたデータや、モデルの訓練コーパスとアプリケーションのコンテンツ間の不一致は、検索パフォーマンスの低下と情報の「紛失」につながる可能性があります。
# MAGIC
# MAGIC もう一つの一般的なシナリオは、類似性検索のすべての結果を使用するのではなく、ドキュメントのサブセットを選択することです。トークン制約や処理コストのために文書数を制限する必要がある場合、最も関連性の高いドキュメントが上位に来るようにしたいでしょう。ここでリランキングが不可欠になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. リランキングプロセス
# MAGIC
# MAGIC 初期検索の精度ギャップを埋めるために、パイプラインに **Reranker** を追加します：
# MAGIC
# MAGIC 1. **初期検索：** Vectorストアが高速ANNアルゴリズムを使用して候補ドキュメントの幅広いセット（通常上位20〜50）を検索します。
# MAGIC 1. **リランキング：** 専用モデル（多くの場合Cross-Encoder）が、特定のクエリに対する各候補ドキュメントの実際の関連性を詳細に評価し、それらの関係を考慮します。
# MAGIC 1. **再順序付け：** リランカーの関連性スコアに基づいてドキュメントが再ソートされ、言語モデルが処理する最も適切な情報が上位に配置されます。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/03-reranking.png" alt="Reranking process" width="500" /> -->
# MAGIC ![03-reranking](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/03-reranking.png)
# MAGIC
# MAGIC *図3. この図はリランキングプロセスの動作を示しています*

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. 利点とトレードオフ
# MAGIC
# MAGIC リランキングは重要な考慮事項をもたらします：
# MAGIC
# MAGIC - **利点：** リランキングは言語モデルに提供されるコンテキストの精度を大幅に向上させ、幻覚を直接的に減少させ、応答品質を改善します。初期検索結果を洗練することで、最も関連性の高い情報が生成段階に到達することを保証します。
# MAGIC - **トレードオフ：** リランカーを追加すると、検索パイプラインのレイテンシとコストの両方が増加します。リランキングモデルは、クエリと候補ドキュメントをリアルタイムで処理する必要があり、計算オーバーヘッドが追加されます。特定の使用ケースに対して、これらのコストと品質改善のバランスを取ってください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. Mosaic AI Vector Search - 機能とアーキテクチャ
# MAGIC
# MAGIC 堅牢なVectorデータベースインフラストラクチャの実装は複雑になる可能性がありますが、DatabricksはMosaic AI Vector Searchでこのプロセスを簡素化します。このセクションでは、サービスのアーキテクチャを探索し、自動データ同期のためのDelta Lakeとのシームレスな統合を強調します。また、Unity Catalogの下での統一ガバナンスモデルについても検討し、Vectorインデックスへの安全で管理されたアクセスを確保します。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/03-vector-search-components.png" alt="Mosaic AI Vector Search components" /> -->
# MAGIC ![03-vector-search-components](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/03-vector-search-components.png)
# MAGIC
# MAGIC *図4. この図はMosaic AI Vector Searchの主要コンポーネントを示しています*

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 製品概要
# MAGIC
# MAGIC **Mosaic AI Vector Search** は、**Databricks Lakehouse内に直接統合されたvectorデータベースソリューション** です。このスケーラブルで低レイテンシのサービスは、データのvector表現をメタデータと一緒に保存し、REST APIとPythonクライアントを通じてリアルタイム類似性検索を可能にします。RAGアプリケーションの検索を最適化するために特別に構築されており、別個のVectorデータベースインフラストラクチャを管理する必要を排除します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. Delta同期とインデックス化
# MAGIC
# MAGIC Mosaic AI Vector Searchの最も強力な機能の一つは、**Delta Lake** との密接な統合です。**Delta Sync API** を通じて、VectorインデックスはソースDeltaテーブルと自動的に同期します。ソーステーブルでデータを追加、更新、削除すると、Vectorインデックスが自動的に更新され、手動介入なしに検索システムが常に最新のデータを反映することを保証します。これにより、エンベディングをソースデータと同期させる運用負担が排除されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 管理と取り込みモード
# MAGIC
# MAGIC Mosaic AI Vector Searchは、エンベディングの取り込みと管理のための3つの柔軟なアプローチを提供し、ニーズに適した制御レベルを選択できます：
# MAGIC
# MAGIC 1. **管理されたエンベディング（Delta同期）：** 生のテキストを含むソースDeltaテーブルを提供すると、Databricksが残りを処理します。システムは設定された **Mosaic AI Model Serving** エンドポイント（Foundation Model APIなど）を使用してエンベディングを自動的に計算し、新しいデータを処理し、インデックスを更新します。エンベディングパイプラインを管理する必要がありません。
# MAGIC
# MAGIC 1. **自己管理エンベディング（Delta同期）：** 独自のカスタムパイプラインを使用してエンベディングを計算し、Deltaテーブルに保存します。Vector Searchインデックスはこのテーブルと同期し、提供する事前計算されたVectorsをインデックス化します。これにより、自動同期の恩恵を受けながら、エンベディングプロセスを完全に制御できます。
# MAGIC
# MAGIC 1. **直接アクセスCRUD API：** REST APIまたはPython SDKを使用してVector Searchインデックスと直接やり取りできます。これにより、基盤となるDeltaテーブル同期に依存することなく、Vectorsとメタデータを直接挿入、更新、削除できます。リアルタイムアプリケーションやカスタムworkflowsに理想的です。
# MAGIC
# MAGIC
# MAGIC <!-- <img src="../Includes/images/03-vector-search-managed-embeddings.png" alt="Mosaic AI Vector Search managed embeddings method" /> -->
# MAGIC ![03-vector-search-managed-embeddings](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/03-vector-search-managed-embeddings.png)
# MAGIC
# MAGIC *図5. この図は、自動同期を伴うVector Search管理エンベディングの動作を示しています。*

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. ガバナンスとアクセス制御
# MAGIC
# MAGIC Mosaic AI Vector Searchは **Unity Catalog** によって管理され、**データとAI資産の統一セキュリティモデル** を提供します。Vector Searchで作成されたインデックスは、Unity Catalog内でセキュア可能なオブジェクトとして表示され、管理者がインデックスレベルで詳細なアクセス制御リスト（ACL）を強制できます。これにより、承認されたユーザーとアプリケーションのみがVectorデータをクエリまたは変更でき、データプラットフォーム全体で一貫したセキュリティポリシーを維持できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. まとめ
# MAGIC
# MAGIC このレッスンでは、RAGシステムにおける検索のためのデータ準備の完全なライフサイクルを探索しました。**embeddings** を非構造化テキストと機械読み取り可能vectors間の重要な橋渡しとして定義し、モデル選択が特定のドメインとクエリパターンに整合する必要があることを強調しました。**Vector databases** のメカニズムを検討し、完全（KNN）と近似（ANN）検索戦略を区別し、**hybrid search** と **reranking** が純粋なVector類似性の限界をどのように克服するかを発見しました。最後に、**Mosaic AI Vector Search** と、**Delta sync** を通じてエンベディング管理を自動化し、**Unity Catalog** との堅牢なセキュリティ統合を提供する能力について探索しました。
# MAGIC
# MAGIC **主要なポイント：**
# MAGIC
# MAGIC 1. **エンベディングと整合性：** エンベディングは、類似した概念をVector空間内で近くにマッピングすることで意味的意味を捉えます。効果的な検索のために、エンベディングモデルはドキュメントとクエリの両方に対して共有Vector空間を作成する必要があります。整合性を確保するために、両方に同じモデルを使用してください。
# MAGIC 2. **検索精度：** **ANN**アルゴリズムは本番システムに必要な速度とスケーラビリティを提供しますが、**リランカー**ステップを追加することは、ノイズをフィルタリングし、言語モデルの高い関連性を確保するためにしばしば不可欠です。追加されるレイテンシとコストに対する品質改善のバランスを取ってください。
# MAGIC 3. **統合アーキテクチャ：** **Mosaic AI Vector Search** は、**Delta Lake** との自動同期を提供し、柔軟な取り込みモード（管理、自己管理、または直接CRUD）をサポートすることで運用を簡素化します。この統合により、Unity Catalogを通じてエンタープライズグレードのガバナンスを維持しながら、別個のVectorデータベースインフラストラクチャを管理する複雑さが排除されます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>