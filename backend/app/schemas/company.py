# Pydantic schemas for company-related requests and responses.

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyUpdateRequest(BaseModel):
    """Only the company name can be changed after registration."""
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty.")
        if len(v) > 150:
            raise ValueError("Company name must be 150 characters or fewer.")
        return v
