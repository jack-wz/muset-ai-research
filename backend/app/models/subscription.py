"""Subscription and billing models."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class SubscriptionHistory(Base, BaseMixin):
    """Subscription history model for tracking subscription changes."""

    __tablename__ = "subscription_histories"

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID",
    )

    # Previous subscription details
    previous_plan = Column(
        String,
        nullable=True,
        comment="Previous subscription plan",
    )

    # New subscription details
    new_plan = Column(
        String,
        nullable=False,
        comment="New subscription plan: free, pro",
    )

    # Change type
    change_type = Column(
        String,
        nullable=False,
        index=True,
        comment="Change type: upgrade, downgrade, renewal, cancellation, expiration",
    )

    # Pricing information
    amount_paid = Column(
        String,
        nullable=True,
        comment="Amount paid (stored as string to avoid floating point issues)",
    )

    currency = Column(
        String,
        default="USD",
        nullable=False,
        comment="Currency code",
    )

    # Payment details
    payment_method = Column(
        String,
        nullable=True,
        comment="Payment method used",
    )

    transaction_id = Column(
        String,
        nullable=True,
        index=True,
        comment="External payment transaction ID",
    )

    # Subscription period
    starts_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Subscription start date",
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Subscription expiration date",
    )

    # Quota changes
    previous_ai_chats_total = Column(
        Integer,
        nullable=True,
        comment="Previous AI chat quota",
    )

    new_ai_chats_total = Column(
        Integer,
        nullable=False,
        comment="New AI chat quota",
    )

    # Additional details
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes about this change",
    )

    subscription_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        default={},
        comment="Additional metadata",
    )

    # Status
    status = Column(
        String,
        default="active",
        nullable=False,
        comment="Status: active, cancelled, expired, pending",
    )

    # Cancellation info
    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cancellation date",
    )

    cancellation_reason = Column(
        Text,
        nullable=True,
        comment="Reason for cancellation",
    )

    # Relationships
    user = relationship("User", back_populates="subscription_histories")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SubscriptionHistory {self.change_type}: {self.previous_plan} → {self.new_plan}>"

    def is_active(self) -> bool:
        """Check if subscription is active."""
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return self.status == "expired"

    def is_cancelled(self) -> bool:
        """Check if subscription was cancelled."""
        return self.status == "cancelled" or self.cancelled_at is not None

    def days_remaining(self) -> int | None:
        """Calculate days remaining in subscription."""
        if not self.expires_at:
            return None
        remaining = (self.expires_at - datetime.utcnow()).days
        return max(0, remaining)

    def is_upgrade(self) -> bool:
        """Check if this was an upgrade."""
        return self.change_type == "upgrade"

    def is_downgrade(self) -> bool:
        """Check if this was a downgrade."""
        return self.change_type == "downgrade"

    @classmethod
    def create_subscription_change(
        cls,
        user_id: str,
        new_plan: str,
        change_type: str,
        new_ai_chats_total: int,
        starts_at: datetime,
        expires_at: datetime | None = None,
        previous_plan: str | None = None,
        previous_ai_chats_total: int | None = None,
        amount_paid: str | None = None,
        payment_method: str | None = None,
        transaction_id: str | None = None,
        notes: str | None = None,
    ) -> "SubscriptionHistory":
        """
        Create a subscription history entry.

        Args:
            user_id: User ID
            new_plan: New subscription plan
            change_type: Type of change
            new_ai_chats_total: New AI chat quota
            starts_at: Subscription start date
            expires_at: Optional expiration date
            previous_plan: Previous plan
            previous_ai_chats_total: Previous quota
            amount_paid: Amount paid
            payment_method: Payment method
            transaction_id: Transaction ID
            notes: Additional notes

        Returns:
            Created subscription history entry
        """
        return cls(
            user_id=user_id,
            previous_plan=previous_plan,
            new_plan=new_plan,
            change_type=change_type,
            previous_ai_chats_total=previous_ai_chats_total,
            new_ai_chats_total=new_ai_chats_total,
            starts_at=starts_at,
            expires_at=expires_at,
            amount_paid=amount_paid,
            payment_method=payment_method,
            transaction_id=transaction_id,
            notes=notes,
        )
