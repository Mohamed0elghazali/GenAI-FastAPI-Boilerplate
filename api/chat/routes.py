"""
api/chat/routes.py
------------------
CRUD endpoints for chat history.
Migrated from routes/chat.py and updated to use typed schemas.
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from api.chat.schemas import ChatCreateRequest, ChatResponse

chat_router = APIRouter(prefix="/chat", tags=["Chat History"])

# Temporary in-memory store — replace with DB calls
_DB: dict[str, dict] = {}


@chat_router.get("/", response_model=list[ChatResponse])
def list_chats():
    """Return all chat sessions."""
    return list(_DB.values())


@chat_router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: str):
    """Return a single chat session by ID."""
    chat = _DB.get(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@chat_router.post("/", response_model=ChatResponse, status_code=201)
def create_chat(payload: ChatCreateRequest):
    """Create a new chat session."""
    chat_id = str(uuid4())
    chat = {
        "id": chat_id,
        "title": payload.title,
        "messages": [],
        "metadata": payload.metadata,
    }
    _DB[chat_id] = chat
    return chat


@chat_router.delete("/{chat_id}", status_code=204)
def delete_chat(chat_id: str):
    """Delete a chat session."""
    if chat_id not in _DB:
        raise HTTPException(status_code=404, detail="Chat not found")
    del _DB[chat_id]
