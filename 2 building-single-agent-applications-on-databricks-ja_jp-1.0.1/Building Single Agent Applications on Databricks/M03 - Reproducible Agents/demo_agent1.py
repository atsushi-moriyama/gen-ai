from databricks_langchain import ChatDatabricks, UCFunctionToolkit
from langchain.agents import create_agent  # 高レベルAPI
import json

class DatabricksAgent:
    def __init__(self, catalog_name: str, schema_name: str, config_file_path: str = "./demo_agent1_config.json"):
        self.catalog_name = catalog_name
        self.schema_name = schema_name
        self.config_file_path = config_file_path
        self._setup_agent()

    def _setup_agent(self):
        with open(self.config_file_path, "r") as f:
            config = json.load(f)

        tool_list_raw = config["tool_list"]
        llm_endpoint = config["llm_endpoint"]
        llm_temperature = config["llm_temperature"]
        system_prompt = config["system_prompt"]

        # 完全修飾されたUC関数名を構築する
        function_names = [f"{tool}" for tool in tool_list_raw]

        # UCツール
        toolkit = UCFunctionToolkit(function_names=function_names)
        tools = toolkit.tools

        # LLM
        llm = ChatDatabricks(endpoint=llm_endpoint, temperature=llm_temperature)

        # エージェントを作成する（AgentExecutorは不要）
        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

    def query(self, prompt: str, chat_history: list | None = None):
        # create_agent のメッセージ入力形式は [...] を想定
        messages = []
        if chat_history:
            # (「human」,「...」) / (『ai』,「...」) のようなタプルを受け入れ、OpenAIの役割にマッピングする
            role_map = {"human": "user", "ai": "assistant", "system": "system"}
            for role, content in chat_history:
                messages.append({"role": role_map.get(role, role), "content": content})
        messages.append({"role": "user", "content": prompt})

        return self.agent.invoke({"messages": messages})

    def ask(self, prompt: str, chat_history: list | None = None):
        return self.query(prompt, chat_history)