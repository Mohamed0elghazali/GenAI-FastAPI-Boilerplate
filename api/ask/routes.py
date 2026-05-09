"""
api/ask/routes.py
-----------------
Endpoints for querying the AI agent.
Migrated from routes/ask.py and updated to use typed schemas.
"""

import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.ask.schemas import AskRequest, AskResponse

ask_router = APIRouter(prefix="/ask", tags=["Ask"])


@ask_router.post("/", response_model=AskResponse)
async def ask(payload: AskRequest):
    """Synchronous ask — returns a complete response."""
    return AskResponse(
        answer=f"Processed: {payload.question}",
        session_id=payload.session_id,
        mode="sync",
    )


@ask_router.post("/async", response_model=AskResponse)
async def aask(payload: AskRequest):
    """Async ask — awaits the agent before returning."""
    await asyncio.sleep(0.2)  # replace with real agent call
    return AskResponse(
        answer=f"Async processed: {payload.question}",
        session_id=payload.session_id,
        mode="async",
    )


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
