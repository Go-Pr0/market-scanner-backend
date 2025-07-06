from __future__ import annotations

"""app/services/ai_service.py
Service layer that interfaces with Google Gemini (Generative AI) models.

It exposes two high-level helper methods that are used by the API layer:
1. ``generate_questions`` – one-shot content generation for follow-up questions.
2. ``chat_advisor`` – short-lived chat session that provides advice based on
   trade context (pre-trade or management).

NOTE: The Google client is created once at import time for efficiency.
"""

from typing import List, Dict, Any, Optional
import json
import logging
import os
import uuid
from google import genai

from app.core.config import settings
from app.services import prompts

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

_api_key: Optional[str] = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
if not _api_key:
    logger.warning("GEMINI_API_KEY is not configured – AI endpoints will raise errors.")
    # We still create a dummy client to avoid import errors; real calls will fail.
    genai_client: Optional[genai.Client] = None
else:
    genai_client = genai.Client(api_key=_api_key)


# ---------------------------------------------------------------------------
# Public service helpers
# ---------------------------------------------------------------------------


def _require_client() -> genai.Client:
    """Utility to ensure the Google client is available."""
    if genai_client is None:
        raise RuntimeError("GEMINI_API_KEY environment variable not set on the server.")
    return genai_client


# NOTE: This function is synchronous because the Google SDK uses blocking HTTP
# calls. It is designed to be executed with FastAPI's `run_in_threadpool`.

def generate_questions(answered: List[Dict[str, str]]) -> List[str]:
    """Generate three follow-up questions based on previously answered ones.

    Parameters
    ----------
    answered: List[Dict[str,str]]
        List of dicts with keys ``question`` and ``answer`` coming from the
        frontend.

    Returns
    -------
    List[str]
        Exactly three follow-up questions. If the AI returns a different number
        we will truncate or pad with empty strings to keep the contract.
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


###############################################################################
# Stateful chat sessions
###############################################################################


# In-memory store of active chat sessions. Key → genai.Chat instance.
# Each entry is a dict with keys: "chat", "status", "data" (initial context).
_CHAT_SESSIONS: Dict[str, Dict[str, Any]] = {}


def chat_advisor(
    status: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None,
    end: bool = False,
) -> Dict[str, Any]:
    """Stateful conversational advisor interface.

    Parameters
    ----------
    status : str
        "pre-trade" or "management" – indicates context. Required on new chat.
    message : str
        The user's message to send to the AI.
    data : dict | None
        Full questionnaire context. Required when starting a new chat.
    conversation_id : str | None
        If provided, continues an existing chat; otherwise a new chat starts.
    end : bool
        If True, the conversation will be terminated and forgotten **after** we
        return the reply.

    Returns
    -------
    dict
        {"conversation_id": str, "reply": str, "ended": bool}
    """

    client = _require_client()

    # If conversation_id is missing or unknown → start new chat
    new_chat = False
    chat_entry: Optional[Dict[str, Any]] = None

    if conversation_id and conversation_id in _CHAT_SESSIONS:
        chat_entry = _CHAT_SESSIONS[conversation_id]
    else:
        if data is None:
            raise ValueError("'data' field is required when starting a new conversation.")

        chat_obj = client.chats.create(model="gemini-2.5-pro-preview-06-05")
        system_msg = prompts.build_chat_advisor_system_message(status, data)
        chat_obj.send_message(system_msg)

        conversation_id = str(uuid.uuid4())
        chat_entry = {"chat": chat_obj, "status": status, "data": data}
        _CHAT_SESSIONS[conversation_id] = chat_entry
        new_chat = True

    chat: genai.Chat = chat_entry["chat"]  # type: ignore[assignment]

    # Send user message
    response = chat.send_message(message)

    reply_text: str = response.text.strip()

    final_reply = reply_text

    # Handle conversation end
    ended = False
    if end:
        _CHAT_SESSIONS.pop(conversation_id, None)
        ended = True

    return {
        "conversation_id": conversation_id,
        "reply": final_reply,
        "new_chat": new_chat,
        "ended": ended,
    } 