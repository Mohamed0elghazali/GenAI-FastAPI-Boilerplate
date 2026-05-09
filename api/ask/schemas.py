"""
api/ask/schemas.py
------------------
Pydantic request / response models for the /ask endpoints.
"""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question or prompt")
    session_id: str | None = Field(None, description="Optional session ID for context")
    stream: bool = Field(False, description="Whether to stream the response")


class AskResponse(BaseModel):
    answer: str
    session_id: str | None = None
    mode: str = "sync"
