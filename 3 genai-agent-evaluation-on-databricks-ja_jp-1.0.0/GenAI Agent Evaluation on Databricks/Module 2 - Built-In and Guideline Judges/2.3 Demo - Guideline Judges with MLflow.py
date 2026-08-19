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

# MAGIC %md-sandbox
# MAGIC # デモ - MLflowでのガイドラインジャッジ
# MAGIC
# MAGIC **概要** 
# MAGIC
# MAGIC このデモでは、生成AI アプリケーションを評価するためのMLflowでのガイドラインジャッジの実装と使用方法を探ります。ガイドラインジャッジは、自然言語による基準を使用してカスタムビジネスルールと品質基準に対してAI出力を評価する強力な方法を提供します。
# MAGIC
# MAGIC **学習目標**
# MAGIC
# MAGIC このデモの終了時には、以下のことができるようになります：
# MAGIC
# MAGIC - MLflowにおけるグローバルガイドラインジャッジと行ごとガイドラインジャッジの違いを理解する
# MAGIC - 統一的な評価基準のために組み込み `Guidelines()` ジャッジを実装する
# MAGIC - シナリオ固有の評価のために `ExpectationsGuidelines()` ジャッジを適用する
# MAGIC - コンテキスト変数を参照する効果的な自然言語ガイドラインを作成する
# MAGIC - AIシステムのオフライン評価とオンライン評価のアプローチを区別する
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">前提条件</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;"> このデモは<strong>01 - エージェントセットアップ</strong>で作成されたエージェントを使用します。続行する前に、そのノートブックを完了していることを確認してください。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## 必須 - サーバーレス コンピュートを選択
# MAGIC
# MAGIC このノートブックでセルを実行する前に、ノートブックを **サーバーレス コンピュート** にアタッチしてください。
# MAGIC
# MAGIC **注意：** このデモは **サーバーレス（バージョン5）** でテストされています。  
# MAGIC サーバーレス バージョンを確認または変更するには、サーバーレス依存関係に関するDatabricksドキュメントを参照してください。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### コンピュート要件
# MAGIC
# MAGIC このコースはサーバーレス コンピュートで実行するように構成されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバーレスで実行されています。
# MAGIC
# MAGIC **このデモではサーバーレス コンピュートはバージョン5である必要があります。** 正しいバージョンを使用していることを確認するには、[ノートブックのサーバーレス バージョンの表示と変更に関するこちらのドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)を参照してください。
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;">必須 - サーバーレス コンピュートを選択</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;">続行する前に、このノートブックをサーバーレス コンピュート リソースにアタッチする必要があります。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### クラスルームセットアップ
# MAGIC
# MAGIC このコースの作業環境を設定するために、以下のセルを実行してください。
# MAGIC
# MAGIC このセットアップでは以下が実行されます：
# MAGIC - `DA` オブジェクト（Databricks Academyヘルパー）の初期化
# MAGIC - **デフォルト カタログ** と **スキーマ** の設定
# MAGIC - このデモに必要なサポート設定のプロビジョニング
# MAGIC
# MAGIC **注意：** `DA` オブジェクトはDatabricks Academyコースでのみ利用可能です

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-3

# COMMAND ----------

