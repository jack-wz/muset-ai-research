"""Notification models for real-time notifications."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class Notification(Base, BaseMixin):
    """
    Notification model for user notifications.

    Supports various notification types:
    - info: General information
    - success: Success messages
    - warning: Warning messages
    - error: Error messages
    - mention: User mentions
    - task_complete: Task completion
    - quota_low: Quota warnings
    - subscription_expire: Subscription expiration warnings
    """

    __tablename__ = "notifications"

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User receiving the notification",
    )

    # Workspace context (optional)
    workspace_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Related workspace (if applicable)",
    )

    # Notification details
    type = Column(
        String,
        nullable=False,
        index=True,
        comment="Notification type: info, success, warning, error, mention, task_complete, quota_low, subscription_expire",
    )

    title = Column(
        String,
        nullable=False,
        comment="Notification title",
    )

    message = Column(
        Text,
        nullable=False,
        comment="Notification message content",
    )

    # Additional data
    data = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional notification data",
    )

    # Action link
    action_url = Column(
        String,
        nullable=True,
        comment="URL to navigate when notification is clicked",
    )

    action_label = Column(
        String,
        nullable=True,
        comment="Label for action button",
    )

    # Status
    read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether notification has been read",
    )

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification was read",
    )

    # Delivery
    delivered = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether notification was delivered (for WebSocket)",
    )

    delivered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification was delivered",
    )

    # Email notification
    email_sent = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email notification was sent",
    )

    email_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When email notification was sent",
    )

    # Expiration
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When notification expires and should be auto-archived",
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Notification {self.type}: {self.title}>"

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.read = True
        self.read_at = datetime.utcnow()

    def mark_as_delivered(self) -> None:
        """Mark notification as delivered."""
        self.delivered = True
        self.delivered_at = datetime.utcnow()

    def mark_email_sent(self) -> None:
        """Mark email as sent."""
        self.email_sent = True
        self.email_sent_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()

    __table_args__ = (
        # Index for fetching user's unread notifications
        Index(
            "ix_notifications_user_read",
            "user_id",
            "read",
            "created_at",
        ),
        # Index for fetching notifications by type
        Index(
            "ix_notifications_user_type",
            "user_id",
            "type",
            "created_at",
        ),
        # Index for fetching workspace notifications
        Index(
            "ix_notifications_workspace",
            "workspace_id",
            "created_at",
        ),
    )


class NotificationPreference(Base, BaseMixin):
    """User notification preferences."""

    __tablename__ = "notification_preferences"

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID",
    )

    # Channel preferences
    email_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Enable email notifications",
    )

    in_app_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Enable in-app notifications",
    )

    desktop_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Enable desktop push notifications",
    )

    # Notification type preferences
    type_preferences = Column(
        JSONB,
        nullable=False,
        default={
            "info": {"email": False, "in_app": True},
            "success": {"email": False, "in_app": True},
            "warning": {"email": True, "in_app": True},
            "error": {"email": True, "in_app": True},
            "mention": {"email": True, "in_app": True},
            "task_complete": {"email": True, "in_app": True},
            "quota_low": {"email": True, "in_app": True},
            "subscription_expire": {"email": True, "in_app": True},
        },
        comment="Per-type notification preferences",
    )

    # Quiet hours
    quiet_hours_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Enable quiet hours",
    )

    quiet_hours_start = Column(
        String,
        nullable=True,
        comment="Quiet hours start time (HH:MM format)",
    )

    quiet_hours_end = Column(
        String,
        nullable=True,
        comment="Quiet hours end time (HH:MM format)",
    )

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self) -> str:
        """String representation."""
        return f"<NotificationPreference user={self.user_id}>"

    def should_send_email(self, notification_type: str) -> bool:
        """Check if email should be sent for notification type."""
        if not self.email_enabled:
            return False

        type_prefs = self.type_preferences.get(notification_type, {})
        return type_prefs.get("email", False)

    def should_send_in_app(self, notification_type: str) -> bool:
        """Check if in-app notification should be sent."""
        if not self.in_app_enabled:
            return False

        type_prefs = self.type_preferences.get(notification_type, {})
        return type_prefs.get("in_app", True)

    def is_in_quiet_hours(self) -> bool:
        """Check if current time is in quiet hours."""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        from datetime import time

        now = datetime.utcnow().time()
        start = time.fromisoformat(self.quiet_hours_start)
        end = time.fromisoformat(self.quiet_hours_end)

        if start < end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end
