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
# MAGIC # 講義 - DatabricksにおけるUnity Catalog関数のエージェントツールとしての活用
# MAGIC
# MAGIC ## 概要
# MAGIC
# MAGIC 「ミッション地区の平均住宅価格は？」や「トップクライアントの顧客生涯価値を計算して」といった質問に対して、適切なデータ操作とビジネスロジックを自動的に発見・実行できるAIエージェントを想像してみてください。これがUnity Catalog関数をエージェントツールとして活用する力です。
# MAGIC
# MAGIC AIエージェントとツールの基本概念を基盤として、このセッションでは最も実用的な実装の一つに焦点を当てます：Unity CatalogのSQLおよびPython関数を、自然言語クエリに基づいてAIエージェントが自動的に選択・実行できる、インテリジェントで発見可能なツールとして使用することです。
# MAGIC
# MAGIC この講義では、続く実践的なデモンストレーションに必要な技術的基盤とベストプラクティスを確立します。そこでは[AI Playground](https://docs.databricks.com/aws/en/generative-ai/agent-framework/ai-playground-agent)を使用して、SQLとPythonのUnity Catalog関数をエージェントツールとして構築・テストします。
# MAGIC
# MAGIC ### 学習目標
# MAGIC
# MAGIC _この講義の終了時には、以下のことができるようになります：_
# MAGIC
# MAGIC - UC関数とエージェントツールの基本的な違いを理解する
# MAGIC - SQLとPythonエージェントツールの違いを説明する
# MAGIC - SQL関数の登録方法を説明する
# MAGIC - Python関数の登録方法の違いを説明する
# MAGIC - Databricks UIを使用して登録された関数を探索する方法を理解する
# MAGIC - AI PlaygroundがUCツールとどのように統合されるかを理解する

# COMMAND ----------

# MAGIC %md
# MAGIC ## A. Unity Catalog関数をエージェントツールとして理解する

# COMMAND ----------

# MAGIC %md
# MAGIC ### A1. Unity Catalog関数のエージェントツールとは？
# MAGIC
# MAGIC 始める前に、UC関数が何であるかを念頭に置くことが重要です。Unity Catalogツールは実際には、内部的にはUnity Catalogユーザー定義関数（UDF）です。Unity Catalogツールを定義するとき、Unity Catalogに関数を登録しています。Unity Catalog UDFについて詳しく学ぶには、[このドキュメント](https://docs.databricks.com/aws/en/udf/unity-catalog)をご覧ください。
# MAGIC
# MAGIC > **UDFとは？** 
# MAGIC > Unity Catalogのユーザー定義関数（UDF）は、Databricks内でSQLとPythonの機能を拡張します。カスタム関数を定義し、使用し、コンピューティング環境間で安全に共有・ガバナンスできます。
# MAGIC
# MAGIC **Unity Catalog関数のエージェントツール** は、SQLまたはPythonで書かれたUnity Catalog関数で、AIエージェントがデータ操作やビジネスロジックを実行するために動的に発見、選択、実行できるものです。手動プログラミングで呼び出す必要がある従来の関数とは異なり、Unity Catalog関数のエージェントツールは以下のように設計されています：
# MAGIC
# MAGIC - 包括的なメタデータとドキュメントを通じた **自己記述**
# MAGIC - 特定のビジネスや分析タスクに **文脈的に適切**
# MAGIC - Unity Catalogのセキュリティとアクセス制御メカニズムを通じた **ガバナンス可能**

# COMMAND ----------

