"""
api/chat/schemas.py
-------------------
Pydantic request / response models for the /chat (history) endpoints.
"""

from typing import Any
from pydantic import BaseModel, Field


class ChatCreateRequest(BaseModel):
    title: str | None = Field(None, description="Optional chat title")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageItem(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatResponse(BaseModel):
    id: str
    title: str | None = None
    messages: list[MessageItem] = []
    metadata: dict[str, Any] = {}
