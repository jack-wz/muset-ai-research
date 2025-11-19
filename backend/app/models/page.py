"""Page model."""
from typing import Any

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import ArrayType, JSONType, UUIDType
from app.models.mixins import BaseMixin, WorkspaceMixin


class Page(Base, BaseMixin, WorkspaceMixin):
    """Page/Document model."""

    __tablename__ = "pages"

    workspace_id = Column(
        UUIDType,
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    title = Column(String, nullable=False)
    slug = Column(String, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft, review, published
    tags = Column(ArrayType(String), default=[], nullable=False)

    # Content
    tiptap_content = Column(JSONType, nullable=False, default={})
    word_count = Column(Integer, default=0, nullable=False)

    # Links and references
    linked_plan_id = Column(UUIDType, nullable=True)
    linked_files = Column(ArrayType(String), default=[], nullable=False)
    linked_memories = Column(ArrayType(String), default=[], nullable=False)

    # Outline and AI edits
    outline = Column(JSONType, default=[], nullable=False)
    ai_edited_sections = Column(JSONType, default=[], nullable=False)

    # Metadata
    last_edited_by = Column(UUIDType, nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="pages")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Page {self.title}>"
