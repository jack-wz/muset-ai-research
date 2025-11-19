"""User model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class User(Base, BaseMixin):
    """User model."""

    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    provider = Column(String, default="google", nullable=False)
    hashed_password = Column(String, nullable=True)  # For email/password auth

    # Subscription info
    subscription_plan = Column(String, default="free", nullable=False)
    ai_chats_left = Column(Integer, default=50, nullable=False)
    ai_chats_total = Column(Integer, default=50, nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Settings stored as JSONB
    settings = Column(
        JSONB,
        nullable=False,
        default={
            "language": "en",
            "theme": "system",
            "notificationChannels": {
                "email": True,
                "inApp": True,
                "desktop": False,
            },
        },
    )

    # Relationships
    owned_workspaces = relationship(
        "Workspace",
        back_populates="owner",
        foreign_keys="Workspace.owner_id",
    )
    workspace_members = relationship("WorkspaceMember", back_populates="user")
    uploads = relationship("UploadAsset", back_populates="uploader")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User {self.email}>"
