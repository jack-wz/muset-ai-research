"""Chat session and message models."""
from typing import Any

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import ArrayType, JSONType, UUIDType
from app.models.mixins import BaseMixin, WorkspaceMixin


class ChatSession(Base, BaseMixin, WorkspaceMixin):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    workspace_id = Column(
        UUIDType,
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    page_id = Column(UUIDType, nullable=True)
    title = Column(String, nullable=False)
    mode = Column(String, default="chat", nullable=False)  # chat, agent-run
    language = Column(String, default="en", nullable=False)
    system_prompt = Column(Text, nullable=True)
    active_model_id = Column(String, nullable=False)
    active_skills = Column(ArrayType(String), default=[], nullable=False)

    # Message IDs
    message_ids = Column(ArrayType(String), default=[], nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ChatSession {self.title}>"


class ChatMessage(Base, BaseMixin):
    """Chat message model."""

    __tablename__ = "chat_messages"

    session_id = Column(
        UUIDType,
        ForeignKey("chat_sessions.id"),
        nullable=False,
        index=True,
    )
    role = Column(String, nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)

    # Streaming state
    streaming_state = Column(JSONType, nullable=True)

    # Attachments and references
    attachments = Column(JSONType, default=[], nullable=False)
    referenced_files = Column(ArrayType(String), default=[], nullable=False)
    referenced_memories = Column(ArrayType(String), default=[], nullable=False)

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    meta = Column(JSONType, default={}, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"
