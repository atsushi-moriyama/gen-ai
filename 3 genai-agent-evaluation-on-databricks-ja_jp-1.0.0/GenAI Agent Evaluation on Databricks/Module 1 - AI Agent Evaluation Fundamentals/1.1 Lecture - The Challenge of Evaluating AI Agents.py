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
# MAGIC # 講義 - AIエージェントの評価の課題
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC 従来のソフトウェアテスト手法は、AIエージェントの非決定論的性質、創発的行動、文脈依存の応答により、根本的に不十分です。この講義では、従来のテストがAIエージェントで失敗する理由を探り、専門的な評価フレームワークを必要とする独特の課題を紹介します。
# MAGIC
# MAGIC AIエージェントによって従来のテストパラダイムが通用しなくなる理由を理解し、多段階推論評価の複雑さを理解し、評価を一回限りの検証ステップではなく継続的なプロセスとして扱う必要がある理由を学びます。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC この講義の終了時には、以下ができるようになります：
# MAGIC - 従来のソフトウェアテスト手法がAIエージェントに不十分である理由を説明する
# MAGIC - AIエージェントの評価に固有の主要な課題（非決定論、創発的行動、文脈依存性）を特定する
# MAGIC - 評価を継続的なプロセスとして扱う必要がある理由を理解する
# MAGIC - 適切な評価データセット設計の重要性を認識する
# MAGIC - 体系的なエージェント評価のための運用セットアップ要件を説明する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 従来のテストが不十分な理由

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. 決定論的テストパラダイム
# MAGIC
# MAGIC 従来のソフトウェアテストは、決定論的な入力と期待される出力に基づいています。ユニットテスト、統合テスト、エンドツーエンドテストを作成し、同じ入力が与えられた場合にコードが毎回まったく同じ結果を生成することを検証します。このアプローチは、動作が予測可能で再現性のある従来のソフトウェアシステムにおいては有効です。
# MAGIC
# MAGIC **従来のテストの前提：**
# MAGIC - 同じ入力は常に同じ出力を生成する
# MAGIC - 動作は明示的にプログラムされ、予測可能である
# MAGIC - 成功は正確な文字列マッチングや数値比較で測定できる
# MAGIC - エッジケースは予測され、体系的にテストできる

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. AIエージェントによりパラダイムが通用しなくなる理由
# MAGIC
# MAGIC **AIエージェントにより、このパラダイムは根本的に通用しなくなります：**
# MAGIC
# MAGIC - **非決定論**：LLMは温度とサンプリングを通じてランダム性を導入し、同じ入力が異なる出力を生成する可能性があります
# MAGIC - **創発的行動**：エージェントは明示的にプログラムされていないツール使用と推論パスについて自律的な決定を行います
# MAGIC - **文脈依存性**：エージェントの応答は取得されたドキュメント、会話履歴、外部データソースに依存します
# MAGIC - **定性的評価**：成功は正確な文字列マッチングではなく、有用性、トーン、適切性についての主観的判断を必要とすることがよくあります
# MAGIC
# MAGIC 簡単な例を考えてみましょう：「サンフランシスコの天気は？」という質問に答えるエージェントは次のように応答するかもしれません：
# MAGIC - 「現在サンフランシスコは65°Fで晴れています。」
# MAGIC - 「サンフランシスコの天気：65度、晴天。」
# MAGIC - 「SFの気温は65°Fで雲はありません。」
# MAGIC
# MAGIC 3つの応答はすべて正しく、有用で、適切ですが、どれも正確に一致しません。従来のアサーションベースのテスト（`assert output == "expected_response"`）は3つすべてで失敗します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. エージェント評価の課題

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. 多次元の複雑さ
# MAGIC
# MAGIC ![the-agent-evaluation-challenge.png](../Includes/images/Evaluation with MLflow/the-agent-evaluation-challenge.png)
# MAGIC
# MAGIC AIエージェントの評価は、従来のソフトウェアを超えた独自の複雑さをもたらします：
# MAGIC
# MAGIC **多段階推論**：エージェントは複数のツールを呼び出し、様々なドキュメントを取得し、複雑な推論チェーンを構築する可能性があります。評価は最終的な答えだけでなく、中間ステップの品質も評価する必要があります。
# MAGIC
# MAGIC **ツール呼び出しの精度**：エージェントは正しいツールを選択しましたか？適切なパラメータを渡しましたか？ツール結果を正しく解釈しましたか？
# MAGIC
# MAGIC **取得品質**：RAGベースのエージェントの場合、評価は取得されたドキュメントに関連情報が含まれていることと、エージェントが複数のソースからの情報を正しく統合していることを検証する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 安全性と実世界の変動性
# MAGIC
# MAGIC **安全性とアライメント**：エージェントは有害な出力を避け、ユーザーの境界を尊重し、不適切な要求を拒否する必要があります—これらは単純な合格/不合格テストを超えた洗練された評価を必要とする品質です。
# MAGIC
# MAGIC **実世界の変動性**：本番環境のエージェントは多様なユーザークエリ、予期しない表現、開発中に予測することが困難なエッジケースに遭遇します。
# MAGIC
# MAGIC これらの課題は、AIエージェントの確率的で文脈的な性質に特別に設計された、より洗練された評価フレームワークを要求します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 継続的なプロセスとしての評価

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. 継続的評価サイクル
# MAGIC
# MAGIC ![evaluation-as-continuous-process.png](../Includes/images/Evaluation with MLflow/evaluation-as-continuous-process.png "evaluation-as-continuous-process.png")
# MAGIC
# MAGIC 包括的なテストスイートが安定した品質シグナルを提供する従来のソフトウェアとは異なり、AIエージェントの評価は継続的なプロセスです：
# MAGIC
# MAGIC **開発段階**：迅速な反復には、変更がリグレッションを引き起こすことなく品質を向上させることを検証するための頻繁な評価が必要です。
# MAGIC
# MAGIC **デプロイ前検証**：多様なテストケースにわたる包括的な評価により、エージェントが本番環境リリース前に品質基準を満たすことを保証します。
# MAGIC
# MAGIC **本番環境モニタリング**：ライブインタラクションの継続的評価により、品質劣化、新たな失敗パターン、改善の機会を特定します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. 継続的評価が重要な理由
# MAGIC
# MAGIC この継続的評価サイクルは、評価インフラストラクチャがスケーラブルで自動化され、開発ワークフローに統合されている必要があることを意味します。評価フレームワークは以下をサポートする必要があります：
# MAGIC
# MAGIC - 開発中の **迅速なフィードバックループ**
# MAGIC - デプロイ前の **包括的な検証**
# MAGIC - 本番環境での **継続的なモニタリング**
# MAGIC - **データセットの変遷**：利用パターンの変化に伴い

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. 評価の準備

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 準備が重要な理由
# MAGIC
# MAGIC 評価フレームワークを使用する前に、評価を目的に適ったものにし、再現可能にすることが重要です。AIエージェントは非決定論的で文脈依存であるため、従来のアサーション形式のテストは不十分です。代わりに、効果的な評価には品質次元の定義、代表的なデータセットの組み立て、ジャッジが答えだけでなく、その答えがどのように生成されたかを評価できるようにするトレーシングの有効化が必要です。
# MAGIC
# MAGIC 目標の明確化、データセットのキュレーション、適切なジャッジの事前選択により、メトリクスが実際のユーザーニーズを反映し、失敗が合格/不合格スコアだけでなく、トレースと根拠を通じて診断可能なフィードバックループを作成します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. 評価データセットの設計
# MAGIC
# MAGIC ![designing-evaluation-datasets.png](../Includes/images/Evaluation with MLflow/designing-evaluation-datasets.png "designing-evaluation-datasets.png")
# MAGIC
# MAGIC 評価データセットは、テストする内容とシグナルの信頼性を定義します。最低限、入力（クエリ）と、適切な場合は期待される答え、行ごとのガイドライン、取得とツール使用を反映するメタデータを含む必要があります。
# MAGIC
# MAGIC **主要な原則：**
# MAGIC
# MAGIC - **代表性：** オフライン結果が本番環境に汎化するよう、一般的で影響の大きいユーザークエリを含める
# MAGIC - **エッジケース：** 曖昧で範囲外の敵対的プロンプトを追加して、失敗モードを早期に表面化させる
# MAGIC - **多様性：** 長さ、複雑さ、ドメイン、ユーザーの専門知識を変化させて、推論と取得の盲点を露呈させる
# MAGIC - **グラウンドトゥルースおよび/またはガイドライン：** 客観的な質問には期待される答えや事実セットを使用；スタイル、ポリシー、完全性が重要な場合は自然言語ガイドラインを使用
# MAGIC - **ストレージとバージョニング：** データセットをJSONまたはDataFrames（理想的にはDelta/Unity Catalog）として保存し、エージェントと共に進化させる

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 運用セットアップ要件
# MAGIC
# MAGIC 結果が比較可能で監査可能になるよう、一貫した基盤を確立します：
# MAGIC
# MAGIC - **MLflowエクスペリメントとラン：** 安定したエクスペリメント名を使用；エージェントバージョン、データセットバージョン、パラメータでランにタグ付け；UIでメトリクスを比較し、例ごとのアーティファクトを検査
# MAGIC - **Unity Catalog統合：** アクセス制御、バージョニング、リネージでデータセットとトレースを管理；エンドツーエンドのトレーサビリティのためにエージェントと依存関係を登録
# MAGIC - **本番環境フィードバックループ（事前計画）：** デプロイ後、AI Gatewayの推論テーブルを有効にして、リクエスト、レスポンス、トレースをログに記録し、モニタリングと新しい評価例の発掘を行う

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. 重要なポイント
# MAGIC
# MAGIC 従来のソフトウェアテスト手法は、AIエージェントの非決定論的、創発的、文脈依存の性質により根本的に不適切です。効果的なエージェント評価には以下が必要です：
# MAGIC
# MAGIC 1. **独特の課題の認識**：非決定論、創発的行動、文脈依存性には専門的な評価手法が必要
# MAGIC 2. **継続的評価の考え方**：評価は一回限りの検証ステップではなく、継続的なプロセス
# MAGIC 3. **適切な準備**：成功は思慮深いデータセット設計、明確な品質定義、堅牢な運用セットアップに依存
# MAGIC 4. **体系的手法**：評価インフラストラクチャはスケーラブルで自動化され、開発ワークフローに統合されている必要がある
# MAGIC
# MAGIC これらの課題を理解することは、効果的なエージェント評価を実装するための基盤です。次の講義では、これらの課題に体系的に対処するツールと技術を探ります。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ デモチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">デモチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>01 Demo - Agent Setup</strong>というタイトルの最初のデモに移動し、このトレーニング全体で使用されるエージェントとUC資産のセットアップを開始してください。完了したら、この講義ノートブックに戻って学習を続けてください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>