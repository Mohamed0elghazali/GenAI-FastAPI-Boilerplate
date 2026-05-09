from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    answer: str
    chunks: List[Dict[str, str]]
    tool_call: Dict[str, Dict[str, Any]] # Structure: {"tool_name": {"count": 0, "inputs": []}}
