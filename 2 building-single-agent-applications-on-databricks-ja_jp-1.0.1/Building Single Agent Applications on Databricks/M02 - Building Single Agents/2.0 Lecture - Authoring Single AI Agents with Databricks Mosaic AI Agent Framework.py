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
# MAGIC # 講義 - Databricks Mosaic AI Agent Frameworkによる単一AIエージェントの作成
# MAGIC
# MAGIC この講義ノートブックでは、Databricksが包括的なMosaic AI Agent Frameworkを通じて単一AIエージェントの開発をどのようにサポートしているかを探求します。Databricks platform上でプロダクション対応のAIエージェントを作成するためのツール、frameworks、ベストプラクティスを検証します。
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC Databricks Mosaic AI Agent Frameworkは、AIエージェントの作成、デプロイ、監視のための統合プラットフォームを提供します。このframeworkは、LangChain、LangGraph、DSPy、OpenAIなどの複数の人気のあるエージェント開発ライブラリをサポートし、Vector Search、Model Serving、MLflowなどのDatabricksサービスとのネイティブ統合を提供します。
# MAGIC
# MAGIC このframeworkは、自動トレーシング、包括的な評価機能、Mosaic AI Model Servingへのシームレスなデプロイなどの機能を通じて、プロダクション対応を重視しています。シンプルなチャットエージェントから複雑なマルチエージェントシステムまで、Databricksはエンタープライズ規模のAIアプリケーションに必要なツールとインフラストラクチャを提供します。
# MAGIC
# MAGIC ## 学習目標
# MAGIC
# MAGIC _この講義の終了時には、以下ができるようになります：_
# MAGIC - Databricks Mosaic AI Agent Frameworkのアーキテクチャとコンポーネントを理解する
# MAGIC - プロダクショングレードのエージェント開発におけるResponsesAgentの利点を説明する
# MAGIC - サポートされているエージェント作成frameworksとその統合パターンを特定する
# MAGIC - エージェントのデプロイに関する考慮事項を説明する
# MAGIC - ストリーミング、カスタム入出力、レトリーバー統合などの高度な機能を認識する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. Mosaic AI Agent Frameworkの紹介
# MAGIC
# MAGIC Databricks Mosaic AI Agent Frameworkは、エンタープライズ規模でAIエージェントを構築、デプロイ、管理するための包括的なソリューションを表しています。このframeworkは、開発からプロダクション監視までの完全な_エージェントライフサイクル_に対応しています。
# MAGIC
# MAGIC ### エージェントのライフサイクル
# MAGIC エージェントのライフサイクルは以下のようにまとめることができます：
# MAGIC 1. **データの準備とツールの作成**：  
# MAGIC     - この段階には、Notebooks、SQLクエリ、Lakeflowスイートを使用したAI関連のETLが含まれます。通常、これはAIエンジニアがVector Searchを使用して非構造化データを埋め込み、インデックス化する場所です。 
# MAGIC     - データが準備されると、エンジニアはSQLまたはPython構文でツールを作成し、包括的なガバナンスのためにそれらのツールを[Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)に登録します。 
# MAGIC 1. **品質チェックを伴う迅速なプロトタイピング**
# MAGIC     - この段階では、通常、エージェントの迅速なプロトタイピングのためのAI Playgroundのノーコードインターフェースで迅速なテストが実行されます。ここで、システムプロンプトを指定し、異なるモデルを選択して並べて比較し、結果を感覚的にチェックできます。 
# MAGIC     - その後、AIエンジニアは[MLflow 3による評価ツール](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)でコンテンツを評価します。これは品質問題とその根本原因を特定するのに役立つように設計されています。 
# MAGIC     - 迅速なプロトタイピングが完了したら、プレイグラウンドからコードをエクスポートし、`mlflow.genai.evaluate()` を活用できます（詳細は[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/eval-harness)をお読みください）。  
# MAGIC 1. **評価とフィードバックの収集**
# MAGIC     - LLMジャッジ、ステークホルダーラベリング、合成データなどの方法を使用して、評価データセットに対してエージェントをテストします。ステークホルダー/ドメインエキスパートのフィードバックは、通常、レビューアプリまたは相互作用の直接トレーシングを通じて収集されます。 
# MAGIC 1. **データとフィードバックのラベリング**
# MAGIC     - 相互作用と出力にラベルを付けて、将来のエージェント反復をテストするための高品質ベンチマークを作成します。これにより、品質評価のグランドトゥルースとして機能する評価セットが作成されます。
# MAGIC     - ラベリングセッションは、GenAIアプリケーションの動作に関するドメインエキスパートからのフィードバックを収集するための構造化された方法を提供します。ラベリングセッションについて詳しくは[こちら](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/concepts/labeling-sessions)をお読みください。
# MAGIC 1. **反復的改善**
# MAGIC     - フィードバックとベンチマーク結果を使用して、品質問題の根本原因を特定し修正します。 
# MAGIC     - 精度、安全性、コスト、レイテンシの望ましいバランスを達成するために、複数のバージョン/設定を評価します。
# MAGIC 1. **プロダクションへのデプロイ**
# MAGIC     - エージェントは開発からスケーラブルなプロダクション対応環境（多くの場合、Model ServingによるREST API）に移行します。ここで、エージェントは、統合ガバナンスのためのUnity Catalogなどのコンポーネントを活用して、アクセスとコンプライアンスのためにガバナンスされます。
# MAGIC 1. **品質とパフォーマンスの監視**
# MAGIC     - デプロイ後、エージェントは開発時と同じ評価とトレーシングツールを使用して継続的に監視されます。ログ、トレース、ユーザーフィードバック、自動ジャッジが継続的な品質シグナルを提供し、プロダクションインタラクションからの新しいデータが将来の改善のための評価セットに組み込まれます。
# MAGIC     - デプロイされたエージェントには[AI Gateway拡張](https://docs.databricks.com/aws/en/ai-gateway/)推論テーブルが自動的に有効になり、DSPyやLangChainなどの人気のあるエージェント作成ライブラリでMosaic AI Agent Frameworkを使用する際に詳細なリクエストログメタデータにアクセスできます。 
# MAGIC     - エンドツーエンドの可観測性のために[MLflowトレーシング](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/)を活用できます。 
# MAGIC     - [GenAIのプロダクション監視により、プロダクションGenAIアプリからのトレースでMLflowスコアラーを自動実行できます](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring)
# MAGIC
# MAGIC > この講義に続くデモでは、サポートされているframeworksでエージェントをプロトタイピングすることに焦点を当てます。  
# MAGIC
# MAGIC ![single-agents-course.png](../Includes/images/single-agents-course.png "single-agents-course.png")
# MAGIC <p>
# MAGIC <em>
# MAGIC この講義では、エージェントframeworksについて扱います。 
# MAGIC </em>
# MAGIC </p>

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. frameworkアーキテクチャ
# MAGIC
# MAGIC UC/外部ツールの初期テストをノートブック/SQL エディターとAI Playgroundの両方で完了したと仮定すると、エージェントframeworksを見る準備ができています。これを支援するために、Databricksは、Mosaic AI Agent Frameworkで高品質なエージェンティックおよびRAGアプリケーションを作成、デプロイ、監視するためのツールスイートを提供しています。このframeworkは、いくつかの主要コンポーネントを中心に構築されています：
# MAGIC
# MAGIC - **MLflow 3 Integration**：実験追跡、モデルログ記録、ライフサイクル管理を提供
# MAGIC - **ResponsesAgent Interface**：OpenAI Responsesスキーマと互換性のあるプロダクション対応インターフェース
# MAGIC - **Agent Authoring Libraries**：LangChain、LangGraph、DSPy、OpenAIのサポート
# MAGIC - **Databricks AI Bridge**：エージェントをDatabricks AI機能に接続する統合パッケージ
# MAGIC - **Agent Governance**：ツールとエージェントはUCに登録・ガバナンスされ、AI GatewayとMLflowトレーシングによる推論ログ/トレース。 
# MAGIC - **Mosaic AI Model Serving**：プロダクションエージェント向けのスケーラブルなデプロイインフラストラクチャ
# MAGIC - **Evaluation & Monitoring**：エージェント品質評価とパフォーマンス追跡のための組み込みツール

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. 要件とセットアップ
# MAGIC
# MAGIC Databricks frameworkを使用してエージェントを開発するには、いくつかの技術プラットフォーム要件とパッケージを認識する必要があります。 
# MAGIC
# MAGIC **Core Requirements：**
# MAGIC - `databricks-agents` 1.2.0以上
# MAGIC - `mlflow` 3.1.3以上
# MAGIC - Python 3.10以上
# MAGIC - サーバーレスコンピュートまたはDatabricks Runtime 13.3 LTS以上
# MAGIC
# MAGIC **Installation Command：**
# MAGIC ```python
# MAGIC %pip install -U -qqqq databricks-agents mlflow
# MAGIC ```
# MAGIC
# MAGIC **AI Bridge Integration Packages：**
# MAGIC Databricks AI Bridgeライブラリは、Databricks AI/BI GenieやVector Searchなどのdatabricks AI機能と相互作用するためのAPIの共有レイヤーを提供します。最新のリリースノートとバージョンは[PyPi](https://pypi.org/project/databricks-ai-bridge/)で確認できます。
# MAGIC - OpenAI統合用の `databricks-openai`
# MAGIC - LangChain/LangGraph統合用の `databricks-langchain`
# MAGIC - DSPy統合用の `databricks-dspy`
# MAGIC - 純粋なPythonエージェント用の `databricks-ai-bridge`（専用統合パッケージなし）

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. ResponsesAgent：プロダクションインターフェース
# MAGIC
# MAGIC DatabricksはMLflow `ResponsesAgent` インターフェースをプロダクショングレードエージェントを作成するための主要な方法として推奨しています。このインターフェースは、Databricks固有の拡張機能を追加しながら、OpenAI Responsesスキーマとの互換性を提供します。
# MAGIC
# MAGIC > [`ChatAgent`](https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-legacy-schema)に慣れている場合、`ResponsesAgent` は新しいエージェント用にこのインターフェースを置き換えることを意図しています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B1. ResponsesAgentの利点
# MAGIC
# MAGIC `ResponsesAgent` インターフェースは、従来のエージェントインターフェースに対して大きな利点を提供し、[サポートframeworksで既存のエージェントをラップすることもサポートしています](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent?language=Streaming+with+code+re-use#what-if-i-already-have-an-agent)。 
# MAGIC
# MAGIC **Advanced Agent Capabilities:**
# MAGIC - 複雑なworkflows用のマルチエージェントサポート
# MAGIC - リアルタイム応答チャンクでのストリーミング出力
# MAGIC - 包括的なツール呼び出しメッセージ履歴
# MAGIC - ツール呼び出し確認サポート
# MAGIC - 長時間実行ツール実行サポート
# MAGIC
# MAGIC **Streamlined Development & Deployment:**
# MAGIC - Framework非依存：Databricks互換性のための既存エージェントのラップ
# MAGIC - IDE自動補完サポートを備えた型付き作成インターフェース
# MAGIC - モデルログ記録中の自動シグネチャ推論
# MAGIC     > 推奨される `ResponsesAgent` インターフェースを使用していない場合、シグネチャを手動で定義するか、MLflowのModel Seignature推論機能を使用して、入力例に基づいてエージェントのシグネチャを自動生成する必要があります。詳細は[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent#infer-model-signature-during-logging)をお読みください。 
# MAGIC - `predict` と `predict_stream` による集約ストリーミング応答の自動トレーシング
# MAGIC     > `ResponsesAgent` は、非ストリーミングリクエストを処理するために `ResponsesAgentResponse` を返す `predict` メソッドの実装を必要とします。一方、ストリーミングエージェントの場合、`predict_stream` メソッドを実装できます。これはこの講義の範囲を超えていますが、詳細は[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent?language=Streaming+with+code+re-use)をお読みください。  
# MAGIC - 詳細ログ記録のためのAI Gateway拡張推論テーブル

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. `ResponsesAgent` スキーマ構造
# MAGIC
# MAGIC `ResponsesAgent` は入力と出力に構造化されたスキーマを使用します：
# MAGIC
# MAGIC **Input Format (`ResponsesAgentRequest`):**
# MAGIC ```python
# MAGIC {
# MAGIC "input": [
# MAGIC {
# MAGIC "role": "user",
# MAGIC "content": "What did the data scientist say when their Spark job finally completed?"
# MAGIC }
# MAGIC ]
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC **Output Format (`ResponsesAgentResponse`):**
# MAGIC ```python
# MAGIC ResponsesAgentResponse(
# MAGIC output=[
# MAGIC {
# MAGIC "type": "message",
# MAGIC "id": str(uuid.uuid4()),
# MAGIC "content": [{"type": "output_text", "text": "Well, that really sparked joy!"}],
# MAGIC "role": "assistant",
# MAGIC }
# MAGIC ]
# MAGIC )
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. 既存エージェントのラッピング
# MAGIC
# MAGIC LangChain、LangGraph、または類似のframeworksで構築されたエージェントを既に持っている場合、それを書き直す必要はありません。代わりに、`mlflow.pyfunc.ResponsesAgent` を継承するラッパークラスを作成します：
# MAGIC
# MAGIC **Basic Wrapper Pattern:**
# MAGIC ```python
# MAGIC from uuid import uuid4
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
# MAGIC
# MAGIC class MyWrappedAgent(ResponsesAgent):
# MAGIC     def __init__(self, agent):
# MAGIC         # 既存のエージェント（LangChain/LangGraph/OpenAI等）を参照
# MAGIC         self.agent = agent
# MAGIC
# MAGIC     def prep_msgs_for_llm(self, messages: list[dict]) -> list[dict]:
# MAGIC         # ResponsesAgentRequestメッセージからエージェントの期待する形式への変換を実装
# MAGIC         return messages
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         # 受信メッセージをエージェントの形式に変換
# MAGIC         messages = self.prep_msgs_for_llm([i.model_dump() for i in request.input])
# MAGIC
# MAGIC         # 既存のエージェントを呼び出し（非ストリーミング）
# MAGIC         agent_response = self.agent.invoke(messages)
# MAGIC
# MAGIC         # 文字列出力を確保；必要に応じて変換
# MAGIC         if not isinstance(agent_response, str):
# MAGIC             agent_response = str(agent_response)
# MAGIC
# MAGIC         # ResponsesAgent形式に変換
# MAGIC         output_item = self.create_text_output_item(text=agent_response, id=str(uuid4()))
# MAGIC         return ResponsesAgentResponse(output=[output_item])
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. サポートされているエージェント作成Frameworks
# MAGIC
# MAGIC Databricksは、エージェント開発のための複数の人気Frameworksをサポートしており、それぞれに特定の強みと使用例があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C1. LangChain統合
# MAGIC
# MAGIC LangChainは、広範囲な統合と機能を持つLLMアプリケーション構築のための包括的なframeworkです。
# MAGIC
# MAGIC **Key Features on Databricks:**
# MAGIC - DatabricksサーブモデルをLLMまたは埋め込みとして使用
# MAGIC - VectorストレージのためのMosaic AI Vector Searchとの統合
# MAGIC - MLflow実験追跡とパフォーマンス監視
# MAGIC - 開発とプロダクション可観測性のためのMLflowトレーシング
# MAGIC - シームレスなデータ統合のためのPySpark DataFrameローダー
# MAGIC - 自然言語クエリのためのSpark DataFrame AgentとDatabricks SQL Agent
# MAGIC
# MAGIC **Example Usage:**
# MAGIC ```python
# MAGIC from databricks_langchain import ChatDatabricks
# MAGIC
# MAGIC chat_model = ChatDatabricks(
# MAGIC endpoint="databricks-gpt-5-1",
# MAGIC temperature=0.1,
# MAGIC max_tokens=250,
# MAGIC )
# MAGIC chat_model.invoke("How to use Databricks?")
# MAGIC ```
# MAGIC > LLM開発のための[DatabricksでのLangChain](https://docs.databricks.com/aws/en/large-language-models/langchain)は実験的機能であり、API定義は時間の経過とともに変更される可能性があることに留意してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### C2. DSPy framework
# MAGIC
# MAGIC [DSPy](https://docs.databricks.com/aws/en/generative-ai/dspy#what-is-dspy)は、自動プロンプトエンジニアリング機能を備えたgenerative AIエージェントをプログラム的に定義・最適化するためのframeworkです。
# MAGIC
# MAGIC **Core DSPy Components:**
# MAGIC - **Modules**：特定のテキスト変換を処理するコンポーネント（手書きプロンプトを置き換える）
# MAGIC - **Signature**：入出力動作の自然言語記述（「質問 -> 回答」）
# MAGIC - **Compiler**：パフォーマンスメトリクスのためにモジュールを調整してパイプラインを改善する最適化ツール
# MAGIC - **Program**：複雑なタスクのためのパイプラインを形成する接続されたモジュール
# MAGIC
# MAGIC **DSPy Advantages:**
# MAGIC - 自動プロンプト最適化
# MAGIC - エージェント改善への体系的アプローチ
# MAGIC - 組み込みパフォーマンス最適化機能
# MAGIC - 手動ではなくプログラム的なプロンプトエンジニアリング

