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
# MAGIC # デモ - LangChainを使用したシングルエージェントの構築
# MAGIC
# MAGIC このデモンストレーションでは、Unity Catalog（UC）関数をLangChain framework内のツールとして活用するAIエージェントの作成方法を探求します。UCツールをLangChainツールキットと統合し、Mosaic AI Model Servingでホストされている基盤モデルを使用して推論と行動を取ることができるエージェントを構築します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC このレッスンの終了時に、以下のことができるようになります：
# MAGIC - ツール、モデル、エージェントframework間のタスクの分離を理解する
# MAGIC - `UCFunctionToolkit` を使用してUnity Catalog関数をLangChainに登録、テスト、統合するプロセスを知る
# MAGIC - ツール呼び出し機能を持つLangChainエージェントを設定および実行する
# MAGIC - エージェント実行のトレース概要を表示および解釈し、MLflowを使用して意思決定を分析する方法を知る

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. 環境設定と前提条件

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. コンピュート要件
# MAGIC
# MAGIC **🚨 必須 - サーバレスコンピュートを選択してください**
# MAGIC
# MAGIC このコースはサーバレスコンピュート上で実行するように設定されています。クラシックコンピュートでも動作する可能性がありますが、テストはサーバレス上で実行されています。
# MAGIC
# MAGIC **このデモはサーバレスコンピュートのバージョン5を使用してテストされました。** 正しいバージョンのサーバレスを使用していることを確認するために、[ノートブックのサーバレスバージョンの表示と変更に関するドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 依存関係のインストール
# MAGIC
# MAGIC ワークスペースセットアップの一部として、いくつかのPythonライブラリがインストールされています。ノートブックスコープのライブラリのリストを確認するには、[このドキュメント](https://docs.databricks.com/aws/en/compute/serverless/dependencies#configure-environment-for-job-tasks)をお読みください。
# MAGIC
# MAGIC **注意：** `langchain-databricks` に慣れている場合は、`databricks-langchain` がそれに置き換わることに注意してください。このデモンストレーションではLangChainを使用していますが、同様のアプローチを他のライブラリにも適用できます。

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup-2.1

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. Airbnbデータセットの検査
# MAGIC クラスルームセットアップの一部として、AirbnbデータセットはUnity Catalog内のDeltaテーブルとして処理および保存されています。次のセルを実行してデータセットの最初の数行をクエリしてください。

# COMMAND ----------

