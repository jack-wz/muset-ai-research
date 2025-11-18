"""Authentication schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    password: str
    name: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth request schema."""

    id_token: str


class GoogleAuthResponse(BaseModel):
    """Google OAuth response schema."""

    access_token: str
    token_type: str = "bearer"
    user: dict
