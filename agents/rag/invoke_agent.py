"""
"""
from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import Dict

from agents.rag.agent import rag_agent
from agents.callbacks.handler import callback_handler
from agents.rag.models import AgentState

logger = logging.getLogger(__name__)

def ask_agent(session_id: str, question: str) -> tuple[AgentState, Dict[str, int]]:
    start_time = perf_counter()
    res = rag_agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={
            "callbacks": [callback_handler],
            "configurable": {"thread_id": session_id},
        },
    )
    exec_time = perf_counter() - start_time
    request_stats = callback_handler.get_request_stats()
    request_stats["exec_time"] = exec_time
    logger.info(f"Response: {res}")
    logger.info(f"Total Stats: {callback_handler.get_total_stats()}")
    return res, request_stats

async def aask_agent(session_id: str, question: str) -> tuple[AgentState, Dict[str, int]]:
    start_time = perf_counter()
    response = await rag_agent.ainvoke(
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
