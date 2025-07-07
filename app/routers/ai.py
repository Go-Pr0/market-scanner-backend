"""app/routers/ai.py
API router exposing AI-driven endpoints for question generation and advisor chat.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool

from app.core.security import require_auth
from app.services import ai_assistant_service
from app.services.ai_assistant_db import ai_assistant_db
from app.models.ai_assistant import (
    ChatMessageRequest, 
    ChatMessageResponse, 
    ChatListResponse, 
    ChatHistoryResponse,
    ChatMessage,
    ChatSession
)
from app.models.user import User

# ---------------------------------------------------------------------------
# Pydantic models for backward compatibility
# ---------------------------------------------------------------------------

class AnsweredItem(BaseModel):
    question: str
    answer: str

class GenerateQuestionsRequest(BaseModel):
    answered: List[AnsweredItem] = Field(..., description="List of previously answered Q&A pairs.")

class GenerateQuestionsResponse(BaseModel):
    additional_questions: List[str]


class SaveQuestionnaireRequest(BaseModel):
    questions: List[AnsweredItem] = Field(..., description="List of question/answer pairs to save.")


class SaveQuestionnaireResponse(BaseModel):
    success: bool
    message: str


class GetQuestionnaireResponse(BaseModel):
    questions: List[AnsweredItem]
    has_questionnaire: bool


# Legacy models for backward compatibility
class ChatAdvisorRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Chat ID to continue existing chat")
    status: Optional[str] = Field(None, description="Either 'pre-trade' or 'management'")
    data: Optional[Dict[str, Any]] = Field(None, description="Context data for new chats")
    message: str = Field(..., description="The user's message to the AI.")


class ChatAdvisorResponse(BaseModel):
    conversation_id: str
    reply: str
    new_chat: bool = False
    ended: bool = False


# ---------------------------------------------------------------------------
# Router definition
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["AI"])


@router.post("/questions/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    current_user: User = Depends(require_auth),
):
    """Tailor the next 3 AI-driven questions based on the already answered ones."""
    try:
        questions = await run_in_threadpool(
            ai_assistant_service.generate_questions,
            [item.model_dump() for item in request.answered],
        )
        return GenerateQuestionsResponse(additional_questions=questions)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/questionnaire/save", response_model=SaveQuestionnaireResponse)
async def save_questionnaire(
    request: SaveQuestionnaireRequest,
    current_user: User = Depends(require_auth),
):
    """Save user's questionnaire answers to the database."""
    try:
        # Convert to the format expected by the database
        questions_data = [
            {"question": item.question, "answer": item.answer}
            for item in request.questions
        ]
        
        success = await run_in_threadpool(
            ai_assistant_db.save_user_questionnaire,
            current_user.email,
            questions_data
        )
        
        if success:
            return SaveQuestionnaireResponse(
                success=True,
                message="Questionnaire saved successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save questionnaire")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/questionnaire", response_model=GetQuestionnaireResponse)
async def get_questionnaire(
    current_user: User = Depends(require_auth),
):
    """Get user's saved questionnaire answers from the database."""
    try:
        questionnaire_data = await run_in_threadpool(
            ai_assistant_db.get_user_questionnaire,
            current_user.email
        )
        
        if questionnaire_data:
            questions = [
                AnsweredItem(question=item.get("question", ""), answer=item.get("answer", ""))
                for item in questionnaire_data
            ]
            return GetQuestionnaireResponse(
                questions=questions,
                has_questionnaire=True
            )
        else:
            return GetQuestionnaireResponse(
                questions=[],
                has_questionnaire=False
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/questionnaire/check")
async def check_questionnaire_status(
    current_user: User = Depends(require_auth),
):
    """Check if user has completed their questionnaire setup."""
    try:
        questionnaire_data = await run_in_threadpool(
            ai_assistant_db.get_user_questionnaire,
            current_user.email
        )
        
        has_questionnaire = questionnaire_data is not None and len(questionnaire_data) > 0
        
        return {
            "has_questionnaire": has_questionnaire,
            "email": current_user.email
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(require_auth),
):
    """Send a message to the AI assistant."""
    try:
        chat_session, ai_message = await run_in_threadpool(
            ai_assistant_service.send_chat_message,
            current_user.id,
            request.message,
            request.chat_id,
            request.status,
            request.context_data
        )
        
        is_new_chat = request.chat_id is None
        
        return ChatMessageResponse(
            chat_id=chat_session.id,
            message=ai_message,
            is_new_chat=is_new_chat
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/recent", response_model=ChatListResponse)
async def get_recent_chats(
    limit: int = 50,
    current_user: User = Depends(require_auth),
):
    """Get recent chat sessions."""
    try:
        chats = await run_in_threadpool(
            ai_assistant_service.get_recent_chats,
            current_user.id,
            limit
        )
        return ChatListResponse(chats=chats)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: str,
    current_user: User = Depends(require_auth),
):
    """Get complete chat history for a specific chat."""
    try:
        result = await run_in_threadpool(
            ai_assistant_service.get_chat_history,
            chat_id,
            current_user.id
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        chat_session, messages = result
        return ChatHistoryResponse(chat=chat_session, messages=messages)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/chat/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(require_auth),
):
    """Delete a chat session."""
    try:
        success = await run_in_threadpool(
            ai_assistant_service.delete_chat,
            chat_id,
            current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Legacy endpoint for backward compatibility
@router.post("/chat/advisor", response_model=ChatAdvisorResponse)
async def chat_advisor(
    request: ChatAdvisorRequest,
    current_user: User = Depends(require_auth),
):
    """Legacy AI chat interaction endpoint (for backward compatibility)."""
    try:
        chat_session, ai_message = await run_in_threadpool(
            ai_assistant_service.send_chat_message,
            current_user.id,
            request.message,
            request.conversation_id,
            request.status,
            request.data
        )
        
        is_new_chat = request.conversation_id is None
        
        return ChatAdvisorResponse(
            conversation_id=chat_session.id,
            reply=ai_message.content,
            new_chat=is_new_chat,
            ended=False  # No longer support ending chats
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc 