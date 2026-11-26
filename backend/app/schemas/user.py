# Pydantic schemas for user-related requests and responses.

import uuid
from pydantic import BaseModel, field_validator


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Only the user's display name can be changed in this phase."""
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Full name must be 100 characters or fewer.")
        return v
