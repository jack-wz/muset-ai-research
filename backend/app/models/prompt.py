"""Prompt suggestion and inspiration models."""
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin, WorkspaceMixin


class PromptSuggestion(Base, BaseMixin):
    """Prompt suggestion model for inspiration and guidance."""

    __tablename__ = "prompt_suggestions"

    # Category of the suggestion
    category = Column(
        String,
        nullable=False,
        index=True,
        comment="Category: question, theme, angle, community-sample",
    )

    # Prompt text content
    text = Column(Text, nullable=False, comment="Prompt suggestion text")

    # Optional icon for UI display
    icon = Column(String, nullable=True, comment="Icon identifier or emoji")

    # Tags for filtering and categorization
    tags = Column(
        ARRAY(String),
        default=[],
        nullable=False,
        comment="Tags for filtering suggestions",
    )

    # Locale/language for i18n support
    locale = Column(
        String,
        default="en",
        nullable=False,
        index=True,
        comment="Language code (en, zh, etc.)",
    )

    # Required skills (optional, references SkillPackage)
    required_skills = Column(
        ARRAY(String),
        default=[],
        nullable=False,
        comment="Required skill package names",
    )

    # Usage statistics
    usage_count = Column(
        String,
        default="0",
        nullable=False,
        comment="Number of times this suggestion was used",
    )

    # Quality rating (optional, for sorting/filtering)
    rating = Column(
        String,
        nullable=True,
        comment="Average user rating (0-5)",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptSuggestion {self.category}: {self.text[:50]}>"


class InspirationBoard(Base, BaseMixin, WorkspaceMixin):
    """Inspiration board for organizing ideas and suggestions."""

    __tablename__ = "inspiration_boards"

    # Workspace relationship
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Board title
    title = Column(
        String,
        nullable=False,
        comment="Inspiration board title",
    )

    # Description (optional)
    description = Column(
        Text,
        nullable=True,
        comment="Board description",
    )

    # Related page IDs
    related_page_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        nullable=False,
        comment="IDs of related pages",
    )

    # Suggestion IDs (references to PromptSuggestion)
    suggestions = Column(
        ARRAY(UUID(as_uuid=True)),
        default=[],
        nullable=False,
        comment="IDs of included prompt suggestions",
    )

    # Community sample IDs (references to community examples)
    community_sample_ids = Column(
        ARRAY(String),
        default=[],
        nullable=False,
        comment="IDs of community examples",
    )

    # Custom notes
    notes = Column(
        Text,
        nullable=True,
        comment="User's custom notes for this board",
    )

    # Board status
    status = Column(
        String,
        default="active",
        nullable=False,
        comment="Board status: active, archived",
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="inspiration_boards")

    def __repr__(self) -> str:
        """String representation."""
        return f"<InspirationBoard {self.title}>"
