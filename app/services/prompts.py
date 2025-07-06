"""app/services/prompts.py

This module centralizes all prompts used for interacting with the Google Gemini AI.
Keeping prompts in one place makes them easier to manage, version, and refine.
"""

import json
from typing import Dict, Any

# ==============================================================================
# PROMPT 1: Generate Follow-up Questions
# ==============================================================================

# ------------------------------------------------------------------------------
# Usage:
# - Used by: `ai_service.generate_questions()`
# - Purpose: To generate three tailored follow-up questions based on a user's
#            initial trade checklist answers.
#
# Response Format Requirement:
# - MUST return a valid JSON object.
# - The JSON should have a single top-level key: "additional_questions".
# - The value should be an array of exactly three strings.
# - Example: {"additional_questions": ["q1", "q2", "q3"]}
# ------------------------------------------------------------------------------
GENERATE_QUESTIONS_PROMPT = """
You are an AI assistant that helps a trader perform pre-trade risk
checks. Given the already answered questions, suggest EXACTLY three
additional follow-up based on the answers. Do not ask about risk management,
nor about trading strategies themselves. They should be about:
- trader psychology
- behavioral reflection
- behavioral audit

Return the result ONLY as valid JSON with the top-level
key 'additional_questions' containing an array of three strings.

The JSON response MUST be wrapped in a markdown code block.
For example:
```json
{
  "additional_questions": ["q1", "q2", "q3"]
}
```
""".strip()


# ==============================================================================
# PROMPT 2: Conversational Chat Advisor
# ==============================================================================

# ------------------------------------------------------------------------------
# Usage:
# - Used by: `ai_service.chat_advisor()` via `build_chat_advisor_system_message()`
# - Purpose: To act as the initial system message that sets the context for a
#            stateful conversational chat with a trader.
#
# Response Format Requirement:
# - SHOULD return plain, conversational text.
# - It should NOT be formatted as JSON.
# ------------------------------------------------------------------------------
def build_chat_advisor_system_message(status: str, data: Dict[str, Any]) -> str:
    """
    Constructs the system context message for a chat advisor session.

    Args:
        status: The context of the chat, either "pre-trade" or "management".
        data: The initial questionnaire data to ground the conversation.

    Returns:
        A formatted string to be used as the initial system prompt.
    """
    if status.lower() == "management":
        role_instruction = (
            "You are an AI assistant helping a trader evaluate an **existing** "
            "open position for continuation, adjustment, or exit."
            "Ask me about my management plan for this trade, and why I want to alter anything"
            "Then."
        )
    else:  # Default to "pre-trade"
        role_instruction = (
            "You are an AI assistant helping a trader evaluate a **new** trade "
            "before entry. Ask me about my trading plan, and why I want to enter this trade."
            "Ask me things such as: if I planned the trade beforehand,etc. Focus on my mentality"
            "& space of mind while going into this trade, tailor your questions to that."
            "Do not focus on the technicals."
        )

    system_context = (
        f"{role_instruction}\n\n"
        f"This is a questionnaire that I filled out with some things I have been working on:\n"
        f"{json.dumps(data, indent=2)}\n\n"
        "The goal here should be to help me reflect on the objective I stated at the start before I perform this action."
        "Help me think though everything, ask me whether or not it's within my trading plan."
        "Keep the conversation going, and ask me questions about what I asked you to ask me."
        "do NOT mention risk management, and just head straight in from here, returning"
        "only the answer, and not refering to what I just said."
        "keep the conversation going until we reach a conclusion."
        "Start the convo, only ask one question at a time."
    )
    return system_context