# COMMAND ----------

# MAGIC %md
# MAGIC ### C3. OpenAI統合
# MAGIC
# MAGIC DatabricksはDatabricksホストモデルを活用しながら、OpenAIスタイルのエージェントをネイティブサポートします。
# MAGIC
# MAGIC **Integration Benefits:**
# MAGIC - 慣れ親しんだOpenAI APIパターンの使用
# MAGIC - Databricks Foundation Model APIの活用
# MAGIC - OpenAIからDatabricksモデルへのシームレスな移行
# MAGIC - ストリーミングと非ストリーミング応答の両方をサポート
# MAGIC - Databricksモデルでのツール呼び出し機能

# COMMAND ----------

# MAGIC %md
# MAGIC ### C4. 複雑なworkflowsのためのLangGraph
# MAGIC
# MAGIC LangGraphは、より複雑でステートフルなworkflowsのためのグラフベースのエージェントオーケストレーションでLangChainを拡張します。
# MAGIC
# MAGIC **LangGraph Capabilities:**
# MAGIC - グラフベースのエージェントworkflows
# MAGIC - エージェントインタラクション間での状態管理
# MAGIC - 複雑な決定木と条件ロジック
# MAGIC - マルチステップ推論とツール調整

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. ストリーミングとリアルタイム応答
# MAGIC
# MAGIC ストリーミング機能により、エージェントはチャンクでリアルタイム応答を提供でき、ユーザーエクスペリエンスを向上させ、インタラクティブなアプリケーションを可能にします。アイデアは、ユーザーに結果を送信する前に完全な応答を待つことです。MLflowを使用すると、エージェントの応答だけでなく、これらのチャンクと思考プロセスも表示でき、特定のツールを使用した理由または使用しなかった理由についての洞察を得ることができます。
# MAGIC
# MAGIC > [Agent Bricksによるナレッジアシスタント](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant)は、以下のスクリーンショットに示されているKA応答のトレースのように、完全なストリーミングサポートを持っています。 
# MAGIC
# MAGIC ![mlflow-ui.png](../Includes/images/mlflow-ui.png "mlflow-ui.png")
# MAGIC <p><em>Agent Bricksによるナレッジアシスタントを介したMLflowによるチャンクトレーシングの例。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. ストリーミング実装
# MAGIC
# MAGIC `ResponsesAgent` でストリーミングを実装するには、このパターンに従います：
# MAGIC
# MAGIC 1. **Emit Delta Events**：同じ `item_id` で複数の `output_text.delta` イベントを送信
# MAGIC 2. **Finish with Done Event**：完全な出力を含む最終的な `response.output_item.done` イベントを送信
# MAGIC
# MAGIC **Streaming Benefits:**
# MAGIC - リアルタイムユーザーフィードバック
# MAGIC - 知覚パフォーマンスの向上
# MAGIC - 長時間実行操作でのより良いユーザーエンゲージメント
# MAGIC - 自動MLflowトレーシング統合
# MAGIC - AI Gateway推論テーブルでの集約応答
# MAGIC
# MAGIC ![mlflow-chunking.png](../Includes/images/mlflow-chunking.png "mlflow-chunking.png")
# MAGIC <p><em>
# MAGIC 完全な思考として描画される出力のチャンクを介したMLflowによるストリーミング応答。 
# MAGIC </em>
# MAGIC </p>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### D2. ストリーミングでのエラー処理
# MAGIC
# MAGIC Mosaic AIは `databricks_output.error` の下の最後のトークンを通じてストリーミングエラーを伝播します：
# MAGIC
# MAGIC ```json
# MAGIC {
# MAGIC   "delta": "...",
# MAGIC   "databricks_output": {
# MAGIC     "trace": {...},
# MAGIC     "error": {
# MAGIC       "error_code": "BAD_REQUEST",
# MAGIC       "message": "TimeoutException: Tool XYZ failed to execute."
# MAGIC     }
# MAGIC   }
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC **注意：** クライアントアプリケーションはこれらのエラーを適切に処理し、表面化する必要があります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## E. （オプション）高度な機能とカスタマイゼーション
# MAGIC
# MAGIC Databricks Agent Frameworkは、洗練されたエージェント実装のためのいくつかの高度な機能を提供します。以下に示すトピックは、このコースの範囲を超えています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E1. カスタム入力と出力
# MAGIC
# MAGIC 一部のシナリオでは、チャット履歴に含まれるべきではない追加のエージェント入力（`client_type`、`session_id` など）や出力（検索ソースリンクなど）が必要です。
# MAGIC
# MAGIC **Custom Fields Support:**
# MAGIC - `custom_inputs`：標準メッセージを超える追加入力パラメータ。カスタム入力と出力について詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent#custom-inputs-and-outputs)をお読みください。
# MAGIC - `custom_outputs`：会話フローの一部ではない追加出力データ
# MAGIC - エージェントコード内で `request.custom_inputs` を介してアクセス
# MAGIC - AI PlaygroundとレビューアプリでのJSON設定
# MAGIC
# MAGIC **Important Limitation:**
# MAGIC Agent Evaluation レビューアプリは、追加の入力フィールドを持つエージェントのトレースレンダリングをサポートしていません。
# MAGIC
# MAGIC > この点に関する高度な機能について詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent#advanced-features)をお読みください。これはこのコースの範囲を超えています。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E2. レトリーバー統合とスキーマ
# MAGIC
# MAGIC AIエージェントは一般的に、Vector searchインデックスからの非構造化データ用のレトリーバーを使用します。Databricksは、レトリーバートレーシングと評価のための専門的なサポートを提供します。レトリーバー統合について詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unstructured-retrieval-tools#set-retriever-schema-to-ensure-mlflow-compatibility)をお読みください。 
# MAGIC
# MAGIC **Retriever Benefits:**
# MAGIC - AI Playground UIでの自動ソースドキュメントリンク
# MAGIC - 自動検索根拠性と関連性評価
# MAGIC - Databricks AI Bridgeレトリーバーツールとの統合
# MAGIC
# MAGIC **Custom Retriever Schema:**
# MAGIC ```python
# MAGIC import mlflow
# MAGIC
# MAGIC mlflow.models.set_retriever_schema(
# MAGIC name="mlflow_docs_vector_search",
# MAGIC primary_key="document_id",      # ドキュメントIDフィールド
# MAGIC text_column="chunk_text",       # コンテンツフィールド
# MAGIC doc_uri="doc_uri",             # ドキュメントURIフィールド
# MAGIC other_columns=["title"],        # 追加メタデータ
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC > これはこのコースの範囲を超えています。レトリーバーツールについて詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unstructured-retrieval-tools)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E3. マルチエージェントシステム
# MAGIC
# MAGIC Databricksは、複数の専門エージェントが協力して問題を解決する複雑なマルチエージェントシステムをサポートします。
# MAGIC
# MAGIC > これはこのコースの範囲を超えています。databricksによって管理されるマルチエージェントシステムについて詳しく学ぶには、[Genie](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)と[Agent Bricks](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)のドキュメントをお読みください。マルチエージェントシステムを備えたGenieについて詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ### E4. ステートフルエージェント
# MAGIC
# MAGIC ステートフルエージェントは、会話スレッド間でメモリを維持し、会話チェックポイント機能を提供できます。
# MAGIC
# MAGIC > これはこのコースの範囲を超えています。ステートフルエージェントについて詳しく学ぶには、[この](https://docs.databricks.com/aws/en/generative-ai/agent-framework/stateful-agents)ドキュメントをご覧ください。ステートフルAIエージェントについて詳しくは[こちら](https://docs.databricks.com/aws/en/generative-ai/agent-framework/stateful-agents)をお読みください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結論
# MAGIC
# MAGIC Databricks Mosaic AI Agent Frameworkは、プロダクション対応のAIエージェントを構築するための包括的なプラットフォームを提供します。主要なポイントには、人気frameworkの強み（例：LangChain）の理解、エージェントのライフサイクルを構築する際の開発と理解、そしてプロダクションに関する考慮事項が含まれます。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>