# MAGIC %md
# MAGIC ### A2. SQLとPythonエージェントツール：主な違いと使用例
# MAGIC
# MAGIC
# MAGIC
# MAGIC ![sql-fun-vs-agent-tool.png](../Includes/images/sql-fun-vs-agent-tool.png "sql-fun-vs-agent-tool.png")
# MAGIC
# MAGIC <p>
# MAGIC <em>
# MAGIC UC SQL関数をエージェントツールとして使用するための構造化例。
# MAGIC </em>
# MAGIC </p>
# MAGIC
# MAGIC 効果的なエージェントツール実装のために、SQLとPython関数をいつ使用するかを理解することが重要です：
# MAGIC
# MAGIC **SQL Agent Tools**
# MAGIC - データクエリと分析操作に最適化
# MAGIC - `CREATE OR REPLACE FUNCTION` 文を使用して実行
# MAGIC - SQL構文と組み込み関数に限定
# MAGIC - サーバーレスモードでのみ実行
# MAGIC - 自動クエリ最適化とキャッシング
# MAGIC - 理想的な用途：データ取得、集計、フィルタリング、分析計算
# MAGIC
# MAGIC **Python Agent Tools**
# MAGIC - カスタムPythonロジックと複雑な計算を実行
# MAGIC - 外部APIやライブラリとの統合をサポート
# MAGIC - 柔軟な実行モード（サーバーレスとローカル）を提供
# MAGIC - 明示的な型ヒントとGoogle形式のdocstringが必要
# MAGIC - 高度なエラーハンドリングとデバッグ機能をサポート
# MAGIC - 理想的な用途：ビジネスロジック、外部統合、複雑なアルゴリズム、データ変換
# MAGIC
# MAGIC **Combining Tools**： 最も強力なエージェントアーキテクチャは、SQLとPythonツールを組み合わせて使用し、SQLがデータアクセスと分析を処理し、Python関数がビジネスロジックと外部統合を管理します。

# COMMAND ----------

# MAGIC %md
# MAGIC ### A3. エージェントツールと従来の関数
# MAGIC
# MAGIC 効果的な実装のために、エージェントツールと従来の関数の違いを理解することが重要です：
# MAGIC
# MAGIC - **Traditional Functions**
# MAGIC     - 開発者による直接的なプログラム使用のために設計
# MAGIC     - 限定的または最小限のドキュメント要件
# MAGIC     - 既知のパラメータで明示的に呼び出し
# MAGIC     - 計算効率とパフォーマンスに焦点
# MAGIC
# MAGIC - **Unity Catalog Functions as Agent Tools**
# MAGIC     - AIエージェントによる動的発見と使用のために設計
# MAGIC     - 豊富なメタデータと包括的なドキュメントが必要
# MAGIC     - 自然言語クエリからパラメータと使用法を推論
# MAGIC     - 明確性、解釈可能性、エージェントの使いやすさに焦点
# MAGIC     - ビジネスコンテキストと使用例を含む
# MAGIC
# MAGIC ![python-function-diagram.png](../Includes/images/python-function-diagram.png "python-function-diagram.png")
# MAGIC
# MAGIC <p align="center"><em>SQLツールの使用方法と同様に、エージェントは脳を使ってUC Pythonツールの実行を推論し、計画を立てます。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ## B. 登録方法

# COMMAND ----------

# MAGIC %md
# MAGIC ### B2. 関数登録方法
# MAGIC
# MAGIC Unity CatalogはSQLとPython関数をエージェントツールとして登録するための異なるアプローチを提供します。UC登録関数はUC権限によってガバナンスされるため、セッションスコープ/ノートブックUDFと比較した場合の登録が差別化されます。
# MAGIC
# MAGIC
# MAGIC ![sql-registration-diagram](../Includes/images/sql-registration-diagram.png "sql-registration-diagram")
# MAGIC
# MAGIC
# MAGIC #### SQL関数登録
# MAGIC - [`CREATE OR REPLACE FUNCTION`文](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-sql-function)を使用：
# MAGIC   - 即座の登録と利用可能性
# MAGIC   - 関数定義とメタデータの完全な制御
# MAGIC   - 既存のSQL開発workflowsとの統合
# MAGIC   - 複雑なSQLロジックとビジネスルールのサポート
# MAGIC   - カスタム環境や依存関係のサポートなし
# MAGIC
# MAGIC ![python-registration-diagram](../Includes/images/python-registration-diagram.png "python-registration-diagram")
# MAGIC
# MAGIC #### Python関数登録
# MAGIC - [`DatabricksFunctionClient()`](https://docs.unitycatalog.io/ai/client/#databricks-function-client)を使用：
# MAGIC   - `create_python_function()` APIがPython呼び出し可能オブジェクトを直接受け入れ
# MAGIC   - 型ヒントとdocstringメタデータの自動抽出
# MAGIC   - Unity Catalogの3層名前空間との統合
# MAGIC   - 関数のバージョニングと置換のサポート
# MAGIC   - サーバーレス（本番）とローカル（開発）モードをサポートしますが、ローカルモードは[SQLベースの関数をサポートしません](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)
# MAGIC - [`CREATE OR REPLACE FUNCTION`文](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-sql-function)を使用：
# MAGIC   - SQLツール作成と同様に、Pythonロジックを使用してSQL構文で登録するPython関数も作成できます（例は[こちら](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-sql-function#create-python-functions)を参照）。
# MAGIC   - `ENVIRONMENT` 句を使用してカスタム依存関係を定義できます（詳細は[こちら](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-sql-function#define-custom-dependencies-in-python-functions)）。

