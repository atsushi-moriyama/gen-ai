import json
from typing import Any, Callable, Generator, Optional
from uuid import uuid4
import warnings

import backoff
import mlflow
import openai
from databricks.sdk import WorkspaceClient
from databricks_openai import UCFunctionToolkit, VectorSearchRetrieverTool
from mlflow.entities import SpanType
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)
from openai import OpenAI
from pydantic import BaseModel
from unitycatalog.ai.core.base import get_uc_function_client

############################################
# LLM endpointとシステムプロンプトを定義する
############################################
with open('lab_agent_config.json', 'r') as f:
    config = json.load(f)

LLM_ENDPOINT_NAME = config["llm_endpoint"]

SYSTEM_PROMPT = config["system_prompt"]

UC_TOOL_NAMES = config["tool_list"]


###############################################################################
## ツール使用検証関数
###############################################################################
@mlflow.trace(
    span_type=SpanType.TOOL,
    name="Check Tool Usage"
)
def validate_tool_usage(result):
    """Check whether the model response used a tool and return a structured result."""
    
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default) if hasattr(obj, key) else default

    # 結果から出力を抽出する
    output_list = _get(result, "output", []) or []

    # ツールの使用方法を探す
    tool_calls = [
        item for item in output_list
        if _get(item, "type") in ("function_call", "function_call_output")
    ]

    if not tool_calls:
        return {
            "used_tool": False,
            "error": "No tools were used during the model response.",
        }

    # デバッグ用にツール名とコールIDを収集する
    tools_info = [
        {
            "name": _get(item, "name"),
            "call_id": _get(item, "call_id"),
            "type": _get(item, "type"),
        }
        for item in tool_calls
    ]

    return {
        "used_tool": True,
        "tools": tools_info,
        "tool_count": len(tools_info)
    }


@mlflow.trace(name="Evaluate Response")
def evaluate_response(result):
    """Evaluate the model response and raise error if no tool was used."""
    
    validation = validate_tool_usage(result)
    
    if not validation["used_tool"]:
        # ツールが使用されなかった場合、明示的にエラーを発生させる
        raise ValueError(validation["error"])
    
    return {
        "message": f"{validation['tool_count']} tool(s) used successfully.",
        "details": validation["tools"]
    }


###############################################################################
## エージェント用のツールを定義し、データ取得やアクション実行を可能にします
## テキスト生成を超えて
## より多くのツールの作成方法と使用例については、以下を参照してください。
## https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html
###############################################################################
class ToolInfo(BaseModel):
    """
    Class representing a tool for the agent.
    - "name" (str): The name of the tool.
    - "spec" (dict): JSON description of the tool (matches OpenAI Responses format)
    - "exec_fn" (Callable): Function that implements the tool logic
    """

    name: str
    spec: dict
    exec_fn: Callable


def create_tool_info(tool_spec, exec_fn_param: Optional[Callable] = None):
    tool_spec["function"].pop("strict", None)
    tool_name = tool_spec["function"]["name"]
    udf_name = tool_name.replace("__", ".")

    # UCツール呼び出し用のキーワード引数を受け取るラッパーを定義する
    # その後、それらをUCツール実行クライアントに渡します
    def exec_fn(**kwargs):
        function_result = uc_function_client.execute_function(udf_name, kwargs)
        if function_result.error is not None:
            return function_result.error
        else:
            return function_result.value
    return ToolInfo(name=tool_name, spec=tool_spec, exec_fn=exec_fn_param or exec_fn)


TOOL_INFOS = []

# Unity CatalogではUDFをエージェントツールとして使用できます

uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
uc_function_client = get_uc_function_client()
for tool_spec in uc_toolkit.tools:
    TOOL_INFOS.append(create_tool_info(tool_spec))


# Databricks vector searchインデックスをツールとして使用する
# 詳細は[ドキュメント](https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html)を参照してください

# # （オプション）Databricks vector searchインデックスをツールとして使用する
# # https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html を参照
# # 詳細については
VECTOR_SEARCH_TOOLS = []
# # TODO: vector searchインデックスをツールとして追加するか、このブロックを削除してください
# VECTOR_SEARCH_TOOLS.append(
#         VectorSearchRetrieverTool(
#         index_name="",
#         # filters="..."
#     )
# )
for vs_tool in VECTOR_SEARCH_TOOLS:
    TOOL_INFOS.append(create_tool_info(vs_tool.tool, vs_tool.execute))



