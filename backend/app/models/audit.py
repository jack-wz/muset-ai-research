"""Audit log model for security and compliance tracking."""
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class AuditLog(Base, BaseMixin):
    """Audit log model for tracking user actions and system events."""

    __tablename__ = "audit_logs"

    # Actor (user who performed the action)
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User ID who performed the action",
    )

    # Workspace context (optional)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Workspace ID if action was workspace-scoped",
    )

    # Entity information
    entity_type = Column(
        String,
        nullable=False,
        index=True,
        comment="Type of entity: page, file, model, skill, workspace, user, etc.",
    )

    entity_id = Column(
        String,
        nullable=False,
        index=True,
        comment="ID of the entity being acted upon",
    )

    # Action type
    action = Column(
        String,
        nullable=False,
        index=True,
        comment="Action: create, update, delete, import, export, activate, deactivate",
    )

    # Action details
    payload = Column(
        JSONB,
        nullable=False,
        default={},
        comment="Detailed action payload",
    )

    # Request metadata
    ip_address = Column(
        String,
        nullable=True,
        comment="IP address of the request",
    )

    user_agent = Column(
        String,
        nullable=True,
        comment="User agent string",
    )

    # Additional metadata
    meta = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional metadata",
    )

    # Result of the action
    status = Column(
        String,
        default="success",
        nullable=False,
        comment="Status: success, failed, partial",
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if action failed",
    )

    # Relationships
    actor = relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])
    workspace = relationship("Workspace", back_populates="audit_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id}>"

    def is_successful(self) -> bool:
        """Check if action was successful."""
        return self.status == "success"

    def is_failed(self) -> bool:
        """Check if action failed."""
        return self.status == "failed"

    def get_actor_name(self) -> str:
        """Get actor name if available."""
        if self.actor:
            return self.actor.name
        return "System"

    @classmethod
    def log_action(
        cls,
        actor_id: str | None,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
        workspace_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> "AuditLog":
        """
        Create an audit log entry.

        Args:
            actor_id: User ID who performed the action
            entity_type: Type of entity
            entity_id: ID of entity
            action: Action type
            payload: Action details
            workspace_id: Optional workspace ID
            ip_address: Optional IP address
            user_agent: Optional user agent
            status: Action status
            error_message: Optional error message

        Returns:
            Created audit log entry
        """
        return cls(
            actor_id=actor_id,
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message,
        )
