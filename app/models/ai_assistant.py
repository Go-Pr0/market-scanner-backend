"""app/models/ai_assistant.py
Pydantic models for AI assistant chat system.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message model."""
    id: Optional[int] = None
    chat_id: str
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    """Chat session model."""
    id: str
    title: Optional[str] = None
    status: str = Field(..., description="Either 'pre-trade' or 'management'")
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    chat_id: Optional[str] = Field(None, description="Chat ID to continue existing chat")
    message: str = Field(..., description="User message content")
    status: Optional[str] = Field(None, description="Chat status for new chats")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data for new chats")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""
    chat_id: str
    message: ChatMessage
    is_new_chat: bool = False


class ChatListResponse(BaseModel):
    """Response model for listing chats."""
    chats: List[ChatSession]


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    chat: ChatSession
    messages: List[ChatMessage]