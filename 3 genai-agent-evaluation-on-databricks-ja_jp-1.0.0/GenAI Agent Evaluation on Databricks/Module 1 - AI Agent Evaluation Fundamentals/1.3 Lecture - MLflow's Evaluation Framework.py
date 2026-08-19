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
# MAGIC # 講義 - MLflowの評価フレームワーク
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC MLflowは、生成AIアプリケーション専用に設計された包括的な評価フレームワークを提供し、自動ジャッジ、トレーシング機能、および体系的な評価ツールを提供します。この講義では、MLflowのアーキテクチャ、コアコンポーネント、およびそれらがどのように連携して厳密なエージェント評価を可能にするかを探ります。
# MAGIC
# MAGIC MLflow評価の3つの基本コンポーネントを検証し、`mlflow.genai.evaluate()` 関数を理解し、トレーシングが高度な評価機能の基盤をどのように提供するかを探ります。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC この講義の終了時には、以下のことができるようになります：
# MAGIC - MLflowの評価フレームワークのアーキテクチャと主要コンポーネントを説明する
# MAGIC - 評価データセット、スコアラー、予測関数の役割を理解する
# MAGIC - `mlflow.genai.evaluate()` 関数が評価をどのようにオーケストレーションするかを説明する
# MAGIC - エージェント評価とデバッグにおけるトレーシングの役割を理解する
# MAGIC - AI Gatewayの統合が本番監視をどのように可能にするかを認識する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. MLflowの概要とOpenTelemetry統合

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. MLflowプラットフォーム概要
# MAGIC
# MAGIC ![preparing-for-evaluation.png](../Includes/images/Evaluation with MLflow/preparing-for-evaluation.png "preparing-for-evaluation.png")
# MAGIC
# MAGIC MLflowは、機械学習のライフサイクル全体を管理するためのオープンソースプラットフォームであり、高度な可観測性と監視のためにOpenTelemetryをネイティブにサポートし、外部の可観測性プラットフォームへのシームレスなトレーシングとメトリクス出力を可能にします。
# MAGIC
# MAGIC **MLflowのコア機能：**
# MAGIC - パラメータ、メトリクス、モデル系譜を含むエクスペリメント追跡
# MAGIC - バージョニング、ステージ移行、注釈のためのモデルレジストリ（Unity Catalogと統合）
# MAGIC - バッチ、ストリーミング、リアルタイム推論のためのモデルデプロイメント
# MAGIC - 即座の可観測性のためのリアルタイムトレーシングサーバー（MLflowトレーシング）
# MAGIC - GenAIトレースの自動スコアリングを含む本番監視
# MAGIC - プロンプトエンジニアリングとGenAI評価ワークフローの充実したサポート

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. OpenTelemetry統合
# MAGIC
# MAGIC **OpenTelemetry統合の利点：**
# MAGIC - OpenTelemetryは、テレメトリデータの収集と出力のためのオープン標準であり、クラウドネイティブシステム全体の可観測性で広く採用されています
# MAGIC - MLflowトレースはOpenTelemetryトレース仕様と完全に互換性があり、人気のあるソリューション（Datadog、New Relic、Grafana、Splunkなど）への出力を可能にします
# MAGIC - MLflowは3つのトレース出力モードをサポートします：
# MAGIC   - MLflowトラッキングのみ（デフォルト）：MLflowトラッキングサーバーにトレースを送信
# MAGIC   - OpenTelemetryのみ：OpenTelemetryコレクターにトレースを送信
# MAGIC   - デュアル出力：MLflowとOpenTelemetryコレクターの両方にトレースを送信

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. コアアーキテクチャ

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 3つの基本コンポーネント
# MAGIC
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC <img src="https://docs.databricks.com/aws/en/assets/images/flowchart-00c729ac75207b58d9c2243583a30d5a.png" alt="MLFlow Evaluation">
# MAGIC </div>
# MAGIC
# MAGIC MLflowは、生成AIアプリケーション専用に設計された包括的な評価フレームワークを提供します。アーキテクチャは3つの基本コンポーネントを中心としています：

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. コンポーネント1：評価データセット
# MAGIC
# MAGIC 評価データセットは、テストする内容を定義します。最低限、入力（エージェントへのクエリやリクエスト）が含まれます。オプションで以下を含むことができます：
# MAGIC
# MAGIC - **出力**：推論を再実行することなく、より高速な評価のための事前生成されたエージェント応答
# MAGIC - **期待値**：期待される事実、期待される応答、行ごとのガイドラインなどのグラウンドトゥルース情報
# MAGIC - **トレース**：多段階エージェント動作を分析するための完全な実行トレース
# MAGIC - **メタデータ**：ユーザー設定、会話履歴、取得されたドキュメントなどの追加コンテキスト
# MAGIC
# MAGIC データセットは通常、簡単な操作とバージョニングのためにJSONファイルまたはPandas DataFrameとして保存されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. コンポーネント2：スコアラー（ジャッジ）
# MAGIC
# MAGIC スコアラーは、定義された基準に対してエージェントの出力を評価します。MLflowは複数のスコアラータイプを提供します：
# MAGIC
# MAGIC - **組み込みジャッジ**：正確性、関連性、安全性などの一般的な基準に対する研究で検証されたLLMベースの評価
# MAGIC - **ガイドラインジャッジ**：自然言語で表現されたカスタムビジネスルール
# MAGIC - **コードベーススコアラー**：決定論的評価のためのPython関数（長さチェック、フォーマット検証など）
# MAGIC - **カスタムLLMジャッジ**：専門的な要件のための独自のLLMベース評価ロジック

