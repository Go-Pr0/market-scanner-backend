"""app/services/ai_assistant_service.py
New AI assistant service with persistent chat storage and individual message handling.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from google import genai

from app.core.config import config
from app.services import prompts
from app.services.ai_assistant_db import ai_assistant_db
from app.services.user_db import user_db
from app.models.ai_assistant import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

_api_key: Optional[str] = config.GEMINI_API_KEY
if not _api_key:
    logger.warning("GEMINI_API_KEY is not configured – AI endpoints will raise errors.")
    genai_client: Optional[genai.Client] = None
else:
    genai_client = genai.Client(api_key=_api_key)


def _require_client() -> genai.Client:
    """Utility to ensure the Google client is available."""
    if genai_client is None:
        raise RuntimeError("GEMINI_API_KEY environment variable not set on the server.")
    return genai_client


def generate_questions(answered: List[Dict[str, str]]) -> List[str]:
    """Generate three follow-up questions based on previously answered ones.
    
    This function remains unchanged from the original implementation.
    """
    client = _require_client()
    
    prompt = f"{prompts.GENERATE_QUESTIONS_PROMPT}\n\nPREVIOUS ANSWERS:\n{json.dumps(answered, indent=2)}"

    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-06-05",
        contents=prompt,
    )

    text: str = response.text.strip()

    # Find the JSON block and parse it
    try:
        # Extract content from the first markdown code block
        json_str = text.split("```json")[1].split("```")[0].strip()
        parsed = json.loads(json_str)
        questions = parsed.get("additional_questions", [])

        if not isinstance(questions, list):
            raise ValueError("Parsed 'additional_questions' is not a list.")

    except (IndexError, json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "Failed to parse AI JSON response, falling back to line split. Error: %s. Response: %s",
            exc,
            text,
            exc_info=True,
        )
        # Fallback: split by lines and pick first three non-empty lines
        lines = [ln.strip("- •* \t") for ln in text.splitlines() if ln.strip()]
        questions = lines[:3]

    # Ensure exactly three questions are returned
    questions = [str(q) for q in questions][:3]
    while len(questions) < 3:
        questions.append("")
    return questions


def _generate_chat_title(first_user_message: str, status: str) -> str:
    """Generate a title for the chat based on the first user message."""
    # Simple title generation - take first 50 chars and add status
    title_base = first_user_message[:50].strip()
    if len(first_user_message) > 50:
        title_base += "..."
    
    status_prefix = "Pre-trade" if status == "pre-trade" else "Management"
    return f"{status_prefix}: {title_base}"


def _build_message_history(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    """Build message history for Gemini API from stored messages."""
    history = []
    for msg in messages:
        # Convert our role names to Gemini's expected format
        role = "user" if msg.role == "user" else "model"
        history.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })
    return history


def send_chat_message(
    user_id: int,
    message: str,
    chat_id: Optional[str] = None,
    status: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> Tuple[ChatSession, ChatMessage]:
    """Send a message to the AI assistant and get a response.
    
    Args:
        user_id: ID of the user sending the message
        message: User message content
        chat_id: Existing chat ID to continue conversation
        status: Chat status for new chats ('pre-trade' or 'management')
        context_data: Context data for new chats (ignored - questionnaire retrieved from DB)
        
    Returns:
        Tuple of (ChatSession, AI response ChatMessage)
    """
    client = _require_client()
    
    # Get or create chat session
    if chat_id:
        chat_session = ai_assistant_db.get_chat_session(chat_id, user_id)
        if not chat_session:
            raise ValueError(f"Chat session {chat_id} not found or access denied")
        is_new_chat = False
    else:
        if not status:
            raise ValueError("Status is required for new chat sessions")
        
        # Get user information to retrieve questionnaire
        user = user_db.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Retrieve questionnaire data from database
        questionnaire_data = ai_assistant_db.get_user_questionnaire(user.email)
        if not questionnaire_data:
            logger.warning(f"No questionnaire data found for user {user.email}")
            questionnaire_data = []
        
        # Build context data from questionnaire
        db_context_data = {
            "questions": [q.get("question", "") for q in questionnaire_data],
            "answers": [q.get("answer", "") for q in questionnaire_data],
            "questionnaire_complete": len(questionnaire_data) > 0
        }
        
        # Generate title from first message
        title = _generate_chat_title(message, status)
        chat_session = ai_assistant_db.create_chat_session(
            user_id=user_id,
            status=status,
            context_data=db_context_data,
            title=title
        )
        is_new_chat = True
    
    # Store user message
    user_message = ai_assistant_db.add_message(
        chat_id=chat_session.id,
        role="user",
        content=message
    )
    
    # Get chat history for context
    all_messages = ai_assistant_db.get_chat_messages(chat_session.id)
    
    # Build the conversation for Gemini
    if is_new_chat:
        # For new chats, start with system message
        system_message = prompts.build_chat_advisor_system_message(
            chat_session.status, 
            chat_session.context_data or {}
        )
        
        # Send system message and user message together
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05",
            contents=[
                {"role": "user", "parts": [{"text": system_message}]},
                {"role": "user", "parts": [{"text": message}]}
            ]
        )
    else:
        # For continuing chats, build full history
        # Skip the user message we just added since we'll send it separately
        history_messages = all_messages[:-1]
        
        # Build conversation history
        conversation_history = []
        
        # Add system message if this is the first continuation
        if len(history_messages) == 0:
            system_message = prompts.build_chat_advisor_system_message(
                chat_session.status, 
                chat_session.context_data or {}
            )
            conversation_history.append({
                "role": "user", 
                "parts": [{"text": system_message}]
            })
        
        # Add message history
        for msg in history_messages:
            role = "user" if msg.role == "user" else "model"
            conversation_history.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        # Add current user message
        conversation_history.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05",
            contents=conversation_history
        )
    
    # Get AI response text
    ai_response_text = response.text.strip()
    
    # Store AI response
    ai_message = ai_assistant_db.add_message(
        chat_id=chat_session.id,
        role="assistant",
        content=ai_response_text
    )
    
    return chat_session, ai_message


def get_chat_history(chat_id: str, user_id: int) -> Optional[Tuple[ChatSession, List[ChatMessage]]]:
    """Get complete chat history for a user."""
    return ai_assistant_db.get_chat_history(chat_id, user_id)


def get_recent_chats(user_id: int, limit: int = 50) -> List[ChatSession]:
    """Get recent chat sessions for a user."""
    return ai_assistant_db.get_recent_chats(user_id, limit)


def delete_chat(chat_id: str, user_id: int) -> bool:
    """Delete a chat session for a user."""
    # Verify the chat belongs to the user before deleting
    chat_session = ai_assistant_db.get_chat_session(chat_id, user_id)
    if not chat_session:
        return False
    
    return ai_assistant_db.delete_chat_session(chat_id)