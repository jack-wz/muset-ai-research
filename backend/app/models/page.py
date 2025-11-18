"""Page model."""
from typing import Any

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin, WorkspaceMixin


class Page(Base, BaseMixin, WorkspaceMixin):
    """Page/Document model."""

    __tablename__ = "pages"

    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    title = Column(String, nullable=False)
    slug = Column(String, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft, review, published
    tags = Column(ARRAY(String), default=[], nullable=False)

    # Content
    tiptap_content = Column(JSONB, nullable=False, default={})
    word_count = Column(Integer, default=0, nullable=False)

    # Links and references
    linked_plan_id = Column(UUID(as_uuid=True), nullable=True)
    linked_files = Column(ARRAY(String), default=[], nullable=False)
    linked_memories = Column(ARRAY(String), default=[], nullable=False)

    # Outline and AI edits
    outline = Column(JSONB, default=[], nullable=False)
    ai_edited_sections = Column(JSONB, default=[], nullable=False)

    # Metadata
    last_edited_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="pages")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Page {self.title}>"
