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
# MAGIC # デモ - MLflowを使用したシングルエージェントのトレーシング
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC 本番環境でAIエージェントを構築・デプロイする際、オブザーバビリティは重要です。エージェントが何を行っているか、どのようなパフォーマンスを発揮しているか、どこで問題が発生するかを理解することで、デプロイメントの成功と失敗を分けることができます。このデモでは、シングルエージェントアプリケーション向けのMLflowのトレーシング機能について説明し、AIシステムの監視、デバッグ、最適化に必要なツールを提供します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC _このデモの終了時には、以下ができるようになります：_
# MAGIC
# MAGIC - エージェントトレーシング用にデフォルトとカスタムの両方のアーティファクトロケーションでMLflowエクスペリメントを設定する
# MAGIC - `mlflow.langchain.autolog()` を使用してLangChainエージェントの自動トレーシングを実装する
# MAGIC - トークン数、レイテンシメトリクス、実行タイムラインを含むトレース出力を解釈する
# MAGIC - `@mlflow.trace` デコレータを適用してPython関数にカスタムトレーシングを追加する
# MAGIC - 複雑な多段階エージェントworkflowsにおける親子スパン関係を分析する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境設定

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバレスコンピュートを選択**
# MAGIC
# MAGIC このコースはサーバレスコンピュートで動作するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバレスで実行されています。
# MAGIC
# MAGIC **このデモはサーバレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバレスを使用していることを確認するには、[ノートブックのサーバレスバージョンの表示と変更に関するドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC
# MAGIC ワークスペース設定の一環として、いくつかのPythonライブラリをインストールする必要があります。次のセルを実行してインストールしてください。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-3.1

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. Airbnbデータセットの確認
# MAGIC クラスルーム設定の一環として、AirbnbデータセットがUnity Catalog内のDeltaテーブルとして処理・保存されています。次のセルを実行してデータセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('sf_airbnb_listings')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### A4. MLflow自動ログの初期化
# MAGIC
# MAGIC MLflowの自動ログは、LangChainなどのサポートされたframeworksのトレースを自動的にキャプチャします。有効にすると、手動での計測を必要とせずに、入力、出力、パラメータ、メトリクスなどを記録します。詳細については、この[リンク](https://mlflow.org/docs/latest/genai/flavors/langchain/autologging/)をご覧ください。

# COMMAND ----------

import mlflow

mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ### A5. エクスペリメントロケーションの定義
# MAGIC
# MAGIC 異なるアーティファクトストレージアプローチを実証するために、2つのエクスペリメント設定を作成します：
# MAGIC
# MAGIC 1. **Default location**: デフォルトのワークスペースロケーションにアーティファクトを保存
# MAGIC 2. **Custom location**: Unity Catalogボリュームにアーティファクトを保存

# COMMAND ----------

# ユーザー名を取得
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()

experiment_name_1 = f"/Workspace/Users/{username}/single_agents_demo1" 
experiment_name_2 = f"/Workspace/Users/{username}/single_agents_demo2" 

artifact_path = f"dbfs:/Volumes/{catalog_name}/{schema_name}/agent_vol"