class ToolCallingAgent(ResponsesAgent):
    """
    Class representing a tool-calling Agent
    """

    def __init__(self, llm_endpoint: str, tools: list[ToolInfo]):
        """Initializes the ToolCallingAgent with tools."""
        self.llm_endpoint = llm_endpoint
        self.workspace_client = WorkspaceClient()
        self.model_serving_client: OpenAI = (
            self.workspace_client.serving_endpoints.get_open_ai_client()
        )
        self._tools_dict = {tool.name: tool for tool in tools}

    def get_tool_specs(self) -> list[dict]:
        """Returns tool specifications in the format OpenAI expects."""
        return [tool_info.spec for tool_info in self._tools_dict.values()]

    @mlflow.trace(span_type=SpanType.TOOL)
    def execute_tool(self, tool_name: str, args: dict) -> Any:
        """Executes the specified tool with the given arguments."""
        return self._tools_dict[tool_name].exec_fn(**args)

    # def call_llm(self, messages: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
    #     with warnings.catch_warnings():
    #         warnings.filterwarnings("ignore", message="PydanticSerializationUnexpectedValue")
    #         for chunk in self.model_serving_client.chat.completions.create(
    #             model=self.llm_endpoint,
    #             messages=self.prep_msgs_for_cc_llm(messages),
    #             tools=self.get_tool_specs(),
    #             stream=True,
    #         ):
    #             chunk_dict = chunk.to_dict()
    #             if len(chunk_dict.get("choices", [])) > 0:
    #                 yield chunk_dict

    def call_llm(self, messages: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="PydanticSerializationUnexpectedValue")
            warnings.filterwarnings("ignore", message=".*Expected.*serialized value.*")  # Add this
            for chunk in self.model_serving_client.chat.completions.create(
                model=self.llm_endpoint,
                messages=self.prep_msgs_for_cc_llm(messages),
                tools=self.get_tool_specs(),
                stream=True,
            ):
                chunk_dict = chunk.to_dict()
                if len(chunk_dict.get("choices", [])) > 0:
                    yield chunk_dict

    def handle_tool_call(
        self,
        tool_call: dict[str, Any],
        messages: list[dict[str, Any]],
    ) -> ResponsesAgentStreamEvent:
        """
        Execute tool calls, add them to the running message history, and return a ResponsesStreamEvent w/ tool output
        """
        args = json.loads(tool_call["arguments"])
        result = str(self.execute_tool(tool_name=tool_call["name"], args=args))

        tool_call_output = self.create_function_call_output_item(tool_call["call_id"], result)
        messages.append(tool_call_output)
        return ResponsesAgentStreamEvent(type="response.output_item.done", item=tool_call_output)

    def call_and_run_tools(
        self,
        messages: list[dict[str, Any]],
        max_iter: int = 10,
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        for _ in range(max_iter):
            last_msg = messages[-1]
            if last_msg.get("role", None) == "assistant":
                return
            elif last_msg.get("type", None) == "function_call":
                yield self.handle_tool_call(last_msg, messages)
            else:
                yield from self.output_to_responses_items_stream(
                    chunks=self.call_llm(messages), aggregator=messages
                )

        yield ResponsesAgentStreamEvent(
            type="response.output_item.done",
            item=self.create_text_output_item("Max iterations reached. Stopping.", str(uuid4())),
        )

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """
        Process request and return response with tool usage validation.
        Raises ValueError if no tools were used.
        """
        outputs = [
            event.item
            for event in self.predict_stream(request)
            if event.type == "response.output_item.done"
        ]
        
        # レスポンスオブジェクトを作成する
        response = ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)
        
        # ツールが使用されたことを確認する
        evaluate_response(response)
        
        return response

    def predict_stream(
        self, request: ResponsesAgentRequest
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        messages = self.prep_msgs_for_cc_llm([i.model_dump() for i in request.input])
        if SYSTEM_PROMPT:
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        yield from self.call_and_run_tools(messages=messages)
    


# MLflowを使用してモデルをログに記録する
AGENT = ToolCallingAgent(llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS)
mlflow.models.set_model(AGENT)