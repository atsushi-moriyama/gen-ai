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
# MAGIC # 講義 - 評価ジャッジの種類
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC MLflowは複数の種類の評価ジャッジを提供しており、それぞれ異なる評価シナリオとカスタマイズレベル向けに設計されています。この講義では、組み込みの研究検証済み評価から完全にカスタムな評価ロジックまで、利用可能なジャッジの全範囲を探索します。
# MAGIC
# MAGIC 一般的な基準のための組み込みジャッジ、ビジネスルールのためのガイドラインジャッジ、特殊要件のためのカスタムアプローチを検討します。それぞれのタイプをいつ、どのように使用するかを理解することは、包括的な評価ワークフローを構築するために重要です。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC この講義の終わりまでに、以下のことができるようになります：
# MAGIC - 異なる種類の評価ジャッジ（組み込み、ガイドライン、カスタム）を区別する
# MAGIC - 一般的な評価基準に適した組み込みジャッジを特定する
# MAGIC - ビジネスルールのためのガイドラインジャッジの実装方法を理解する
# MAGIC - カスタムジャッジが必要な場合を認識し、その実装方法を理解する
# MAGIC - 評価結果におけるフィードバック・オブジェクトと根拠の役割を理解する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. ジャッジタイプの概要

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. 評価ジャッジのスペクトラム
# MAGIC
# MAGIC | アプローチ              | カスタマイズレベル | ユースケース |
# MAGIC |----------------------|------------------------|-----------|
# MAGIC | 組み込みジャッジ      | 最小                | `Correctness` や `RetrievalGroundedness` などの組み込みスコアラーでLLM評価を素早く試す。 |
# MAGIC | ガイドラインジャッジ    | 中程度               | スタイルや事実性ガイドラインなど、カスタムな自然言語ルールに対してレスポンスが合格か不合格かをチェックする組み込みジャッジ。 |
# MAGIC | カスタムジャッジ        | 完全                   | 詳細な評価基準とフィードバック最適化を持つ完全にカスタマイズされたLLMジャッジを作成。数値スコア、カテゴリ、またはブール値を返すことが可能。 |
# MAGIC | コードベースのスコアラー   | 完全                   | 完全一致、フォーマット検証、パフォーマンスメトリクスなどを評価するプログラマティックで決定論的なスコアラー。 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 一般的な基準のための組み込みジャッジ

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 研究検証済みジャッジ
# MAGIC
# MAGIC MLflowは一般的な評価タスクのために研究検証済みのジャッジを提供します。これらのジャッジは広範囲な研究を通じて開発され、人間の専門家の判断に対して検証され、特定の評価基準に最適化されています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 主要な組み込みジャッジ
# MAGIC
# MAGIC **Correctness**  
# MAGIC 提供された正解と比較して、モデルの回答が事実的に正しいかどうかを評価します。  
# MAGIC `expectations` を通じて評価データセットに正解が必要です（例：期待される回答や期待される事実）。
# MAGIC
# MAGIC **RelevanceToQuery**  
# MAGIC レスポンスがユーザーのクエリに直接的かつ適切に対応しているかを評価します。  
# MAGIC 話題から外れた、接線的な、または無関係な回答を特定するのに有用です。正解は **必要ありません**。
# MAGIC
# MAGIC **RetrievalSufficiency**  
# MAGIC 取得されたコンテキストが正解の事実を含む正しいレスポンスを生成するために必要なすべての情報を含んでいるかを判定します。  
# MAGIC 正解（`expectations`）が必要で、生成品質ではなく検索品質を評価します。
# MAGIC
# MAGIC **RetrievalRelevance**  
# MAGIC 取得された文書がユーザーのクエリに関連しているかを評価します。  
# MAGIC 正解は **必要なく**、最終回答とは独立して検索ステップのみに焦点を当てます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 追加の組み込みジャッジ
# MAGIC
# MAGIC **RetrievalGroundedness**  
# MAGIC モデルの回答が取得されたコンテキストに基づいており、サポートされていない事実を幻覚していないかをチェックします。  
# MAGIC 正解は **必要なく**、レスポンスと提供された文書間の整合性を評価します。
# MAGIC
# MAGIC **Safety**  
# MAGIC レスポンスに有害、攻撃的、または安全でないコンテンツが含まれていないかを評価します。  
# MAGIC 正解は**必要なく**、ベースラインのコンテンツ安全性チェックとして一般的に使用されます。
# MAGIC
# MAGIC **Guidelines**  
# MAGIC レスポンスが指定された自然言語のルールや制約（例：スタイル、トーン、またはフォーマット要件）に従っているかを評価します。  
# MAGIC グラウンドトゥルースは **不要** です。
# MAGIC
# MAGIC **ExpectationsGuidelines**  
# MAGIC レスポンスが評価データセットで定義された例ごとの自然言語基準を満たしているかを評価します。  
# MAGIC 事実的な正解は必要ありませんが、`expectations` で提供される例固有のガイドラインに依存します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B4. 使用パターンの例
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.genai.scorers import Correctness
# MAGIC
# MAGIC correctness_eval = Correctness(
# MAGIC     model="databricks:/foundation-model-endpoint")
# MAGIC
# MAGIC correctness_results = mlflow.genai.evaluate(
# MAGIC     data=eval_dataset,
# MAGIC     predict_fn=lambda input: agent.predict({"input": input}),
# MAGIC     scorers=[correctness_eval],
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC この例は、Databricks基盤モデルエンドポイントで `Correctness` スコアラーを使用してエンドポイントを評価する一般的なパターンを示しています。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ デモチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">デモチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>2.2 Demo - Using MLflow Built-In Judges</strong>に移動して、これらの組み込みジャッジの動作を確認してください。完了したら、この講義ノートブックに戻って学習を続けてください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. ガイドラインジャッジ

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. 2つのタイプのガイドラインジャッジ
# MAGIC
# MAGIC **1. グローバルガイドライン（`Guidelines` クラス）**
# MAGIC
# MAGIC データセット内のすべての評価に統一基準を適用します。グローバルガイドラインは、トーン、スタイル、またはフォーマット要件など、すべてのテストケースで一貫した標準を強制したい場合に理想的です。
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.genai.scorers import Guidelines
# MAGIC
# MAGIC tone_guidelines = Guidelines(
# MAGIC     name="professional_tone",
# MAGIC     guidelines=[
# MAGIC         "The response must use professional, business-appropriate language",
# MAGIC         "The response should avoid slang, colloquialisms, or overly casual phrasing",
# MAGIC         "The response must address the user respectfully"
# MAGIC     ],
# MAGIC     model="databricks:/foundation-model-endpoint"
# MAGIC )
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 行ごとのガイドライン
# MAGIC
# MAGIC **2. 行ごとのガイドライン（`ExpectationsGuidelines` クラス）**
# MAGIC
# MAGIC 各例に異なる基準を適用し、異なるシナリオで異なる標準が必要な場合に有用です。データセットの各行は `expectations` フィールドに独自の特定のガイドラインを含みます。
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.genai.scorers import ExpectationsGuidelines
# MAGIC
# MAGIC # データセットは "expectations" に行ごとのガイドラインを含む
# MAGIC # 例の行：
# MAGIC # {
# MAGIC #   "input": "返金ポリシーは何ですか？",
# MAGIC #   "output": "私たちの返金ポリシーでは...",
# MAGIC #   "expectations": {
# MAGIC #     "guidelines": ["30日間の期間を言及する必要があります", "レシート要件を含める必要があります"]
# MAGIC #   }
# MAGIC # }
# MAGIC
# MAGIC expected_guidelines = ExpectationsGuidelines(
# MAGIC     name="policy_requirements",
# MAGIC     model="databricks:/foundation-model-endpoint"
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC このアプローチは、各入力が独自の検証基準を必要とする多様なユースケースをテストするのに理想的です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. ガイドラインジャッジの利点とベストプラクティス
# MAGIC
# MAGIC **ガイドラインジャッジの利点：**
# MAGIC
# MAGIC - **ドメインエキスパートのアクセシビリティ**: ビジネス関係者がコーディングなしでガイドラインを書くことができます
# MAGIC - **迅速な反復**: コード変更なしで評価基準を更新できます
# MAGIC - **解釈可能性**: 自然言語のガイドラインは自己文書化されています
# MAGIC - **柔軟性**: コード化が困難な複雑で文脈依存の要件を表現できます
# MAGIC
# MAGIC **ガイドライン作成のヒント：**
# MAGIC
# MAGIC - 曖昧ではなく具体的で明確にする（「レスポンスは信頼できるべき」ではなく「レスポンスはソース文書を引用する必要があります」）
# MAGIC - 客観的に検証可能なガイドラインを書く
# MAGIC - レスポンス内の観察可能な属性に焦点を当てる
# MAGIC - 意図した通りに動作することを確認するため、複数の例でガイドラインをテストする

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ デモチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">デモチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>2.3 Demo - Guideline Judges with MLflow</strong>に移動して、ガイドラインジャッジを実際に探索してください。完了したら、この講義ノートブックに戻って学習を続けてください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ ラボチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">ラボチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>2.4 Lab - Applying Agent Evaluation</strong>に移動して、包括的な評価ワークフローの実装を練習してください。完了したら、この講義ノートブックに戻って学習を続けてください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. カスタムジャッジとコードベースのスコアラー

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 決定論的評価のためのコードベースのスコアラー
# MAGIC
# MAGIC 組み込みジャッジがニーズを満たさない場合、MLflowはコードベースのスコアラーを通じてカスタム評価ロジックをサポートします：
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.genai.scorers import scorer
# MAGIC from mlflow.entities import Feedback
# MAGIC
# MAGIC @scorer
# MAGIC def response_length(outputs):
# MAGIC     """Verify response length is appropriate."""
# MAGIC     word_count = len(str(outputs.get("response", "")).split())
# MAGIC
# MAGIC     if 20 <= word_count <= 100:
# MAGIC         return Feedback(
# MAGIC             value="yes",
# MAGIC             rationale=f"Response length ({word_count} words) is appropriate"
# MAGIC         )
# MAGIC     else:
# MAGIC         return Feedback(
# MAGIC             value="no",
# MAGIC             rationale=f"Response is too {'short' if word_count < 20 else 'long'} ({word_count} words)"
# MAGIC         )
# MAGIC ```
# MAGIC
# MAGIC カスタムスコアラーにより、組み込みジャッジが提供する範囲を超えたドメイン固有の検証ロジックを実装できます。`@scorer` デコレータは関数を再利用可能な評価コンポーネントに変換します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. プリミティブ戻り値を使用する代替アプローチ
# MAGIC
# MAGIC より単純なユースケースでは、スコアラーは直接プリミティブ値を返すことができます：
# MAGIC
# MAGIC ```python
# MAGIC from mlflow.genai.scorers import scorer
# MAGIC
# MAGIC @scorer
# MAGIC def response_length(outputs):
# MAGIC     wc = len(str(outputs.get("response", "")).split())
# MAGIC     return "yes" if 20 <= wc <= 100 else "no"
# MAGIC ```
# MAGIC
# MAGIC このアプローチはより簡潔ですが、スコアリング決定の根拠を提供しないため、単純な合格/不合格チェックにより適しています。
# MAGIC
# MAGIC `@scorer` はプレーンなPython関数をMLflow GenAI Scorerに変換します。これは `mlflow.genai.evaluate()` がオフラインで実行でき、後で本番監視のために登録できるファーストクラスのプラガブルメトリクスです。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. カスタムLLMジャッジ
# MAGIC
# MAGIC 洗練された評価のための **カスタムLLMジャッジ** ：
# MAGIC
# MAGIC 組み込みジャッジでカバーされていない特殊な評価基準のために、独自のLLMベースのジャッジを実装できます。これには以下が含まれます：
# MAGIC 1. 基準を明確に指定する評価プロンプトの設計
# MAGIC 2. それらのプロンプトに基づいて判断を行うLLMの呼び出し
# MAGIC 3. LLMレスポンスを構造化された `Feedback` オブジェクトに解析
# MAGIC 4. このロジックを `mlflow.genai.evaluate()` と互換性のある関数にラップ
# MAGIC
# MAGIC **カスタムジャッジを使用する場合：**
# MAGIC
# MAGIC - アプリケーション固有のドメイン特有の評価基準が必要な場合
# MAGIC - 組み込みジャッジがユースケースにとって重要なニュアンスをキャプチャしない場合
# MAGIC - 独自の標準や規制に対して評価している場合
# MAGIC - 複数のシグナルやデータソースを組み合わせる評価ロジックが必要な場合
# MAGIC
# MAGIC カスタムジャッジは、MLflowの評価フレームワーク、トレーシング、ログインフラストラクチャとの統合を維持しながら、最大の柔軟性を提供します。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ デモチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">デモチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>2.5 Demo - Custom Judges with MLflow</strong>に移動して、特殊な評価ニーズのためのカスタムジャッジの作成方法を学んでください。完了したら、この講義ノートブックに戻って学習を続けてください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. Feedbackオブジェクトと根拠

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. 構造化されたFeedbackオブジェクト
# MAGIC
# MAGIC ```python
# MAGIC Feedback(
# MAGIC     value="yes",        # バイナリ合格/不合格または数値スコア
# MAGIC     rationale="The response correctly identifies the capital as Sacramento...",  # 説明
# MAGIC     metadata={...}      # 追加の構造化情報
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC MLflowジャッジは単純なスカラースコアではなく、構造化された `Feedback` オブジェクトを返します。この構造は評価結果を理解するために重要な解釈可能性を提供します。
# MAGIC
# MAGIC **主要コンポーネント：**
# MAGIC - `value`: 実際のスコアまたは判断
# MAGIC - `rationale`: 人間が読める説明
# MAGIC - `metadata`: 追加のコンテキスト

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. 根拠が重要な理由
# MAGIC
# MAGIC - **デバッグ**: 例が失敗した理由を理解する、単に失敗したことだけでなく
# MAGIC - **ジャッジ検証**: ジャッジが正しく推論していることを確認する
# MAGIC - **パターン識別**: 一般的な根拠テーマが体系的な問題を明らかにする
# MAGIC - **ステークホルダーコミュニケーション**: 技術者以外の聴衆に評価結果を説明する
# MAGIC
# MAGIC **根拠を効果的に使用する：**
# MAGIC
# MAGIC 1. すべての失敗の根拠を読んでパターンを特定する
# MAGIC 2. ジャッジが正しく推論していることを確認するため、合格の根拠をスポットチェックする
# MAGIC 3. 一般的な根拠フレーズを抽出して失敗タイプを分類する
# MAGIC 4. チームと評価について議論する際に代表的な根拠を共有する
# MAGIC
# MAGIC 合格/不合格スコアと詳細な根拠の組み合わせにより、MLflow評価は定量的（追跡可能なメトリクス）かつ定性的（理解可能な推論）になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. 重要なポイント
# MAGIC
# MAGIC MLflowは多様な評価ニーズを満たすための包括的な評価ジャッジスイートを提供します：
# MAGIC
# MAGIC 1. **組み込みジャッジ**: 正確性、関連性、安全性などの一般的な基準のための研究検証済み評価
# MAGIC 2. **ガイドラインジャッジ**: グローバルと例ごとの両方で、自然言語ガイドラインを通じたビジネスルール評価
# MAGIC 3. **カスタムコードベースのスコアラー**: 特定の要件のための決定論的評価ロジック
# MAGIC 4. **カスタムLLMジャッジ**: 特殊なドメイン要件のための洗練された評価
# MAGIC 5. **構造化されたフィードバック**: 根拠が解釈可能性とデバッグ機能を提供
# MAGIC
# MAGIC 適切なジャッジの組み合わせの選択は、特定の評価要件、利用可能な正解、および必要なカスタマイズレベルに依存します。次の講義では、評価戦略と実践的な実装アプローチを探索します。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>