# MAGIC %md
# MAGIC ## パート1. ガイドラインジャッジの理解
# MAGIC
# MAGIC ガイドラインジャッジは、AI応答がカスタムの自然言語ルールに合格または不合格するかを評価するMLflowの組み込みコンポーネントです。これらのジャッジは、コンプライアンス要件、スタイルガイドライン、事実の正確性、コンテンツの適切性などのビジネスクリティカルな側面の評価に優れています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. 利用可能なガイドラインジャッジの種類
# MAGIC
# MAGIC MLflowは2つの主要なガイドラインジャッジ実装を提供します：
# MAGIC
# MAGIC 1. **組み込み `Guidelines()` ジャッジ**: 評価データセット内のすべての行に対してグローバルガイドラインを統一的に適用します。このジャッジはアプリケーションの入力と出力を評価し、オフライン評価と本番監視の両方のシナリオで動作します。
# MAGIC
# MAGIC 2. **組み込み `ExpectationsGuidelines()` ジャッジ**: 評価データセット内でドメインエキスパートによってラベル付けされた行ごとのガイドラインを適用します。このアプローチはアプリケーションの入力と出力を評価しますが、特にオフライン評価ワークフロー用に設計されています。
# MAGIC
# MAGIC 両方のジャッジは、指定された基準に基づいて合格/不合格の判定を行うために特別に調整された大規模言語モデルを使用します。

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 1.2. オフライン評価 vs. オンライン評価
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">オフライン評価 vs. オンライン評価</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;"><strong>オフライン評価</strong>は、ベンチマークデータセットと参照メトリクスを使用してデプロイ前にAIシステムをテストすることに焦点を当てており、一方で<strong>オンライン評価</strong>は、デプロイ後に実際のユーザーからリアルワールドのフィードバックを収集し、ライブ使用状況とパフォーマンスを追跡します。オフライン手法はシステムが意図通りに動作することを検証し、オンライン手法は実際にどの程度うまく動作しているかを明らかにし、継続的な改善を推進します。</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. ガイドラインジャッジの動作原理
# MAGIC
# MAGIC ガイドラインジャッジは、テキストが指定された基準を満たすかどうかを評価するために特別に調整されたLLMを使用して動作します。評価プロセスは以下の主要なステップに従います：
# MAGIC
# MAGIC 1. **コンテキストの受信**: ジャッジは、リクエスト、レスポンス、retrieved_documents、user_preferencesなど、評価するデータを含むJSONディクショナリを受け入れます
# MAGIC 2. **ガイドラインの適用**: 自然言語ルールを使用して合格/不合格条件を定義します
# MAGIC 3. **判定の実行**: ジャッジは、決定を説明する詳細な根拠とともにバイナリの合格/不合格スコアを返します
# MAGIC
# MAGIC ジャッジは、アプリケーショントレースからリクエストとレスポンスデータを自動的に抽出するため、複雑なデータ前処理なしでリアルワールドのAIインタラクションを簡単に評価できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.4. 評価データセットの読み込み
# MAGIC
# MAGIC 次のセルを実行して、Unity Catalogの `agent_vol` から評価データセットを読み取るヘルパー関数を作成します。これらのデータセットは後で使用します。これらのデータセットを少し時間をかけて調べ、それぞれで使用されている異なるフィールドを比較対照してください。それぞれが以下に示される異なるユースケースをカバーしているためです。

# COMMAND ----------

import json 

def read_eval_from_vol(file_name:str):
    path = Path(f"/Volumes/{catalog_name}/{schema_name}/agent_vol/{file_name}")

    with path.open("r", encoding="utf-8") as f:
        dataset = json.load(f)

    return dataset

guidelines_dataset = read_eval_from_vol("guidelines_eval.json")
guidelines_dataset_pre_gen = read_eval_from_vol("guidelines_eval_pre_gen.json")
guidelines_dataset_row_level = read_eval_from_vol("guidelines_eval_row_level.json")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.5. サンプルデータセットの検査
# MAGIC
# MAGIC 次のセルを実行して、`guidelines_dataset` のフォーマットされたビューを印刷します。

# COMMAND ----------

from pprint import pprint

