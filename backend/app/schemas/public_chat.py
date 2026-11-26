# Defines anonymous widget session and public chat response schemas.

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chatbot import PublicChatbotResponse


class PublicSessionResponse(BaseModel):
    session_token: str
    expires_in: int
    chatbot: PublicChatbotResponse


class PublicChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class PublicChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[PublicChatMessage] = Field(default_factory=list, max_length=6)


class PublicSource(BaseModel):
    source_number: int
    title: str
    page_number: int | None = None


class PublicChatResponse(BaseModel):
    request_id: str
    status: str
    answer: str
    sources: list[PublicSource] = Field(default_factory=list)
