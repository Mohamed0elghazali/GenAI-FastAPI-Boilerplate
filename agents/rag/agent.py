import re
import logging

from datetime import datetime
from time import perf_counter
from langgraph.graph import StateGraph, START, END
from typing import Literal, Dict
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver  

from core.clients import ClientFactory
from agents.callbacks.handler import callback_handler
from agents.rag.prompts.system_prompt import SYSTEM_PROMPT
from agents.rag.tools.tools_limits import TOOL_CALL_LIMITS
from agents.rag.tools.file_system_tools import write_file_tool
from agents.rag.models import AgentState

logger = logging.getLogger(__name__)

LLM = ClientFactory.get_llm()

tools = [write_file_tool]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = LLM.bind_tools(tools)
tools_description = "\n\n".join([f'{tool.name}\n{tool.description}' for tool in tools])

def check_tool_call_limit(state: AgentState, tool_call_name: str):
    """Check if the tool call limit is exceeded"""
    tool_call_num = state.get("tool_call", {}).get(tool_call_name, {}).get("count", 0)
    tool_call_limit = TOOL_CALL_LIMITS.get(tool_call_name, 3)

    if tool_call_num > tool_call_limit:
        return True
    return False

def update_tool_call(state: AgentState, tool_call_name: str, tool_call_args: dict, tool_call_outupt: dict):
    """Update the tool call count and arguments"""
    if "tool_call" not in state:
        state["tool_call"] = {}

    if tool_call_name not in state["tool_call"]:
        state["tool_call"][tool_call_name] = {"count": 0, "inputs": [], "outputs": []}

    state["tool_call"][tool_call_name]["count"] += 1
    state["tool_call"][tool_call_name]["inputs"].append(tool_call_args)
    state["tool_call"][tool_call_name]["outputs"].append(tool_call_outupt)

def init_state(state: AgentState) -> AgentState:
    state["chunks"] = []
    state["tool_call"] = {}
    return state

def llm_call(state: AgentState) -> AgentState:
    """LLM decides whether to call a tool or not"""

    system_prompt_1 = [
        SystemMessage(
            content=[
                {"text": SYSTEM_PROMPT.format(TOOLS_PLACEHOLDER=tools_description)},
                {"cachePoint": {"type": "default"}},
            ]
        )
    ]
    system_prompt_2 = [SystemMessage(content=f"Current Time is {datetime.now()}")]
    messages = system_prompt_1 + system_prompt_2 + state["messages"]
    state["messages"] = [llm_with_tools.invoke(messages)]
    return state

def tool_node(state: AgentState) -> AgentState:
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # check tool call limit
        if check_tool_call_limit(state, tool_name):
            tool_result = (
                f"SYSTEM ERROR: The tool '{tool_name}' has exceeded its execution limit. "
                "DO NOT try to call this tool again. "
                "If the current context is enough, provide the final answer now. "
                "If you are missing critical info, politely ask the user to provide the missing details."
            )
        else:
            tool = tools_by_name[tool_name]
            tool_result = tool.invoke(tool_args)
            update_tool_call(state, tool_name, tool_args, tool_result)
        
        result.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))
        state["messages"] = result
    return state

def output_response(state: AgentState):
    final_answer = state["messages"][-1].content
    match = re.search(r'<thinking>(.*?)</thinking>', final_answer, re.DOTALL)
    thinking_variable = match.group(1).strip() if match else None
    state["answer"] = re.sub(r'<thinking>.*?</thinking>', '', final_answer, flags=re.DOTALL).strip()
    state["thinking"] = thinking_variable
    return state

def should_continue(state: AgentState) -> Literal["Action", "END"]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "Action"
    # Otherwise, we stop (reply to the user)
    return "END"

agent_builder = StateGraph(AgentState)
agent_builder.add_node("init_state", init_state)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("environment", tool_node)
agent_builder.add_node("output_response", output_response)

agent_builder.add_edge(START, "init_state")
agent_builder.add_edge("init_state", "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "Action": "environment",
        "END": "output_response",
    },
)
agent_builder.add_edge("environment", "llm_call")
agent_builder.add_edge("output_response", END)

checkpointer = InMemorySaver()

agent = agent_builder.compile(checkpointer=checkpointer)

def ask_agent(session_id: str, question: str) -> tuple[AgentState, Dict[str, int]]:
    start_time = perf_counter()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={
            "callbacks": [callback_handler],
            "configurable": {"thread_id": session_id},
        },
    )
    exec_time = perf_counter() - start_time
    request_stats = callback_handler.get_request_stats()
    request_stats["exec_time"] = exec_time
    logger.info(f"Response: {response}")
    logger.info(f"Total Stats: {callback_handler.get_total_stats()}")
    return response, request_stats

if __name__ == "__main__":
    response, stats = ask_agent("user1", "ما هى عاصمة مصر")
    print(response)
    print(stats)
    print("\n")
    for msg in response["messages"]:
        msg.pretty_print()
