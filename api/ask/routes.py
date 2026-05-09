"""
api/ask/routes.py
-----------------
Endpoints for querying the AI agent.
Migrated from routes/ask.py and updated to use typed schemas.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.ask.schemas import AskRequest, AskResponse
from agents.rag.invoke_agent import ask_agent, aask_agent

logger = logging.getLogger(__name__)

ask_router = APIRouter(prefix="", tags=["Ask"])

@ask_router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest):
    """Synchronous ask — returns a complete response."""
    try:
        res, stats = ask_agent(session_id=payload.session_id, question=payload.question)
        return AskResponse(
            answer=res.get("answer", "no answer found. try again."),
            session_id=payload.session_id,
            stats=stats
        )
    except Exception as e:
        logger.error(f"error at ask agent. error: {str(e)}",)
        return HTTPException(status_code=500, detail=str(e))


@ask_router.post("/async-ask", response_model=AskResponse)
async def aask(payload: AskRequest):
    """Async ask — awaits the agent before returning."""
    try:
        res, stats = await aask_agent(session_id=payload.session_id, question=payload.question)
        return AskResponse(
            answer=res.get("answer", "no answer found. try again."),
            session_id=payload.session_id,
            stats=stats
        )
    except Exception as e:
        logger.error(f"error at aask agent. error: {str(e)}",)
        return HTTPException(status_code=500, detail=str(e))


@ask_router.post("/stream")
async def ask_stream(payload: AskRequest):
    """Streaming ask — yields response chunks as plain text."""

    async def generator():
        for word in ["streaming", "response", "for", "ask"]:
            yield word + " "
            await asyncio.sleep(0.1)

    return StreamingResponse(generator(), media_type="text/plain")


@ask_router.post("/async-stream")
async def aask_stream(payload: AskRequest):
    """Async streaming ask."""

    async def generator():
        for word in ["async", "streaming", "response"]:
            yield word + " "
            await asyncio.sleep(0.1)

    return StreamingResponse(generator(), media_type="text/plain")
