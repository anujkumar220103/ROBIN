# Pydantic schemas for authentication requests (register, login) and responses.

import uuid
from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    company_name: str
    full_name: str
    email: EmailStr
    password: str

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name cannot be empty.")
        if len(v) > 150:
            raise ValueError("Company name must be 150 characters or fewer.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Full name must be 100 characters or fewer.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Minimum 12 characters — strong passphrase encourage karte hain.
        # Arbitrary complexity rules nahi lagate jo passphrases restrict karti hain.
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters.")
        if len(v) > 128:
            raise ValueError("Password must be 128 characters or fewer.")
        return v


class RegisterResponse(BaseModel):
    message: str
    user: "RegisteredUserInfo"
    company: "RegisteredCompanyInfo"


class RegisteredUserInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class RegisteredCompanyInfo(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    user: RegisteredUserInfo
    company: RegisteredCompanyInfo
    csrf_token: str  # Returned in body so cross-origin JS can read it (cookie unreadable across origins)


# ---------------------------------------------------------------------------
# Me (current user session)
# ---------------------------------------------------------------------------

class MeResponse(BaseModel):
    user: RegisteredUserInfo
    company: RegisteredCompanyInfo
    csrf_token: str  # Returned in body so session restore after page refresh also gets the token


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutResponse(BaseModel):
    message: str
