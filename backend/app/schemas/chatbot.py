# Defines chatbot configuration request and response schemas.

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.services.domain_service import normalize_origin


class ChatbotUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    welcome_message: str | None = Field(default=None, max_length=500)
    placeholder: str | None = Field(default=None, max_length=150)
    primary_color: str | None = None
    position: Literal["bottom-right", "bottom-left"] | None = None
    launcher_label: str | None = Field(default=None, max_length=50)
    suggested_questions: list[str] | None = None
    allowed_domains: list[str] | None = None
    show_sources: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Chatbot name is required.")
        return value.strip() if value is not None else value

    @field_validator("primary_color")
    @classmethod
    def validate_color(cls, value):
        if value is not None and not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("Primary color must be a valid six-digit hexadecimal color.")
        return value

    @field_validator("suggested_questions")
    @classmethod
    def validate_questions(cls, value):
        if value is None:
            return value
        if len(value) > 5:
            raise ValueError("A maximum of five suggested questions is allowed.")
        cleaned = []
        for item in value:
            item = item.strip()
            if not item:
                continue
            if len(item) > 150:
                raise ValueError("Suggested questions must be 150 characters or fewer.")
            if item.lower() in {existing.lower() for existing in cleaned}:
                continue
            cleaned.append(item)
        return cleaned

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, value):
        if value is None:
            return value
        if len(value) > 10:
            raise ValueError("A maximum of ten allowed origins is allowed.")
        normalized = []
        for item in value:
            origin = normalize_origin(item)
            if origin not in normalized:
                normalized.append(origin)
        return normalized


class ChatbotResponse(BaseModel):
    id: uuid.UUID
    public_id: str
    name: str
    description: str
    welcome_message: str
    placeholder: str
    primary_color: str
    position: str
    launcher_label: str
    suggested_questions: list[str]
    allowed_domains: list[str]
    is_active: bool
    show_sources: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatbotActivate(BaseModel):
    acknowledge_public_documents: bool
    acknowledge_external_processing: bool


class ChatbotRotate(BaseModel):
    confirm: bool


class PublicChatbotResponse(BaseModel):
    public_id: str
    name: str
    description: str
    welcome_message: str
    placeholder: str
    primary_color: str
    position: str
    launcher_label: str
    suggested_questions: list[str]
    show_sources: bool