# COMMAND ----------

# MAGIC %md
# MAGIC ### B4. コンポーネント3：予測関数
# MAGIC
# MAGIC 予測関数は、評価データセットの出力を生成します。これは以下のようなものです：
# MAGIC
# MAGIC - エージェントの予測メソッド（オンザフライ評価用）
# MAGIC - エージェントが期待する形式に入力を変換するラムダ
# MAGIC - 事前生成された出力を評価する場合は完全に省略
# MAGIC
# MAGIC これら3つのコンポーネントは `mlflow.genai.evaluate()` で統合され、評価プロセスをオーケストレーションし、メトリクスを収集し、分析のための包括的な結果をログに記録します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. `mlflow.genai.evaluate()`関数

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. 中央オーケストレーションポイント
# MAGIC
# MAGIC ```python
# MAGIC import mlflow
# MAGIC from mlflow.genai.scorers import Correctness
# MAGIC
# MAGIC results = mlflow.genai.evaluate(
# MAGIC     data=eval_dataset,                  # DataFrame、list[dict]、またはEvaluationDataset
# MAGIC     scorers=[Correctness()],            # 組み込みおよび/またはカスタムスコアラー
# MAGIC     predict_fn=my_app,                  # オプション：直接評価
# MAGIC     # model_id="models:/my-app/1",      # オプション：バージョン管理されたアプリへのリンク
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC `mlflow.genai.evaluate()` 関数は、エージェント評価の中央オーケストレーションポイントとして機能します。その動作を理解することは、効果的な評価ワークフローにとって重要です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 主要パラメータ
# MAGIC
# MAGIC **主要パラメータ：**
# MAGIC - `data`：評価データセット
# MAGIC - `scorers`：スコアリング関数のリスト
# MAGIC - `predict_fn`：エージェント/アプリ関数
# MAGIC - `model_id`：オプションのモデル参照

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. 評価ワークフロー
# MAGIC
# MAGIC **評価ワークフロー：**
# MAGIC
# MAGIC 1. **データ読み込み**：MLflowが評価データセットを読み込み、その構造を検証します
# MAGIC 2. **出力生成**：`predict_fn` が提供されている場合、MLflowは各入力に対してそれを呼び出し、出力を生成します
# MAGIC 3. **トレース作成**：各予測は、predict_fnが計測されている場合（例：`@mlflow.trace` または `mlflow.openai.autolog` で）、または `mlflow.genai.to_predict_fn` でエンドポイントを評価する場合にMLflowトレースを作成します。「解答シート」モードでは、アプリを実行せずに入力/出力からトレースを構築します
# MAGIC 4. **スコアラー実行**：各スコアラーがそのロジックに従って入力/出力/トレースを評価します
# MAGIC 5. **結果集計**：個別のスコアが要約メトリクスに集計されます
# MAGIC 6. **ログ記録**：結果が分析と比較のためにMLflowにログ記録されます

# COMMAND ----------

