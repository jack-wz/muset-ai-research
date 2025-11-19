"""Workspace and related models."""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class Workspace(Base, BaseMixin):
    """Workspace model."""

    __tablename__ = "workspaces"

    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    active_project_id = Column(UUID(as_uuid=True), nullable=True)

    # Statistics stored as JSONB
    stats = Column(
        JSONB,
        nullable=False,
        default={
            "pageCount": 0,
            "totalWords": 0,
            "draftCount": 0,
            "activePlans": 0,
        },
    )

    # Relationships
    owner = relationship("User", back_populates="owned_workspaces", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace")
    pages = relationship("Page", back_populates="workspace")
    writing_plans = relationship("WritingPlan", back_populates="workspace")
    context_files = relationship("ContextFile", back_populates="workspace")
    memories = relationship("Memory", back_populates="workspace")
    chat_sessions = relationship("ChatSession", back_populates="workspace")
    inspiration_boards = relationship("InspirationBoard", back_populates="workspace")
    upload_assets = relationship("UploadAsset", back_populates="workspace")
    audit_logs = relationship("AuditLog", back_populates="workspace")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Workspace {self.name}>"


class WorkspaceMember(Base, BaseMixin):
    """Workspace member model."""

    __tablename__ = "workspace_members"

    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    role = Column(String, default="editor", nullable=False)  # owner, editor, viewer
    joined_at = Column(DateTime(timezone=True), nullable=False)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_members")

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkspaceMember workspace={self.workspace_id} user={self.user_id}>"