df = spark.read.table('sf_airbnb_listings')
display(df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. Databricks Function Clientの初期化
# MAGIC
# MAGIC `DatabricksFunctionClient` は、Unity Catalog関数を実行するためのプログラマティックインターフェースを提供します。コンピュート要件に合わせてサーバレス実行モード用に設定します。これは登録されたUC関数をテストするために使用されます。

# COMMAND ----------

from unitycatalog.ai.core.databricks import DatabricksFunctionClient

# client = DatabricksFunctionClient()  # クラシックコンピュート用
client = DatabricksFunctionClient(execution_mode="serverless")  # サーバレスコンピュート用

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. エージェントの概念の理解
# MAGIC
# MAGIC エージェントframeworkを使用する際には、現代のエージェントの3つの核心コンポーネントを独立してテストすることが重要であることを理解することが大切です：
# MAGIC
# MAGIC 1. ツール構築
# MAGIC 2. 大規模言語モデル（LLM）/小規模言語モデル（SLM）の選択
# MAGIC 3. エージェントframeworkの選択
# MAGIC
# MAGIC ### C1. エージェント概念のクイックレビュー
# MAGIC
# MAGIC シングルエージェントを構築する際、これらのコンポーネントがどのようにエージェントを構成するかを理解することが重要です。簡潔に言うと、_AIエージェントは環境を観察・分析し（計画）、特定の目標を達成するために行動を取る（ツールを使用する）能力を持っています_。これをもう少し詳しく説明しましょう：
# MAGIC
# MAGIC 1. **Tool building**： これは基盤となるLLM/SLM（ツール呼び出しが可能である限り）および_あらゆる_エージェントframeworkに依存しません。実行可能なツールは、信頼性と一貫性を確保するためにLLM/SLMに装備する前に徹底的にテストする必要があります。
# MAGIC 2. **LLM/SLM**： プロンプトとシステムポリシーによって導かれる認識された計画に基づいて、ツールを呼び出すかどうかを_決定_する本質的なエージェント能力を持つ言語モデルが必要です。したがって、LLM/SLMだけでも、推論ループが浅い場合でも、推論ループの結果に基づいて環境で行動できる場合は、エージェントと_見なされる可能性がある_ことを覚えておくことが重要です。
# MAGIC 3. **Agentic Framework**： 基盤となるframeworkは、共通のLLM間でプラグ可能であり、framework固有のポリシー（例：状態/メモリ管理とトレース）を通じてモデルの_動作_を調整するために存在します。
# MAGIC
# MAGIC ### C2. このデモンストレーションの焦点領域
# MAGIC
# MAGIC これを念頭に置いて、このデモンストレーションではツールの構築やLLM/SLMの選択時に考慮すべき事項については_扱わない_ことに注意してください。代わりに、以下に焦点を当てます：
# MAGIC
# MAGIC 1. Unity CatalogツールでLangChainエージェント（ツール呼び出しLLM + LangChain framework）を設定および装備する方法
# MAGIC 2. LangChainエージェントを実行する方法
# MAGIC 3. MLflowを使用した基本的なトレース実行

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. Unity Catalog関数とLangChainの統合
# MAGIC
# MAGIC `databricks_langchain` を活用して、UC関数をLangChainに直接統合できるツールとしてラップできます。
# MAGIC
# MAGIC **`UCFunctionToolkit`** は、Databricks-LangChain統合のコンポーネントです。Unity Catalogユーザー定義関数（UDF）とエージェントframework（LangChainなど）の間のブリッジとして機能します。Unity Catalog関数を`UCFunctionToolkit`でラップすると、その関数がLLMエージェントがプログラム的に呼び出すことができる「ツール」としてアクセス可能になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. ツールリストの定義
# MAGIC
# MAGIC まず、使用したい関数のリストを `function_names` と呼びます。`UCFunctionToolkit` を使用する際は、カタログとスキーマを含める必要があります。

# COMMAND ----------

tool_list_raw = [
    'avg_neigh_price',
    'cnt_by_room_type'
]

function_names = []
for tool in tool_list_raw:
    tool = catalog_name + '.' + schema_name + '.' + tool
    function_names.append(tool)

print(f"Tool list: {function_names}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. UCFunctionToolkitの作成
# MAGIC
# MAGIC ツールキットはUnity Catalog関数をラップし、LangChainツールとして利用可能にします。

# COMMAND ----------

from databricks_langchain import UCFunctionToolkit

# Unity Catalog関数でツールキットを作成
toolkit = UCFunctionToolkit(function_names=function_names)
tools = toolkit.tools

# COMMAND ----------

# MAGIC %md
# MAGIC ### D3. ツールキットのテスト
# MAGIC
# MAGIC ツールキットが作成されたので、それを使用してツールを実行できることを確認するための簡単なチェックを実行しましょう。ここでは、以前に定義した `tools` によるツールキットと `DatabricksFunctionClient` を使用して、`execute_function` APIを使用してテストペイロードを送信することで、サンプルペイロードを実行します。次の2つのセルからの出力は、上記でSQLクエリを使用してテストしたときと同じになることに注意してください。

# COMMAND ----------

payload1 = {'neighborhood_name': 'Mission'}
payload1_test_result = client.execute_function(
    function_name=tools[0].uc_function_name,
    parameters=payload1
)
print(payload1_test_result.value)

# COMMAND ----------

payload2 = {
    'neighborhood_name': 'Mission',
    'room_type_filter': 'Private room'
}
payload2_test_result = client.execute_function(
    function_name=tools[1].uc_function_name,
    parameters=payload2
)
print(payload2_test_result.value)

# COMMAND ----------

# MAGIC %md
# MAGIC ### D4. 進捗チェックポイント
# MAGIC
# MAGIC 要約すると、これまでに以下を行いました：
# MAGIC
# MAGIC 1. UC関数を構築し、SQLクエリを通じてそれらの関数をUCに登録しました。
# MAGIC 2. SQLクエリを使用してこのノートブック内でUC関数をローカルでテストしました。
# MAGIC 3. `tools` と呼ばれる **LangChain** ツールキットを作成し、前のステップと同じサンプルペイロードを使用してこのツールキットをテストしました。
# MAGIC
# MAGIC 次に、エージェントを設定して実行します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. エージェントの設定と実行
# MAGIC
# MAGIC `langchain.agents` の `AgentExecutor` メソッドは、LLMがエージェントの決定関数を繰り返し呼び出し、ツール実行を処理し、推論、行動、観察のステップ間の情報の流れを管理するオーケストレーターとして機能します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. エージェント設定の読み込み
# MAGIC
# MAGIC 明確にするために、クエリしたいendpoint、LLMの温度値、システムプロンプトを `demo_agent.json` という別のファイルに保存しました。エージェントの設定をこのメインノートブックから分離することで、デバッグと更新に役立ちます。まず、`json.load()` を使用してこの設定を読み込みましょう。

# COMMAND ----------

import json

# JSONファイルを読み込み
with open("./demo_agent.json", "r") as f:
    config = json.load(f)

llm_endpoint = config['llm_endpoint']
llm_temperature = config['llm_temperature']
system_prompt = config["system_prompt"]

print("Endpoint:", llm_endpoint)
print("Temperature:", llm_temperature)
print("System Prompt:", system_prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. オプション演習
# MAGIC
# MAGIC frameworkがLLMから独立していることを実証するために、左側のメニューバーの **Serving** に移動してLLM endpoint名を切り替えてみてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E3. 必要なライブラリのインポート
# MAGIC
# MAGIC エージェントの構築と実行に必要なPythonライブラリをインポートします。

# COMMAND ----------

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

from databricks_langchain import ChatDatabricks

import mlflow

# COMMAND ----------

# MAGIC %md
# MAGIC ### E4. 言語モデルの初期化
# MAGIC
# MAGIC `llm_endpoint` として保存されたLLMを温度 `llm_temperature` で初期化します。これは、LangChainアプリケーション内で使用するために特別に設計された会話型LLMインターフェースを提供する `databricks-langchain` パッケージによって提供されるクラスである`ChatDatabricks`を使用して行います。

# COMMAND ----------

llm_config = ChatDatabricks(
    endpoint=llm_endpoint,
    temperature=llm_temperature
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### E5. プロンプトテンプレートの定義
# MAGIC
# MAGIC ここでは、`demo_agent.json` から取得した変数 `system_prompt` を使用します。また、チャット履歴、入力、エージェントのスクラッチパッドも設定します。
# MAGIC
# MAGIC `ChatPromptTemplate.from_messages()` は、チャット中心のLLMに_順次_送信される、それぞれ独自の役割と内容を持つすべてのメッセージのリストを生成するための再利用可能なテンプレートを構築します。つまり、最初にシステムプロンプトが使用され、次に進行中の会話を注入し、その後にユーザー入力と中間結果のためのエージェントの段階的推論が続きます。

# COMMAND ----------

prompt_payload = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_prompt,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### E6. MLflowトレースの有効化
# MAGIC デバッグと分析のためにエージェント実行の詳細をキャプチャするMLflowによる自動トレースを有効にします。サーバレス環境を使用する場合、MLflowトレースUIがエージェントの出力の一部として表示されるようにするには、自動ログ記録を有効にする必要があることに注意してください。MLflowは[人気のGenAIライブラリと統合されている](https://mlflow.org/docs/latest/genai/tracing/#one-line-auto-tracing-integrations)ため、次のセルに示すように `mlflow.<framework>.autolog()` で開始するのは実際に非常に簡単です。

# COMMAND ----------

mlflow.langchain.autolog()

# COMMAND ----------

# MAGIC %md
# MAGIC ### E7. エージェント設定の作成
# MAGIC
# MAGIC LLMの設定（`llm_config`）、以前に定義したツールキットからのツール、および上記で定義したプロンプトペイロード（`prompt_payload`）を指定してエージェントを定義します。

# COMMAND ----------

agent_config = create_tool_calling_agent(
    llm_config,
    tools,
    prompt_payload
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### E8. エージェントの実行
# MAGIC
# MAGIC エージェントの設定が整ったので、`AgentExecutor` でエージェントを実行する準備ができました。`verbose=True` パラメータは、エージェントの推論とツール呼び出しプロセスの詳細ログを有効にします。

# COMMAND ----------

agent_executor = AgentExecutor(agent=agent_config, tools=tools, verbose=True)
response = agent_executor.invoke(
    {
        "input": "Get the average for Mission and tell me the number of properties there that have a shared room"
    }
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## F. エージェント応答の高レベル分析とMLflowによるトレース
# MAGIC
# MAGIC MLflow Trace UIは、エージェントの実行時に出力の一部として表示されます。**Summary** タブをクリックすると、エージェントの推論ループの高レベルビューが表示されます。これにより、エージェントの意思決定プロセスの詳細な可視性が提供されます。
# MAGIC
# MAGIC ![optional alt text](../Includes/images/mlflow-tool-use-2.png)
# MAGIC
# MAGIC 出力は上記のスクリーンショットと同様になるはずで、以下が含まれます：
# MAGIC
# MAGIC - **呼び出されたツール**：上記のクエリの性質により、両方のツールが呼び出されます。
# MAGIC - **`ChatDatabricks` とUCツールに渡されたパラメータ**：例えば、下の画像では、ツール `avg_neigh_price` に対して文字列 `Mission` が入力され、出力が `{"format": "SCALAR", "value": "229.7557803468208"}` であったことがわかります。
# MAGIC
# MAGIC ![optional alt text](../Includes/images/mlflow-tool-use-1.png)
# MAGIC
# MAGIC - **各ツールから返された結果**：例えば、`ChatDatabricks_2` のドロップダウン矢印をクリックすると、推論チェーンの一部としてLLMへの入力および出力として供給されたツールの結果が表示されます。
# MAGIC - **エージェントによって生成された最終応答**（`ChatDatabricks_3`）。
# MAGIC
# MAGIC 前のセルからの出力は、以前に作成した両方のツールが呼び出されたことを示しています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### F1. エージェントの応答の解析
# MAGIC
# MAGIC エージェントの応答を解析し、読みやすい形式で表示します。

# COMMAND ----------

# エージェントの応答からテキストセグメントを抽出
output_segments = response['output']

for segment in output_segments:
    if isinstance(segment, dict) and segment.get('type') == 'text':
        print(segment['text'])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC このデモンストレーションを実行することで、Unity Catalogによって保存・管理されているツールに接続されたLangChainエージェントの構築に成功しました。以下のことを学びました：
# MAGIC
# MAGIC - `UCFunctionToolkit` を使用してUnity Catalog関数をLangChainにブリッジする
# MAGIC - ツール呼び出し機能を持つ基盤モデルを設定する
# MAGIC - ユーザークエリについて推論し、適切なツールを呼び出すAIエージェントを実行する
# MAGIC - MLflowを使用してエージェントの動作をトレースおよび分析する
# MAGIC
# MAGIC このアプローチにより、ガバナンス、セキュリティ、系譜追跡を維持しながら、Unity Catalogに保存された組織のデータ資産を活用する本番対応のAIエージェントを構築できます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>