# MAGIC %md
# MAGIC ### C4. 戻り値と結果アクセス
# MAGIC
# MAGIC **戻り値：**
# MAGIC
# MAGIC 関数は以下を含む `EvaluationResult` オブジェクトを返します：
# MAGIC - **run_id**：この評価実行の一意識別子
# MAGIC - **metrics**：すべての例にわたって集計されたメトリクス（例：平均スコア、合格率）
# MAGIC
# MAGIC **例ごとの結果へのアクセス：**
# MAGIC
# MAGIC MLflow 3では、例ごとの結果はresult_df属性ではなくトレースを介してアクセスされます：
# MAGIC ```python
# MAGIC eval_traces = mlflow.search_traces(run_id=results.run_id)
# MAGIC ```
# MAGIC
# MAGIC この構造化されたアプローチにより、個々のエージェント相互作用への完全な可観測性を維持しながら、体系的な評価が可能になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. MLflowトレーシング：エージェント可観測性の基盤

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 包括的な可観測性
# MAGIC
# MAGIC MLflowトレーシングは、エージェント実行への包括的な可観測性を提供し、エージェントの推論プロセスのすべてのステップをキャプチャします。トレーシングは、適切に計測された予測関数で `mlflow.genai.evaluate()` を使用する際に有効になり、多くの評価機能の基盤を形成します。
# MAGIC
# MAGIC **トレーシングがキャプチャするもの：**
# MAGIC
# MAGIC - **モデル呼び出し**：プロンプト、応答、モデルパラメータを含む基盤モデルとのすべての相互作用
# MAGIC - **ツール呼び出し**：入力パラメータと戻り値を含む関数呼び出し
# MAGIC - **取得操作**：コンテンツとメタデータを含むベクトルストアから取得されたドキュメント
# MAGIC - **タイミング情報**：パフォーマンス分析のための各操作の継続時間
# MAGIC - **階層構造**：実行フローを示す親子関係

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. トレース内のスパンタイプ
# MAGIC
# MAGIC MLflowはトレースを特定のタイプのスパンに整理します：
# MAGIC - **ルートスパン**：完全なエージェント呼び出しを表すトップレベルスパン
# MAGIC - **RETRIEVER**：ベクトル検索または他の取得システムからドキュメントが取得されるスパン
# MAGIC - **TOOL**：個別のツールまたは関数呼び出し
# MAGIC - **CHAT_MODEL**：言語モデルの相互作用
# MAGIC - **CHAIN**：操作のシーケンス（LangChainベースのエージェントで一般的）

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 評価におけるトレーシングの重要性
# MAGIC
# MAGIC **評価におけるトレーシングの重要性：**
# MAGIC
# MAGIC `RetrievalSufficiency` などの特定の評価ジャッジは、機能するためにトレースを必要とします。これらは、取得システムが適切な情報を提供したかどうかを評価するために、（最終応答だけでなく）何が取得されたかを分析します。トレースなしでは、これらの高度な評価は不可能です。
# MAGIC
# MAGIC トレーシングはまた、失敗した評価中に正確に何が起こったかを検査することを可能にし、問題が取得品質、ツール選択、またはLLM推論に起因するかどうかを特定することでデバッグを可能にします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. AI Gateway統合と本番監視

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. AI Gateway統合
# MAGIC
# MAGIC Mosaic AI Agent Frameworkを使用してエージェントを登録し、Model Servingにデプロイすると、DatabricksはAI Gateway拡張推論テーブルを自動的に有効にします。これらのテーブルは、本番環境でのすべてのリクエストと応答の詳細なログ記録を提供します。
# MAGIC
# MAGIC **推論テーブルの利点：**
# MAGIC
# MAGIC - **自動ログ記録**：デプロイされたエージェントへのすべてのリクエストが追加の計測なしでキャプチャされます
# MAGIC - **豊富なメタデータ**：リクエスト/応答コンテンツ、タイムスタンプ、レイテンシ、モデルバージョン、トレースデータが含まれます
# MAGIC - **クエリインターフェース**：分析と監視のためのUnity CatalogでのSQLクエリ可能なテーブル
# MAGIC - **評価統合**：推論テーブルデータを評価データセットとして直接使用可能

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. 本番から評価へ
# MAGIC
# MAGIC この統合により、強力なフィードバックループが作成されます：
# MAGIC 1. エージェントが本番環境で実行され、すべての相互作用を推論テーブルにログ記録します
# MAGIC 2. 推論テーブルをクエリして、興味深い例、失敗ケース、またはエッジケースを抽出します
# MAGIC 3. これらの実世界の例が評価データセットを補強します
# MAGIC 4. 将来の評価が実際の本番シナリオに対してテストされます
# MAGIC
# MAGIC このアプローチにより、評価データセットが静的で潜在的に古くなることなく、実際のユーザー行動とともに進化することが保証されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. 重要なポイント
# MAGIC
# MAGIC MLflowの評価フレームワークは、以下を通じてエージェント評価のための包括的なソリューションを提供します：
# MAGIC
# MAGIC 1. **3コンポーネントアーキテクチャ**：評価データセット、スコアラー、予測関数がシームレスに連携します
# MAGIC 2. **中央オーケストレーション**：`mlflow.genai.evaluate()` が評価ワークフローの複雑さを処理します
# MAGIC 3. **包括的なトレーシング**：エージェント実行への完全な可観測性により、高度な評価とデバッグが可能になります
# MAGIC 4. **本番統合**：AI Gatewayと推論テーブルが本番と評価の間のフィードバックループを作成します
# MAGIC 5. **OpenTelemetry互換性**：業界標準の可観測性ツールとの統合
# MAGIC
# MAGIC この基盤により、エージェント開発ニーズとともに成長する体系的でスケーラブルな評価が可能になります。次の講義では、このフレームワーク内で実装できる特定のタイプのジャッジと評価戦略を探ります。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>