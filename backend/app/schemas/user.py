"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """User creation schema."""

    password: Optional[str] = None
    provider: str = "google"


class UserUpdate(BaseModel):
    """User update schema."""

    name: Optional[str] = None
    avatar: Optional[str] = None
    settings: Optional[dict] = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    avatar: Optional[str] = None
    provider: str
    subscription_plan: str
    ai_chats_left: int
    ai_chats_total: int
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
