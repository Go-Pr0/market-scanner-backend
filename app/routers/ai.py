"""app/routers/ai.py
API router exposing AI-driven endpoints for question generation and advisor chat.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool

from app.core.security import require_auth
from app.services import ai_service  # type: ignore  # pylint: disable=import-error

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AnsweredItem(BaseModel):
    question: str
    answer: str

class GenerateQuestionsRequest(BaseModel):
    answered: List[AnsweredItem] = Field(..., description="List of previously answered Q&A pairs.")

class GenerateQuestionsResponse(BaseModel):
    additional_questions: List[str]


class ChatAdvisorRequest(BaseModel):
    # Conversation control
    conversation_id: Optional[str] = Field(
        None, description="Identifier for an ongoing conversation. Omit to start a new one."
    )
    end: bool = Field(False, description="Set true to end and discard the conversation after this message.")

    # Context / metadata
    status: str = Field(..., description="Either 'pre-trade' or 'management'. Required on new chat.")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Full questionnaire context. Required only when starting a new conversation.",
    )

    # User message
    message: str = Field(..., description="The user's message to the AI.")


class ChatAdvisorResponse(BaseModel):
    conversation_id: str
    reply: str
    new_chat: bool
    ended: bool


# ---------------------------------------------------------------------------
# Router definition
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["AI"])


@router.post("/questions/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    _: bool = Depends(require_auth),
):
    """Tailor the next 3 AI-driven questions based on the already answered ones."""
    try:
        questions = await run_in_threadpool(
            ai_service.generate_questions,
            [item.model_dump() for item in request.answered],
        )
        return GenerateQuestionsResponse(additional_questions=questions)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/advisor", response_model=ChatAdvisorResponse)
async def chat_advisor(
    request: ChatAdvisorRequest,
    _: bool = Depends(require_auth),
):
    """Main AI chat interaction endpoint (pre-trade or management)."""
    try:
        result = await run_in_threadpool(
            ai_service.chat_advisor,
            request.status,
            request.message,
            request.data,
            request.conversation_id,
            request.end,
        )
        return ChatAdvisorResponse(**result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc 