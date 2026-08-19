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
# MAGIC # 講義 - ベストプラクティスと実用的な応用
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC この最終講義では、エージェント評価のベストプラクティスを統合し、実用的な実装のためのガイダンスを提供します。包括的な評価のためのヒント、MLflowエコシステム統合の理解、そして実世界のシナリオにこれらの概念を適用する方法について探求します。
# MAGIC
# MAGIC この講義では、評価は深くコンテキストに依存することを強調し、自身のアプリケーション、ユーザー、ビジネスニーズに特有の評価要件について考えるためのフレームワークを提供します。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC この講義の終わりまでに、以下ができるようになります：
# MAGIC - 包括的なエージェント評価のベストプラクティスを適用する
# MAGIC - MLflowがより広範な評価エコシステムとどのように統合するかを理解する
# MAGIC - 自身のユースケースに対する評価戦略設計のための主要な質問を特定する
# MAGIC - 評価を一回限りの活動ではなく継続的な規律として認識する
# MAGIC - 継続的改善をサポートする評価インフラストラクチャを計画する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. エージェント評価のヒント

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. 包括的な評価戦略
# MAGIC
# MAGIC ![tips-for-agent-evaluation.png](../Includes/images/Evaluation with MLflow/tips-for-agent-evaluation.png "tips-for-agent-evaluation.png")
# MAGIC
# MAGIC 効果的なエージェント評価には、品質の複数の次元、多様な評価シナリオ、継続的改善のための体系的なプロセスを考慮する総合的なアプローチが必要です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 多次元品質評価
# MAGIC
# MAGIC **考慮すべき品質の次元：**
# MAGIC
# MAGIC - **正確性**：回答の事実的な主張は正確か？
# MAGIC - **関連性**：回答はユーザーの実際の質問に対応しているか？
# MAGIC - **完全性**：回答は冗長でなく十分に詳細か？
# MAGIC - **安全性**：回答は有害または不適切なコンテンツを含まないか？
# MAGIC - **一貫性**：類似のクエリに対して類似の品質の回答を受け取るか？
# MAGIC - **効率性**：エージェントはツールとリソースを適切に使用するか？
# MAGIC - **ユーザー体験**：回答は役立ち、明確で、適切にフォーマットされているか？

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. 評価データセットのベストプラクティス
# MAGIC
# MAGIC **堅牢な評価データセットの構築：**
# MAGIC
# MAGIC 1. **ユーザー調査から始める**：実際のユーザークエリと問題点を分析する
# MAGIC 2. **失敗事例を含める**：エージェントが拒否またはリダイレクトすべきシナリオをテストする
# MAGIC 3. **複雑さを変える**：シンプルな検索から複雑な多段階推論まで含める
# MAGIC 4. **境界をテストする**：エッジケースと曖昧なクエリを含める
# MAGIC 5. **多様性を維持する**：異なるドメイン、クエリスタイル、ユーザータイプをカバーする
# MAGIC 6. **体系的にバージョン管理する**：エージェントバージョンと併せてデータセットの変更を追跡する
# MAGIC 7. **定期的に検証する**：正解が正確で関連性を保っていることを確認する

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. 評価ワークフローのベストプラクティス
# MAGIC
# MAGIC **体系的な評価プロセス：**
# MAGIC
# MAGIC - **可能な限り自動化する**：CI/CDパイプラインを使用してコード変更時に評価を実行する
# MAGIC - **品質ゲートを設定する**：デプロイメントの最小しきい値を定義する
# MAGIC - **体系的に比較する**：ベースラインパフォーマンスに対して常に変更を評価する
# MAGIC - **根拠を文書化する**：評価決定の背後にある推論を記録する
# MAGIC - **結果を共有する**：評価結果をステークホルダーがアクセスできるようにする
# MAGIC - **洞察に基づいて行動する**：評価結果を使用して具体的な改善を推進する

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. MLflow評価エコシステム

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. エコシステム統合
# MAGIC
# MAGIC ![mlflow-ecosystem.png](../Includes/images/Evaluation with MLflow/mlflow-ecosystem.png "mlflow-ecosystem.png")
# MAGIC
# MAGIC MLflow評価は、開発から本番環境モニタリングまで包括的な評価機能を提供するため、より広範なDatabricksエコシステムと統合されています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. MLflow実験と実行
# MAGIC
# MAGIC MLflow実験は評価結果を整理し、エージェントの反復間での比較と分析を可能にします。
# MAGIC
# MAGIC **実験構造：**
# MAGIC
# MAGIC `mlflow.genai.evaluate()` への各評価呼び出しは、実験内で実行を作成します：
# MAGIC - **実行** は特定の設定での個別の評価実行を表します
# MAGIC - **実験** は比較のために関連する評価実行をグループ化します
# MAGIC - **メトリクス** は実行レベル（集計スコア）でログされます
# MAGIC - **アーティファクト** には詳細な例ごとの結果と評価データセットが含まれます

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 比較と分析のベストプラクティス
# MAGIC
# MAGIC **比較機能：**
# MAGIC
# MAGIC MLflow UIは体系的な比較を可能にします：
# MAGIC - 実行間でメトリクスを比較して改善を定量化する
# MAGIC - 時間の経過に伴うメトリクスの傾向を視覚化する
# MAGIC - タグ、パラメータ、またはメトリクスで実行をフィルタリングする
# MAGIC - 外部分析のために結果をエクスポートする
# MAGIC
# MAGIC **ベストプラクティス：**
# MAGIC
# MAGIC - 一貫した実験命名規則を使用する
# MAGIC - 意味のあるメタデータで実行にタグを付ける（エージェントバージョン、設定、データセットバージョン）
# MAGIC - ハイパーパラメータと設定を実行パラメータとしてログする
# MAGIC - 実行コンテキストと発見を文書化する説明的なノートを追加する

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. 実用的応用フレームワーク

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. 自身のユースケースのための主要な質問
# MAGIC
# MAGIC デモンストレーションを進める際に、これらの概念があなた自身のユースケースにどのように適用されるかを考えてください：
# MAGIC
# MAGIC **思考を導く質問：**
# MAGIC - 自身のアプリケーションにとって最も重要な品質の次元は何ですか？
# MAGIC - 本番で最も問題となる失敗モードはどれですか？
# MAGIC - 実際の使用を反映する評価データセットをどのように収集しますか？
# MAGIC - 評価基準を知らせることができる既存のシステムやプロセスは何ですか？
# MAGIC - 開発ワークフローに評価をどのように統合しますか？
# MAGIC - 本番環境モニタリングでどのメトリクスを追跡しますか？

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. コンテキスト依存の評価
# MAGIC
# MAGIC 効果的な評価は深くコンテキストに依存します。MLflowは強力なツールを提供しますが、自身の特定のアプリケーション、ユーザー、ビジネス要件にとって「良い」とは何かを定義する必要があります。
# MAGIC
# MAGIC **自身のコンテキストを考慮してください：**
# MAGIC
# MAGIC - **ドメイン要件**：医療、法律、または金融アプリケーションでは専門的な評価基準が必要な場合があります
# MAGIC - **ユーザーの期待**：専門家ユーザーは一般消費者とは異なる回答スタイルを期待する場合があります
# MAGIC - **リスク許容度**：高リスクアプリケーションは実験的ツールよりも厳格な評価が必要です
# MAGIC - **リソース制約**：開発速度と評価の徹底さのバランスを取る
# MAGIC - **規制要件**：一部のドメインでは特定のコンプライアンスまたは監査機能が必要です

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. 実装計画
# MAGIC
# MAGIC **評価実装の計画：**
# MAGIC
# MAGIC 1. **シンプルに始める**：基本的な組み込みジャッジから始めて徐々に拡張する
# MAGIC 2. **ステークホルダーを特定する**：ドメイン専門家、ユーザー、ビジネスステークホルダーを含める
# MAGIC 3. **成功メトリクスを定義する**：明確で測定可能な品質基準を確立する
# MAGIC 4. **インフラストラクチャを計画する**：ストレージ、コンピュート、ガバナンス要件を考慮する
# MAGIC 5. **フィードバックループを設計する**：評価結果を開発プロセスに接続する
# MAGIC 6. **スケールに備える**：評価インフラストラクチャがニーズと共に成長できることを確認する

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. 継続的な規律としての評価

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 継続的改善の考え方
# MAGIC
# MAGIC 評価は一回限りの活動ではなく、継続的な規律であることを覚えておいてください。エージェントが進化し、使用パターンが変化し、理解が深まるにつれて、評価アプローチも進化すべきです。MLflowの柔軟なフレームワークは、厳密さと再現性を維持しながら、この継続的改善をサポートします。
# MAGIC
# MAGIC **進化の推進要因：**
# MAGIC
# MAGIC - **エージェント機能**：新機能には新しい評価基準が必要です
# MAGIC - **ユーザー行動**：使用パターンの変化にはデータセットの更新が必要です
# MAGIC - **ビジネス要件**：優先順位の変化により品質の定義が変わる場合があります
# MAGIC - **技術的進歩**：新しい評価技術が利用可能になります
# MAGIC - **学んだ教訓**：本番経験が評価の改善を知らせます

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. 評価文化の構築
# MAGIC
# MAGIC **評価の卓越性を促進する：**
# MAGIC
# MAGIC - **評価を可視化する**：チーム間で結果と洞察を共有する
# MAGIC - **改善を称賛する**：評価によって推進された品質改善を認識する
# MAGIC - **失敗から学ぶ**：評価の失敗を学習機会として使用する
# MAGIC - **ツールに投資する**：チームに優れた評価インフラストラクチャを提供する
# MAGIC - **チームメンバーを訓練する**：全員が評価の原則と実践を理解することを確認する

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. 今後の展望

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. 品質の基盤
# MAGIC
# MAGIC AIエージェントの品質は、最終的に評価の品質に依存します。堅牢な評価インフラストラクチャの構築に早期に投資すれば、開発から本番、そしてその先まで、エージェントのライフサイクル全体を通じて利益を得ることができます。
# MAGIC
# MAGIC **良い評価の長期的利益：**
# MAGIC
# MAGIC - **開発の高速化**：迅速なフィードバックにより高速な反復が可能になります
# MAGIC - **高品質**：体系的な評価により問題を早期に発見できます
# MAGIC - **ユーザーの信頼**：一貫した品質がユーザーの信頼を構築します
# MAGIC - **運用効率**：自動化された評価により手動テストが削減されます
# MAGIC - **継続的改善**：データ駆動の最適化が可能になります

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. 次のステップ
# MAGIC
# MAGIC これで体系的なエージェント評価を実装するための概念的基盤ができました。今後のデモンストレーションでは、これらの概念を実践的なスキルに変換し、実際のエージェントを評価し、結果を解釈し、品質改善を推進する方法を正確に示します。
# MAGIC
# MAGIC **評価の旅：**
# MAGIC
# MAGIC 1. **概念を適用する**：実践的なデモンストレーションに取り組む
# MAGIC 2. **自身のコンテキストに適応する**：自身の特定の要件と制約を考慮する
# MAGIC 3. **シンプルに始める**：基本的な評価を実装し、徐々に拡張する
# MAGIC 4. **測定し改善する**：評価結果を使用して具体的な改善を推進する
# MAGIC 5. **共有し学ぶ**：評価機能を構築している他の人と協力する

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ⚠️ ラボチェックポイント
# MAGIC <div style="border-left: 4px solid #ff9800; background: #fff3e0; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <span style="font-size: 24px;"></span>
# MAGIC     <div>
# MAGIC       <strong style="color: #e65100; font-size: 1.1em;">ラボチェックポイント</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>06 Lab - Developer and SME Feedback with MLflow</strong>に移動して、人間のフィードバック機能を探索し、評価学習の旅を完了してください。完了したら、結論のためにこの講義ノートブックに戻ってください。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. 結論
# MAGIC
# MAGIC 効果的なエージェント評価は芸術でもあり科学でもあります。評価フレームワークの技術的理解、品質基準を定義するドメイン専門知識、継続的改善を確保する体系的プロセスが必要です。
# MAGIC
# MAGIC MLflowは技術的基盤を提供しますが、成功は自身の特定のコンテキストへのこれらのツールの思慮深い適用に依存します。厳格なオフライン評価と包括的なオンライン監視を組み合わせることで、ユーザーに一貫して高品質な体験を提供するエージェントを構築できます。
# MAGIC
# MAGIC 評価インフラストラクチャへの投資は、エージェントのライフサイクル全体を通じて配当をもたらします。今日から評価機能の構築を始めれば、ユーザーのニーズを満たし、期待を上回る高品質なAIエージェントを開発、デプロイ、維持するのに適した立場に立つことができます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>