"""Memory model for long-term storage."""
from typing import Any

from sqlalchemy import Column, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import ArrayType, JSONType, UUIDType
from app.models.mixins import BaseMixin, WorkspaceMixin


class Memory(Base, BaseMixin, WorkspaceMixin):
    """Memory model for long-term storage."""

    __tablename__ = "memories"

    workspace_id = Column(
        UUIDType,
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    type = Column(
        String,
        nullable=False,
    )  # style, glossary, preference, knowledge
    title = Column(String, nullable=False)

    # Payload stores type-specific data as JSON/JSONB
    # For style: {samples, toneDescriptors, pacing, sentenceLength, doAndDont}
    # For glossary: {term, definition, usageExamples, locale}
    # For knowledge: {topic, summary, citations}
    # For preference: {key, value, context}
    payload = Column(JSONType, nullable=False)

    # Vector embedding reference
    embedding_id = Column(String, nullable=True)

    # Metadata
    tags = Column(ArrayType(String), default=[], nullable=False)
    importance_score = Column(Float, default=0.5, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="memories")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Memory {self.type}: {self.title}>"