pprint(guidelines_dataset)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## パート2. グローバルガイドラインの実装
# MAGIC
# MAGIC 次に、いくつかのガイドラインを初期化します。`Guidelines()` ジャッジは、評価データセット（`guidelines_dataset` で定義）内の_すべての行_に対して統一的なガイドラインを適用します。このアプローチは、すべてのAIインタラクションに適用すべき一貫した品質基準がある場合に理想的です。次のセルを実行して、エージェントのトーンに関連するガイドラインスコアラーを定義します。
# MAGIC
# MAGIC このデモは `mlflow.genai.scorers` に集中するため、各評価（`scorers` モジュール用）が3つのコンポーネントによって定義されることに注意することが重要です：
# MAGIC - **データセット**: 入力と期待値（およびオプションで事前生成された出力とトレース）
# MAGIC - **スコアラー**: 評価基準
# MAGIC - **予測関数**: データセットの出力を生成する
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC   <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC     <div>
# MAGIC       <strong style="color: #0d47a1; font-size: 1.1em;">注意</strong>
# MAGIC       <p style="margin: 8px 0 0 0; color: #333;">
# MAGIC         MLflowのGenAI評価システムについて詳しくは
# MAGIC         <a
# MAGIC           href="https://mlflow.org/docs/latest/genai/eval-monitor/#running-an-evaluation"
# MAGIC           target="_blank"
# MAGIC           rel="noopener noreferrer"
# MAGIC           style="color: #1976d2; text-decoration: underline;"
# MAGIC         >
# MAGIC           こちら
# MAGIC         </a>をお読みください。
# MAGIC       </p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

