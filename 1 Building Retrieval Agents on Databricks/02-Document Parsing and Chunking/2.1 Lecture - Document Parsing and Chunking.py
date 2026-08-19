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
# MAGIC # ドキュメント解析とチャンキング
# MAGIC
# MAGIC ## はじめに
# MAGIC
# MAGIC **Retrieval Augmented Generation (RAG)** アプリケーションの効果は、取得するデータの品質によって根本的に制約されます。**embedding generation** の前に、PDF、HTMLファイル、画像などの生の **unstructured data** を取り込み、保存し、**Large Language Models (LLMs)** が解釈できる形式に変換する必要があります。このレッスンでは、**Databricks Intelligence Platform** 内でのデータ準備段階に焦点を当て、特に保存には **Delta Lake**、ガバナンスには **Unity Catalog** を活用します。バイナリファイルから構造化テキストを抽出するためのネイティブな **`ai_parse_document`** 関数を検証し、基本的な **fixed-size splitting** から **context-aware methods** へと移行する **text chunking** の重要な戦略を探求します。
# MAGIC
# MAGIC ## レッスンの目標
# MAGIC
# MAGIC * RAGにおける非構造化データの保存におけるDelta LakeとUnity Catalogボリュームの役割を説明する。
# MAGIC * Databricks AI関数、特に`ai_parse_document`の機能と、図の説明などのv2.0機能について説明する。
# MAGIC * AutoloaderとSpark宣言型パイプライン（SDP）を使用した効率的な取り込みパターンを特定する。
# MAGIC * 固定サイズ、再帰的、埋め込みベースのセマンティックチャンキング戦略を比較対照する。
# MAGIC * Databricksでの解析とチャンキングに使用される標準的なツールとframeworksをマッピングする。

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. データストレージと処理アーキテクチャ
# MAGIC
# MAGIC RAGアーキテクチャでは、データストレージは生のソースファイルと処理済みの構造化テキストの両方に対応する必要があります。**Delta Lake** は統合データ管理レイヤーとして機能し、すべてのデータタイプにACIDトランザクションとバージョニングを提供します。Delta Tableは構造化データに最適化されていますが、RAG workflowsは通常、PDFなどの非構造化ファイルから始まります。
# MAGIC
# MAGIC **Unity Catalog Volumes** は、これらの非表形式ファイルのガバナンスレイヤーを提供します。ボリュームを使用することで、テーブルやモデルに適用されるのと同じ統合権限モデルを使用して、生ファイルへのアクセスを管理できます。生ドキュメントをボリュームに保存し、処理済みテキストをDelta Tableに保存することで、元のファイルから検索に使用されるチャンクテキストまでの完全なリネージを維持できます。
# MAGIC
# MAGIC **注意：** ボリュームは「生」ファイル（ブロンズ）を保存し、Delta Tableは「解析およびチャンク化された」テキスト（シルバー/ゴールド）を保存します。
# MAGIC
# MAGIC 以下は、データ取り込みと処理ワークフローの概要です。典型的な使用例では、そしてこのモジュールでは、このワークフローに従い、最初の3つのステップに焦点を当てます：
# MAGIC
# MAGIC 1. **Data ingestion and pre-processing：** Unity Catalogボリュームからファイルを読み取り、AI関数を使用して解析する。
# MAGIC 1. **Data storage：** 解析されたドキュメントをDelta Lakeに保存し、必要なガバナンス制御を適用する。（ガバナンスはこのモジュールでは詳細に扱われません。）
# MAGIC 1. **Chunking：** 埋め込み生成に適したチャンクにデータを分割する。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/02-process-diagram.png" alt="データストレージ、取り込み、処理ワークフロー" /> -->
# MAGIC   ![02-process-diagram](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/02-process-diagram.png)
# MAGIC
# MAGIC *図1. この図は、データ取り込み、処理、埋め込み生成ワークフローの5つの主要ステップを示しています。*

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. AI関数を使用したドキュメント処理
# MAGIC
# MAGIC ドキュメント処理は、特にドキュメントが主要な知識源として機能する場合、検索エージェント用の高品質な知識ベースを構築するために不可欠です。実世界のドキュメントは複雑な構造を持つことが多く、これらの課題に対処するため、多様なドキュメント形式から情報を解釈・抽出するために特別に設計された大規模言語モデル（LLM）やOCR対応LLMなどの高度なモデルを活用します。Databricksは、このプロセスを合理化するためのネイティブAI関数を提供します。特に、`ai_parse_document` 関数は、PDFや画像の堅牢な解析を可能にし、生ファイルから直接構造化コンテンツとレイアウト情報を抽出します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. ドキュメント処理の課題
# MAGIC
# MAGIC 実世界のドキュメントの解析は複雑です。なぜなら、それらは単純なテキストだけではないからです。ドキュメントには、**images**、**multi-column layouts**、**tables**、**figures**、**headers**、**subheaders**、**page numbers** の組み合わせが含まれることが多いです。この情報をセマンティックな意味を維持しながら適切に抽出することは、いくつかの課題を提示します：
# MAGIC
# MAGIC * **Hierarchical Information：**チャートや図表は、保持されなければならない階層関係を伝えることが多い。
# MAGIC * **Order Preservation：**多列ドキュメントでは、読み順が重要であり、単純な解析では列が誤って結合される可能性がある。
# MAGIC * **Contextual Integrity：**画像（チャートや製品写真など）は、関連するテキスト説明と関連付けられて保持されなければならない。
# MAGIC
# MAGIC
# MAGIC
# MAGIC <!-- <img src="../Includes/images/02-complex-page-structure-example.png" alt="複雑なページレイアウトを示すページの例" /> -->
# MAGIC ![02-complex-page-structure-example](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/02-complex-page-structure-example.png)
# MAGIC
# MAGIC *図2. この画像は、複雑なページレイアウトを持つページレイアウトの例を示しています。*

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### B2. 解析のためのLLMとOCR
# MAGIC
# MAGIC これらの課題に対処するため、現代のアプローチは **Large Language Models (LLMs)** と **OCR (Optical Character Recognition)** モデルを活用します。従来のテキストパーサーとは異なり、これらのモデルはドキュメントレイアウトを「見る」ことができます。OCRモデルは画像内のテキストを識別でき、マルチモーダルLLMは要素の空間的配置を解釈し、キャプションが上の画像に属することや、表が複数ページにまたがることを理解できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. `ai_parse_document`の使用
# MAGIC
# MAGIC Databricksは **AI Functions** でこのプロセスを簡素化します。これにより、開発者は簡単なSQLやPython関数呼び出しを使用して、これらの高度なAIモデルを直接データに適用できます。これにより、別のモデル推論インフラストラクチャを管理する必要がなくなります。これらの関数はサーバレスで実行され、数百万行を処理するために自動的にスケールし、Unity Catalog内のガバナンスされたデータで直接動作します。
# MAGIC
# MAGIC **`ai_parse_document`** 関数は、このタスクのための主要なDatabricksツールです。これは最先端のGenerative AIモデルを呼び出して、非構造化ドキュメント（PDFや画像など）から構造化コンテンツを抽出し、結果を構造化JSONオブジェクト（VARIANT型）として返します。
# MAGIC
# MAGIC **Key Capabilities (Schema v2.0)：**
# MAGIC
# MAGIC * **Layout Awareness：** ドキュメントコンテンツをレイアウト情報から分離する。
# MAGIC * **Figure Descriptions：** PDF内で見つかったチャートや画像のテキスト説明を自動生成でき、視覚データをLLMがアクセス可能にする。
# MAGIC * **Bounding Boxes：** テキスト要素の座標（bbox）を返し、UIでソースをハイライトするのに有用。
# MAGIC
# MAGIC **Example implementation：**
# MAGIC
# MAGIC ```sql
# MAGIC -- バイナリPDFデータからドキュメントレイアウトとコンテンツを抽出
# MAGIC SELECT ai_parse_document(content) as parsed_document  
# MAGIC FROM read_files(  
# MAGIC   '/Volumes/path/to/pdfs/',  
# MAGIC   format => 'binaryFile'  
# MAGIC )
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. データクリーニングと変換
# MAGIC
# MAGIC ドキュメントを解析した後、解析されたコンテンツをクリーニングし、目標に合う形式に変換する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. ノイズ除去
# MAGIC
# MAGIC テキストをチャンク化する前に、検索品質を劣化させるアーティファクトを除去するためのクリーニングが必要です。生の抽出には、テキストのセマンティックフローを中断する可能性のあるヘッダー、フッター、ページ番号が含まれることが多いです。クリーニングロジックは解析段階の出力に適用されるべきです。HTMLデータについては、過度の書式設定タグがモデルを混乱させる可能性がありますが、`ai_parse_document` はHTMLフォーマットでテーブルをインテリジェントに抽出でき、その構造を保持してウェブページの解析と表形式データの解釈可能性を確保します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. メタデータの注入
# MAGIC
# MAGIC 効果的なRAGシステムは、Vector類似性検索 *前に* 検索結果をフィルタリングするためにメタデータに依存します。変換中に、ドキュメントタイトル、著者名、作成日などのメタデータを抽出し、関連付けることが重要です。このメタデータがファイルプロパティにない場合、**ai_extract** などの関数を使用して、非構造化テキストから構造化フィールド（「請求書日付」や「契約タイプ」など）を識別・抽出できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. チャンキング戦略
# MAGIC チャンキングは、長いドキュメントを小さく管理可能なセグメントに分割するプロセスです。このステップは、埋め込みモデルにコンテキストウィンドウ制限があり、精密な情報検索には粒度の細かい検索結果が必要であるため不可欠です。
# MAGIC
# MAGIC もう一つの重要な考慮事項は、コンテキストサイズと言語モデルパフォーマンスの関係です。「Lost in the Middle」現象は、LLMが大きなコンテキストウィンドウの深部に埋もれた情報を見落とすときに発生します。その結果、重要な詳細が見逃されないよう、より小さく関連性の高いチャンクを作成することが推奨されます。
# MAGIC
# MAGIC 重要な問題は、ドキュメントを最適にチャンク化する方法です。いくつかのチャンキング手法があり、このセクションでは最も一般的で効果的なアプローチを探求します。
# MAGIC
# MAGIC **ヒント**: チャンクサイズとスプリッターに基づくチャンキングを視覚化するには [ChunkViz](https://chunkviz.up.railway.app/) をチェックしてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 固定サイズ vs 再帰的チャンキング
# MAGIC
# MAGIC * **Fixed-Size Chunking (Legacy/Baseline)：** ハードな文字数またはトークン数（例：500トークン）に基づいてテキストを分割します。計算コストは安いですが、文や段落を半分に分割することが多く、コンテキストを破壊します。
# MAGIC
# MAGIC * **Semantic Chunking (Recommended Standard)：** 任意の文字分割とは異なり、このアプローチは **sentences**、**paragraphs**、**document sections** などの意味のある言語境界に基づいてテキストを分割します。ドキュメントの論理構造を尊重することで、情報のセマンティックな整合性を保持します。さらに、セマンティックチャンキングでは、関連する **metadata**、**tags**、**titles** をチャンクに直接注入することが多く、小さなテキストセグメントでも検索中により広いコンテキストを保持できます。
# MAGIC
# MAGIC
# MAGIC <!-- <img src="../Includes/images/02-chunking-methods.png" alt="視覚化されたチャンキング手法"/> -->
# MAGIC ![02-chunking-methods](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/02-chunking-methods.png)
# MAGIC
# MAGIC *図3. 固定サイズチャンキングとセマンティックチャンキングの視覚的表現。*

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. 高度なチャンキング戦略
# MAGIC
# MAGIC 検索パフォーマンスを最大化し、境界を越えたセマンティックな一貫性を確保するため、複雑なドキュメントを処理し、コンテキストを保持するために、より洗練された戦略が必要です。
# MAGIC
# MAGIC * **Chunk Overlap：** この技法は、連続するチャンク間のオーバーラップ量（例：10-20%）を定義します。次のチャンクの開始時にテキストの小部分を繰り返すことで、チャンク間でコンテキスト情報が失われることを防ぎ、文やアイデアが急激に切断されることを防ぎます。
# MAGIC
# MAGIC * **Embedding-Based Semantic Chunking：** これは、埋め込みモデルを使用してブレークポイントを決定するより高度な手法です。連続する文間のセマンティック類似性を計算し、トピックが大幅に変化したとき（つまり、類似性がしきい値を下回ったとき）のみチャンクを「分割」します。これにより、各チャンクが明確で一貫した概念を表すことが保証されます。
# MAGIC
# MAGIC * **Windowed Summarization：** これは、各チャンクに前のいくつかのチャンクの「ウィンドウ化要約」を含める「コンテキスト強化」チャンキング手法です。現在のテキストだけを見る代わりに、モデルは前に来たものの要約を受け取り、全履歴を埋め込むコストなしに、より広いコンテキストを提供します。
# MAGIC
# MAGIC <!-- <img src="../Includes/images/02-advanced-chunking-methods.png" alt="視覚化された高度なチャンキング手法"/> -->
# MAGIC ![02-advanced-chunking-methods](https://files.training.databricks.com/binder/prod_main/building-retrieval-agents-on-databricks-ja_jp-1.0.1/images/02-advanced-chunking-methods.png)
# MAGIC
# MAGIC
# MAGIC *図4. 高度なチャンキング手法の視覚的表現。各色はチャンクを表します。*

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 埋め込みモデルの考慮事項
# MAGIC
# MAGIC 埋め込みモデルは後のモジュールで詳細に扱われますが、その技術的制約はチャンキング段階で *今* 考慮されなければなりません。
# MAGIC
# MAGIC * **Context Window Limits：** すべての埋め込みモデルには最大トークン制限（例：512、8192トークン）があります。テキストチャンクがこの制限を超えると、モデルは単純にテキストを **切り捨て**、制限を超えたコンテンツを無視します。これにより、不完全なベクトル表現となり、データが失われます。したがって、最大チャンクサイズは常に埋め込みモデルのコンテキストウィンドウ制限を安全に下回る必要があります。
# MAGIC
# MAGIC * **Granularity vs. Context：** より大きなコンテキストウィンドウはより大きなチャンクを可能にし、より多くのコンテキストを捕捉しますが、特定の詳細を希薄化する可能性があります。より小さなウィンドウはより小さなチャンクを強制し、より精密ですが周囲のコンテキストが不足する可能性があります。チャンクサイズの選択は、下流で使用する予定の特定の埋め込みモデルの機能と一致しなければならない直接的なトレードオフです。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. チャンキングのためのツールとframeworks
# MAGIC
# MAGIC Databricksでのドキュメント処理は、ネイティブAI関数とLangChainなどの主要なオープンソースライブラリを組み合わせて、堅牢な多段階パイプラインを作成します。このワークフローは、順次解析とチャンキングを通じて生ファイルを埋め込み可能なテキストに変換します。
# MAGIC
# MAGIC 1. **Parsing (Extraction)：** 最初のステップは、生ファイルを解析し、レイアウト情報と共にクリーンなテキストを抽出することです。
# MAGIC    * **`ai_parse_document` (Native)：** この推奨ツールは、標準ドキュメント（PDF、画像）を効率的に処理し、OCRとレイアウト解析をサーバレスで実行します。下流タスクの準備ができた構造化テキストを返します。
# MAGIC 1. **Chunking (Splitting)：**抽出後、テキストはより小さく管理可能なチャンクに分割されなければなりません。
# MAGIC    * **LangChain：** LangChainなどのライブラリは、解析されたテキストに対する高度な分割ロジック（例：`RecursiveCharacterTextSplitter`）を提供します。LangChainのテキストスプリッターのスイートは多様な形式と戦略をサポートし、チャンキングの業界標準となっています。
# MAGIC    * **Custom Functions：** 開発者は、特定のマークダウンヘッダーでテキストを分割するなど、専門的な分割ロジックを `ai_parse_document` の出力に適用するために、カスタムPythonユーザー定義関数（UDF）を実装することもできます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. まとめ
# MAGIC
# MAGIC DatabricksでのRAGのためのデータ準備には、取り込み、解析、変換の信頼できるパイプラインが含まれます。生ファイルは最初にUnity Catalogボリュームに取り込まれます。次に、LLMとOCRを活用してPDFなどの複雑なドキュメントからクリーンなテキストとレイアウト情報を抽出するネイティブ **`ai_parse_document`** 関数を使用して解析されます。最後に、このテキストは **Recursive Character Splitting** や **Embedding-Based Semantic Chunking** などの高度な手法を使用して戦略的にチャンク化され、検索システムが埋め込みモデルの制約を尊重しながら精密でコンテキストリッチな情報にアクセスできることを保証します。
# MAGIC
# MAGIC **Key Takeaways:**
# MAGIC
# MAGIC 1. **Unified Governance:** 生ファイルをUnity Catalogボリュームに、処理済みチャンクをDelta Tableに保存して、完全なデータリネージとセキュリティを維持する。
# MAGIC 2. **Sequential Processing:** ドキュメント準備は2段階プロセスです：まず、堅牢な抽出（OCR/レイアウト）のために **`ai_parse_document`** を使用し、次に、論理的分割のためにLangChainなどのライブラリを使用します。
# MAGIC 3. **Advanced Chunking：** 単純な固定サイズ分割を超えて、**semantic strategies**、**Overlap**、または **Parent Document Retrieval** を採用して、コンテキスト損失を防ぎ、検索精度を向上させる。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>