# COMMAND ----------

# MAGIC %md
# MAGIC ### B3. （オプション）実行環境の考慮事項
# MAGIC
# MAGIC UC Python関数の技術的考慮事項（サーバーレス vs ローカルモード）について詳しく読むには、[このドキュメント](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool#running-functions-using-serverless-or-local-mode)をご覧ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## C. UIによるツール登録の検証
# MAGIC
# MAGIC 関数がUnity Catalogに登録されると、LLMがコンテキストとクエリフィルタリングのために消費するメタデータ情報を検証できます。以下は、UC内のツールの場所をナビゲートする際に期待される2つの例です。
# MAGIC
# MAGIC ![sql-func-validation.png](../Includes/images/sql-func-validation.png "sql-func-validation.png")
# MAGIC
# MAGIC <p align="center"><em> コンテキストと使用法のためのLLMフレンドリーなノートで登録されたSQL UC関数の例。</em></p>
# MAGIC
# MAGIC ![python-tool-ui.png](../Includes/images/python-tool-ui.png "python-tool-ui.png")
# MAGIC
# MAGIC <p align="center"><em> SQL関数と同様に、登録されたPython関数では、説明、定義、その他のメタデータを確認できます。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ## D. プロトタイピングのためのAI Playgroundとの統合

# COMMAND ----------

# MAGIC %md
# MAGIC ### D1. AI Playground統合
# MAGIC
# MAGIC AI PlaygroundはSQLとPythonのUnity Catalog関数をエージェントツールとしてテストとプロトタイピングするためのノーコードインターフェースを提供します。AI Playgroundでは、UC権限レベルでのツールへの自動アクセスと、ClaudeやGPTモデルなどの最先端LLMにアクセスできます。AI Playgroundは、エージェントコードを構築する前に、クエリ、LLM、ツール使用をプロトタイピングするために使用すべきです。以下は、LLMからのツール使用を呼び出すプロンプトを送信する際のAI Playgroundの外観例です。
# MAGIC
# MAGIC ![ai-playground-tools.png](../Includes/images/ai-playground-tools.png "ai-playground-tools.png")
# MAGIC
# MAGIC <p align="center"><em>AI Playgroundでは、例えばGPT-5.1のように、一部のモデルにツールを追加する機能があります。</em></p>

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC これでUCツールがどのように構築、登録、視覚的に検査、Databricksでテストできるかを理解したので、これらの概念を実践でカバーするフォローアロングデモンストレーションの準備が整いました。

# COMMAND ----------

# MAGIC %md
# MAGIC &copy; 2026 Databricks, Inc. All rights reserved. Apache, Apache Spark, Spark, the Spark Logo, Apache Iceberg, Iceberg, and the Apache Iceberg logo are trademarks of the <a href="https://www.apache.org/" target="_blank">Apache Software Foundation</a>.<br/><br/><a href="https://databricks.com/privacy-policy" target="_blank">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use" target="_blank">Terms of Use</a> | <a href="https://help.databricks.com/" target="_blank">Support</a>