from mlflow.genai.scorers import Guidelines
language_guideline = Guidelines(
    name="spanish",
    guidelines=["The response should be in Spanish"],
    model_name = guidelines_endpoint
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1. 基本的なグローバルガイドラインの実装
# MAGIC
# MAGIC グローバルガイドラインは、すべての評価に統一的に適用されるルールを定義することで動作します。ジャッジは自動的に `request`（入力から）と `response`（出力から）を抽出して評価コンテキストを作成します。次のセルを実行して、`language_guideline` で定義されたグローバルガイドラインで評価します。レスポンスがスペイン語ではなく英語になるため、両方の入力が失敗することに注意してください。

# COMMAND ----------

guidelines_dataset_results = mlflow.genai.evaluate(
    data=guidelines_dataset,
    predict_fn= lambda input: agent.predict({"input": input}),
    scorers=[language_guideline]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.2. グローバルガイドライン結果の検査
# MAGIC
# MAGIC 以下に示すように `guidelines_results` オブジェクトを検査できます。各行をクリックすると、その特定のトレースのMLflowインターフェースが表示されることに注意してください。また、結果がスペイン語に翻訳されなかったため（システムプロンプトの一部として含めていない、または入力の一部として注入していない）、両方の入力が失敗したことが評価に表示されることに注意してください。

# COMMAND ----------

print(f"The run ID is: {guidelines_dataset_results.run_id}")
print(f"The aggregated metrics are: {guidelines_dataset_results.metrics}")
print("\nThe results from the previous batch of inputs:")
display(guidelines_dataset_results.result_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.3. 事前生成された入力/出力の評価
# MAGIC
# MAGIC 次に、評価したい事前生成された入力と出力のデータセットがある場合を考えてみましょう。これは `agent_vol` の `guidelines_eval_pre_gen.json` ファイルに保存されています（データセット自体を表示したい場合）。基本的に、何らかの入力に基づくスペイン語レスポンスの評価をテストしています。最初のデータポイントは正しくスペイン語翻訳を返しましたが、2番目は返しませんでした。
# MAGIC
# MAGIC 次の2つのセルを実行し、前と同様に **MLflowで評価結果を表示** をクリックして評価を表示してください。すでにエージェントのレスポンス（入力と出力）が評価データセット `guidelines_eval_pre_gen.json` に保存されているため、`mlflow.genai.evaluate()` で `predict_fn` でエージェントを渡していないことに注意してください。

# COMMAND ----------

guidelines_dataset_pre_gen_results = mlflow.genai.evaluate(
    data=guidelines_dataset_pre_gen,
    scorers=[language_guideline]
)

# COMMAND ----------

print(f"The run ID is: {guidelines_dataset_pre_gen_results.run_id}")
print(f"The aggregated metrics are: {guidelines_dataset_pre_gen_results.metrics}")
print("\nThe results from the previous batch of inputs:")
display(guidelines_dataset_pre_gen_results.result_df)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## パート3. エッジケース用の行ごとガイドラインの実装
# MAGIC
# MAGIC `ExpectationsGuidelines` ジャッジは、データセット内の各行に異なるガイドラインを適用することで、シナリオ固有の評価を可能にします。上記と同様に、次の2つのセルを実行して `mlflow.genai.evaluate()` を使用した評価を実行し、評価からメタデータを表示します。この特定のデータセットでは、1つの行が評価に合格し、1つが不合格になることがわかります。次のセルを実行した後、前と同様にトレースを表示して推論を表示し、理解してください。
# MAGIC
# MAGIC このアプローチは、異なるタイプのインタラクションが異なる評価基準を必要とし、細かい要件がある場合に特に価値があります。
# MAGIC
# MAGIC <div style="border-left: 4px solid #f44336; background: #ffebee; padding: 16px 20px; border-radius: 4px; margin: 16px 0;">
# MAGIC <div style="display: flex; align-items: flex-start; gap: 12px;">
# MAGIC <div>
# MAGIC <strong style="color: #c62828; font-size: 1.1em;"> `ExpectationsGuidelines` スコアラーには `outputs` フィールドが必要です。</strong>
# MAGIC <p style="margin: 8px 0 0 0; color: #333;"> これらは直接渡すか、それらを含むトレースとして渡すことができます。直接渡します。</p>
# MAGIC </div>
# MAGIC </div>
# MAGIC </div>

# COMMAND ----------

from mlflow.genai.scorers import ExpectationsGuidelines

expected_guidelines = ExpectationsGuidelines(
    name="expected_guidelines",
    model_name = guidelines_endpoint
)

guidelines_dataset_row_level_results = mlflow.genai.evaluate(
    data = guidelines_dataset_row_level,
    scorers=[expected_guidelines]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 行ごとガイドライン結果の検査
# MAGIC
# MAGIC `per_row_results.results_df` を使用して `assessment` カラムを表示するか、前と同様に興味のある行をクリックして推論を表示することもできることに注意してください。

# COMMAND ----------

print(f"The run ID is: {guidelines_dataset_row_level_results.run_id}")
print(f"The aggregated metrics are: {guidelines_dataset_row_level_results.metrics}")
print("\nThe results from the previous batch of inputs:")
display(guidelines_dataset_row_level_results.result_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. 行ごとガイドラインを使用する場合
# MAGIC
# MAGIC 行ごとガイドラインは以下の場合に最も効果的です：
# MAGIC - カスタムガイドラインで特定の例をラベル付けしたドメインエキスパートがいる場合
# MAGIC - データセット内の異なる行が異なる評価基準を必要とする場合
# MAGIC - AIシステムがさまざまなエッジケースや特殊なシナリオをどのように処理するかをテストする必要がある場合
# MAGIC - 評価データセットに、それぞれ独自の品質要件を持つ多様なインタラクションタイプが含まれている場合

# COMMAND ----------

# MAGIC %md
# MAGIC ##結論
# MAGIC
# MAGIC ガイドラインジャッジは、自然言語基準を使用して生成AIアプリケーションを評価する強力で直感的な方法を提供します。グローバルガイドラインと行ごとガイドラインの両方を実装することで、ビジネス要件と品質基準に合致する包括的な評価フレームワークを作成できます。
# MAGIC
# MAGIC ガイドラインジャッジの主な利点には、ビジネスフレンドリーなアプローチ（ドメインエキスパートがコーディングなしで基準を書ける）、コード変更なしで基準を更新する柔軟性、結果の明確な解釈可能性、評価基準の迅速な反復のサポートが含まれます。
# MAGIC
# MAGIC すべてのインタラクションに対する統一的な品質基準を実装する場合でも、シナリオ固有の評価基準が必要な場合でも、MLflowのガイドラインジャッジは、AIアプリケーションが組織のコンプライアンス、スタイル、正確性、全体的な品質の基準を満たすことを保証するために必要なツールを提供します。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>