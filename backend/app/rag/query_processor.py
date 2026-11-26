# Validates and prepares user questions for retrieval.
# Semantic meaning preserve karna important hai — aggressive preprocessing avoid karte hain.

import logging
from typing import Optional

from app.core.config import settings
from app.schemas.chat import ConversationMessage

logger = logging.getLogger(__name__)

# Standalone query banane ke liye use karte hain jab follow-up question ambiguous ho.
_FOLLOWUP_INDICATORS = [
    " it ", " its ", " this ", " that ", " they ", " their ", " he ", " she ",
    "it?", "them?", "that?", "this?", " do so", " the same",
]


def validate_question(question: str) -> str:
    """Validate and clean the user question.

    Semantic meaning preserve karte hain — sirf leading/trailing whitespace remove karte hain.
    Technical terms, numbers, dates, aur named entities intact rehte hain.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    cleaned = question.strip()

    if len(cleaned) > settings.RAG_MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Question is too long. Maximum allowed length is {settings.RAG_MAX_QUESTION_LENGTH} characters."
        )

    return cleaned


def build_retrieval_query(
    question: str,
    history: Optional[list[ConversationMessage]] = None,
) -> str:
    """Build a retrieval-ready query from the question and conversation context.

    Follow-up questions mein pronouns aur references ambiguous hote hain.
    Pichle conversation ka context add karke retrieval query improve karte hain.
    """
    if not history:
        return question

    # Recent messages se context nikalo — bounded history use karte hain.
    recent = history[-(settings.RAG_MAX_HISTORY_MESSAGES):]

    # Agar question clearly standalone hai (no pronouns/references) to as-is return karo.
    question_lower = question.lower()
    has_ambiguity = any(indicator in f" {question_lower} " for indicator in _FOLLOWUP_INDICATORS)
    if not has_ambiguity and len(question.split()) > 4:
        return question

    # Pichle user message se context add karo.
    last_user_content = ""
    for msg in reversed(recent):
        if msg.role == "user" and msg.content != question:
            last_user_content = msg.content.strip()
            break

    if last_user_content:
        # Context-aware query: pichle topic ko current question ke saath combine karo.
        combined = f"{last_user_content} {question}"
        # Token estimate karo — rough 4 chars per token.
        if len(combined) <= settings.RAG_MAX_QUESTION_LENGTH:
            return combined

    return question


def estimate_tokens(text: str) -> int:
    """Rough token estimate — accurate tokenizer nahi hai, isliye conservative estimate use karte hain.

    Actual LLM tokenizers alag hote hain — ye sirf context budgeting ke liye hai.
    """
    # ~4 characters per token is a common conservative estimate for English text.
    return max(1, len(text) // 4)
