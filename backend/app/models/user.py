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
    subscription_histories = relationship(
        "SubscriptionHistory",
        back_populates="user",
        order_by="SubscriptionHistory.created_at.desc()",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User {self.email}>"

    # Subscription management methods

    def is_pro(self) -> bool:
        """Check if user has pro subscription."""
        return self.subscription_plan == "pro"

    def is_free(self) -> bool:
        """Check if user is on free plan."""
        return self.subscription_plan == "free"

    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription."""
        if self.subscription_plan == "free":
            return True
        if self.subscription_expires_at:
            return self.subscription_expires_at > datetime.utcnow()
        return True

    def has_chats_remaining(self) -> bool:
        """Check if user has AI chats remaining."""
        return self.ai_chats_left > 0

    def can_use_ai_chat(self) -> bool:
        """Check if user can use AI chat (has active subscription and chats remaining)."""
        return self.has_active_subscription() and self.has_chats_remaining()

    def decrement_chat_quota(self, amount: int = 1) -> bool:
        """
        Decrement AI chat quota.

        Args:
            amount: Number of chats to decrement

        Returns:
            True if successful, False if insufficient quota
        """
        if self.ai_chats_left >= amount:
            self.ai_chats_left -= amount
            return True
        return False

    def reset_chat_quota(self) -> None:
        """Reset AI chat quota to total."""
        self.ai_chats_left = self.ai_chats_total

    def get_quota_percentage(self) -> float:
        """Get percentage of quota remaining."""
        if self.ai_chats_total == 0:
            return 0.0
        return (self.ai_chats_left / self.ai_chats_total) * 100

    def is_quota_low(self, threshold: float = 20.0) -> bool:
        """
        Check if quota is running low.

        Args:
            threshold: Percentage threshold (default 20%)

        Returns:
            True if quota is below threshold
        """
        return self.get_quota_percentage() < threshold

    def days_until_expiration(self) -> int | None:
        """
        Calculate days until subscription expiration.

        Returns:
            Number of days, or None if no expiration date
        """
        if not self.subscription_expires_at:
            return None
        remaining = (self.subscription_expires_at - datetime.utcnow()).days
        return max(0, remaining)