print(f"Experiment 1 name: {experiment_name_1}")
print(f"Experiment 2 name: {experiment_name_2}")
print(f"Artifact location: {artifact_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. エージェントトレースの理解
# MAGIC
# MAGIC 実装に入る前に、トレースとは何か、そしてなぜエージェントのオブザーバビリティに不可欠なのかを理解しましょう。
# MAGIC
# MAGIC トレースは、各ステップを「スパン」としてキャプチャすることで、AIアプリケーション内で何が起こっているかを可視化します。トレースは詳細なレシートのようなもので、モデルに何を尋ねたか、何を応答したか、どのくらい時間がかかったか、トークンでどのくらいのコストがかかったかを示します。
# MAGIC
# MAGIC - **シンプル** なアプリの場合、パフォーマンスとコストを一目で理解するのに役立ちます。
# MAGIC - エージェントやRAGシステムのような **複雑な多段階** アプリケーションの場合、トレースは各コンポーネントがどのように連携するかを正確に明らかにし、問題のデバッグとアプリケーションの最適化を容易にすることで、さらに強力になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. MLflowエクスペリメントでの自動トレーシング
# MAGIC
# MAGIC MLflowは、エクスペリメントデータとアーティファクトの保存場所を設定するために、`set_experiment()` と `create_experiment()` の2つの方法を提供します。両方のアプローチを見てみましょう。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. デフォルトアーティファクトロケーションでのトレーシング
# MAGIC
# MAGIC `set_experiment()` を使用すると、デフォルトのワークスペースロケーションにアーティファクトが保存されるエクスペリメントが作成されます。このアプローチは簡単で、開発とテストに適しています。
# MAGIC
# MAGIC **注意:** これはモデルをUnity Catalogに登録するものでは _ありません_。単にトレースを記録するだけです。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 1. 次のセルを実行して出力を確認してください。
# MAGIC 2. ユーザーフォルダに移動して、エクスペリメント `single_agents_demo1` を確認してください。このエクスペリメントをクリックしても、まだエージェントを呼び出していないためトレースは見つからないことに注意してください。次にこれを行います。

# COMMAND ----------

mlflow.set_experiment(experiment_name_1)

artifact_location = mlflow.get_experiment_by_name(experiment_name_1).artifact_location

print(f"Artifact location: {artifact_location}")

# COMMAND ----------

# MAGIC %md
# MAGIC #### C1.1 エージェントの読み込み
# MAGIC
# MAGIC 次に、`demo_agent1` という `.py` ファイルで定義されたシンプルなエージェントを読み込みます。
# MAGIC
# MAGIC #### エージェントは何をするのか？
# MAGIC
# MAGIC `demo_agent1.py` モジュールは、Unity Catalog関数をツールとして呼び出すことができる対話型AIエージェントを作成する `DatabricksAgent` クラスを定義します。JSONファイル（LLM endpoint、温度、システムプロンプト、ツールリストを含む）から設定を読み込み、提供されたカタログとスキーマを使用して完全修飾関数名を構築し、LangChainエージェントエグゼキューターを設定します。このクラスは、自然言語プロンプトを使用してエージェントと対話するための `query()` と `ask()` メソッドを提供し、会話コンテキスト用のオプションのチャット履歴サポートも含まれています。

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

import demo_agent1
agent = demo_agent1.DatabricksAgent(
    catalog_name=catalog_name,
    schema_name=schema_name
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### C1.2 トレーシングでのエージェントテスト
# MAGIC
# MAGIC エージェントにプロンプトを送信し、結果のトレースを確認します。

# COMMAND ----------

prompt = "Get the average for Mission."

# COMMAND ----------

# MAGIC %md
# MAGIC 1. 次のセルを実行して、`ask()` メソッドを使用してエージェントにプロンプトを渡してください。
# MAGIC 2. セルの下に表示されるトレース出力を確認してください。

# COMMAND ----------

agent.ask(prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC #### C1.3 トレース出力の分析
# MAGIC
# MAGIC トレース出力は、エージェントの実行に関する豊富な情報を提供します。利用可能な内容を見てみましょう。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC - **Summary** レベルまたは **Details & Timeline** タブで出力を確認してください。どちらも、エージェントがこの質問に答えるために単一のUCツールを使用したことを示します。トークン数とレイテンシも確認できます。
# MAGIC - **Details & Timeline** をクリックし、**Show execution time**（**Inputs / Outputs** の左側）をクリックしてください。これにより、エージェント推論のどのコンポーネントが最も/最も少ない時間を要したかが表示されます。
# MAGIC
# MAGIC ![トークン数とレイテンシビュー](../Includes/images/token-count-latency.png)
# MAGIC
# MAGIC - **Details & Timeline** で **Attributes** をクリックしてください。ここでは、モデル名、トークン数（入力と出力の両方）、タイミング情報などのメタデータを確認できます。
# MAGIC
# MAGIC ![実行時間ビュー](../Includes/images/show-execution-time.png)

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. Unity Catalogでのカスタムアーティファクトロケーション
# MAGIC
# MAGIC 次に、アーティファクトロケーションをUnity Catalogに変更する方法を見てみましょう。`create_experiment()` を使用すると、エージェントのトレースとアーティファクトを保存するためのUnity Catalogボリュームなど、カスタムアーティファクトロケーションを指定できます。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 次のセルを実行して、`experiment_name_2` に基づく新しいエクスペリメントを作成し、アーティファクトパスが `artifact_path` を指すようにしてください。セルを複数回実行した場合のエラーハンドリングの追加ロジックがあることに注意してください。
# MAGIC > `mlflow.create_experiment()` で新しいエクスペリメントを作成する場合、その後に `mlflow.set_experiment()` を続ける必要があることに注意してください。

# COMMAND ----------

experiment_status = mlflow.get_experiment_by_name(experiment_name_2)

if experiment_status is None:
    print("Experiment does not exist. Creating new experiment.")
    mlflow.create_experiment(
        name=experiment_name_2,
        artifact_location=artifact_path
    )
    mlflow.set_experiment(experiment_name_2)
else:
    print("Experiment already exists.")
    experiment_id = experiment_status.experiment_id
    mlflow.set_experiment(experiment_id=experiment_id)
    print(f"Experiment ID: {experiment_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC #### C2.1 カスタムアーティファクトロケーションでのテスト
# MAGIC
# MAGIC エージェントを再度呼び出し、カスタムUnity Catalogボリュームに保存されたアーティファクトを確認しましょう。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 1. 次のセルを実行して、同じプロンプトでエージェントを呼び出してください。

# COMMAND ----------

agent.ask(prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC #### C2.2 カスタムアーティファクトストレージの確認
# MAGIC
# MAGIC カスタムアーティファクトディレクトリがトレースデータで更新されることを確認できます。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 1. Unity Catalogボリュームの `agent_vol` に移動し、上記に表示されたトレースIDに対応する新しいフォルダがあることを確認してください（例については下のスクリーンショットを参照）。
# MAGIC
# MAGIC ![ボリューム内のトレースID](../Includes/images/trace-id.png)
# MAGIC
# MAGIC 2. **agent_vol → トレースID → artifacts → traces.json** に移動し、JSONオブジェクトを展開してください。以下の画像のようになります。
# MAGIC
# MAGIC ![JSONトレース構造](../Includes/images/json-trace.png)

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. `@mlflow.trace` デコレータでのカスタムトレーシング
# MAGIC
# MAGIC 自動トレーシングはサポートされたframeworksでは適切に動作しますが、カスタムPython関数やビジネスロジックをトレースする必要がある場合があります。MLflowは、これらのシナリオを処理するための手動トレーシング用の高レベルAPIを提供します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. 手動トレーシングアプローチ
# MAGIC
# MAGIC カスタムトレーシングを実装する方法は2つあります：
# MAGIC
# MAGIC 1. **`@mlflow.trace` デコレータの使用**: コードの変更を最小限に抑えた関数レベルのトレーシングに最適
# MAGIC 2. **コンテキストマネージャーの使用**: コードブロックと複雑なworkflowsのトレーシングに最適
# MAGIC
# MAGIC このデモではデコレータアプローチに焦点を当てます。低レベルクライアントAPIも存在しますが、これらはこのデモの範囲を超えています。詳細は[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/low-level-api)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. `@mlflow.trace` デコレータの理解
# MAGIC
# MAGIC `@mlflow.trace` デコレータを使用すると、_1行_ のコードだけで任意の関数にトレーシングを追加できます：関数の上に `@mlflow.trace` を追加するだけで、MLflowは自動的に入力内容、出力内容、所要時間、発生したエラーをキャプチャします。機能をここで要約しますが、デコレータについて詳しくは[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/fluent-apis#context-manager)をお読みください。
# MAGIC
# MAGIC 主な機能：
# MAGIC
# MAGIC - 関数間の親子関係を理解し、`mlflow.langchain.autolog()` などの自動トレーシング機能と連携できます。
# MAGIC - デコレータは、同期、非同期、ジェネレータ関数を含むすべての一般的な関数タイプをサポートし、あらゆるアプリケーションアーキテクチャに柔軟に対応します。
# MAGIC - 完全なオブザーバビリティを確保するため、`@mlflow.trace` デコレータは一般的に[複数のデコレータ](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/fluent-apis#using-mlflowtrace-with-other-decorators)を使用する際に最も外側に配置する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. 例1: シンプルな関数トレーシング
# MAGIC
# MAGIC まず、`@mlflow.trace` デコレータを使用してカスタムPython関数にオブザーバビリティを追加する簡単な例を見てみましょう。この例では、framework統合（OpenAIやLangChainの自動トレーシングなど）によって自動的にキャプチャされない関数をトレースする方法を実演します。
# MAGIC
# MAGIC 以下のセルでは、カスタムの `span_type` パラメータを持つ `@mlflow.trace` を使用しています。`span_type=SpanType.TOOL` は、これをトレースUIでツールスパンとして分類し、トレースをレビューする際に異なるタイプの操作（`FUNC`、`TOOL`、`CHAIN` など）を識別しやすくします。スパンタイプについて詳しくは[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/data-model#span-types)をお読みください。`span_type` にはカスタムの `str` 値を常に渡すことができることに注意してください。
# MAGIC
# MAGIC > **スパンとは何ですか？** スパンは、アプリケーション内の各ステップに関するデータを記録するために使用されます。MLflow UIでトレースを表示するとき、スパンのコレクションを見ています。`span` という名前は[OpenTelemetryトレース](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/open-telemetry)を参照しています。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 次のセルを実行して、質問を受け取り最小長要件を適用するシンプルなPython検証関数 `validate_input` を作成してください。また、検証関数を呼び出す`process_question` も定義します。エージェントと統合する前に、カスタムトレースをテストすることは常にベストプラクティスです。

# COMMAND ----------

import mlflow
from mlflow.entities import SpanType

@mlflow.trace(
    span_type=SpanType.TOOL, 
    name="Validate Input"
)
def validate_input(question: str, min_length: int = 5):
    """Check if the user's question meets basic requirements"""
    if len(question) < min_length:
        return {
            "valid": False,
            "error": f"Question too short (minimum {min_length} characters)"
        }
    if question.strip() == "":
        return {
            "valid": False,
            "error": "Question cannot be empty"
        }
    return {
        "valid": True,
        "cleaned_question": question.strip()
    }

@mlflow.trace(name="Process Question")
def process_question(user_input: str):
    """Process and validate user input"""
    # ステップ1: 入力を検証
    validation_result = validate_input(user_input)
    
    # ステップ2: 質問を処理
    cleaned = validation_result["cleaned_question"]
    return f"Processing: {cleaned}"

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. トレースされた関数のテスト
# MAGIC
# MAGIC 有効な入力と無効な入力でトレースされた関数をテストしてみましょう。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 1. 次のセルを実行してトレースを確認してください。`process_question` が親スパンで全体的なプロセスを示していることに注意してください。子スパンの`validate_input` は、ユーザーの入力を使用してユーザーが基本要件を満たしていることを確認するクイックチェックを実行します。以下で与えられたプロンプトは問題なく通過します。

# COMMAND ----------

# 有効な入力でテスト
result = process_question("What is the average for Mission?")
print(result)

# COMMAND ----------

# MAGIC %md
# MAGIC 2. 次のプロンプト **"Hi"** は、`validate_input` 関数で定義された長さ要件を満たしていないため失敗します。出力では、MLflowがエラーを処理し、**Events** の下のTrace UIでレポートを提供することに注意してください（下のスクリーンショットを参照）。**Events** を確認して **exception.message** の下で問題を特定し、エラーハンドリングの一部として設定された `cleaned_question` を表示してください。
# MAGIC
# MAGIC ![MLflowトレースエラーハンドリング](../Includes/images/mlflow-trace-error.png)

# COMMAND ----------

# 無効な入力でテスト - これは検証に失敗します
result2 = process_question("Hi")
print(result2)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D5. 例2: カスタム関数でのLLM呼び出しのトレーシング
# MAGIC
# MAGIC この例は前の例を基に、LLMレイヤーを追加します。上で定義した `validate_input` 関数を使用しますが、以下で定義した `call_llm` 関数を使用して質問をLLMに渡す追加レイヤーを追加します。この関数には `CHAT_MODEL` のスパンタイプが渡され、これはチャットモデルへのクエリを表します。これは前に定義した同じ `agent` オブジェクト（`demo_agent1_config.json` で定義されたツールを使用する能力を持つ）を呼び出します。

# COMMAND ----------

import mlflow
from mlflow.entities import SpanType

@mlflow.trace(
    name="Call LLM",
    span_type=SpanType.CHAT_MODEL
)
def call_llm(question: str):
    return agent.ask(question)

@mlflow.trace(name="Process Question")
def process_question(user_input: str):
    """Main function that validates input and calls LLM"""
    # ステップ1: 入力を検証
    validation_result = validate_input(user_input)
    
    # ステップ2: 有効な場合、LLMを呼び出し
    cleaned = validation_result["cleaned_question"]
    llm_response = call_llm(cleaned)
    
    return llm_response

# COMMAND ----------

# MAGIC %md
# MAGIC ### D6. 多段階トレースワークフローのテスト
# MAGIC
# MAGIC 検証とLLM対話を含む完全なワークフローをテストしてみましょう。
# MAGIC
# MAGIC #### 手順
# MAGIC
# MAGIC 1. 有効な質問で次のセルを実行し、トレース階層を確認してください。
# MAGIC 2. `Call LLM` を使用する際に、カスタムトレースとUCツールの両方がトレースに表示されることに注意してください。
# MAGIC
# MAGIC これは、エージェントが装備されたツールを使用する能力を与えながら、宣言的なツール呼び出しを可能にするパターンです。

# COMMAND ----------

# 有効な質問でテスト
result = process_question(prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC 3. 無効な質問でテストして、エラーがトレースを通じてどのように伝播するかを確認してください。これは前に見たのと同じエラーです。

# COMMAND ----------

# 無効な質問でテスト
result2 = process_question("Hi")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このデモでは、MLflowを使用したシングルエージェントアプリケーション向けの包括的なトレーシング戦略について説明しました。エージェント開発ワークフローでそれぞれ異なる使用例に対応する、自動と手動の両方のトレーシングアプローチの実装方法を学びました。
# MAGIC
# MAGIC ## 次のステップ
# MAGIC MLflowを使用したシングルエージェントのトレーシングについて理解したので、次のデモでタグ付けと再現可能なエージェントの構築のためのMLflowについて学習を続けることができます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>