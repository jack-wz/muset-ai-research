"""Search index models for full-text search functionality."""
from typing import Any, Optional

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin, WorkspaceMixin


class SearchIndex(Base, BaseMixin, WorkspaceMixin):
    """
    Global search index for all searchable content.

    This model provides unified full-text search across:
    - Pages and documents
    - Chat messages
    - File contents
    - Other searchable entities
    """

    __tablename__ = "search_indexes"

    # Workspace relationship for access control
    workspace_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Content identification
    content_type = Column(
        String,
        nullable=False,
        index=True,
    )  # page, chat_message, file, memory, etc.

    content_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )  # ID of the indexed entity

    # Searchable content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Main searchable content

    # Full-text search vector (PostgreSQL TSVector)
    search_vector = Column(
        TSVECTOR,
        nullable=True,
    )

    # Additional metadata for search results
    search_metadata = Column(
        JSONB,
        default={},
        nullable=False,
    )  # tags, author, file_type, etc.

    # URL/path to the content (for navigation)
    url = Column(String, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SearchIndex {self.content_type}:{self.content_id} - {self.title}>"

    __table_args__ = (
        # Composite index for efficient lookups
        Index(
            "ix_search_indexes_workspace_content",
            "workspace_id",
            "content_type",
        ),
        # Unique constraint to prevent duplicate indexes
        Index(
            "ix_search_indexes_content_unique",
            "content_type",
            "content_id",
            unique=True,
        ),
        # GIN index for full-text search
        Index(
            "ix_search_indexes_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
        # GIN index for metadata JSONB queries
        Index(
            "ix_search_indexes_metadata",
            "search_metadata",
            postgresql_using="gin",
        ),
    )


class SearchHistory(Base, BaseMixin):
    """User search history for analytics and personalization."""

    __tablename__ = "search_histories"

    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    workspace_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Search query
    query = Column(String, nullable=False)

    # Search filters applied
    filters = Column(
        JSONB,
        default={},
        nullable=False,
    )  # content_type, date_range, etc.

    # Results metadata
    results_count = Column(
        JSONB,
        default={"total": 0},
        nullable=False,
    )

    # Clicked result (if any)
    clicked_result_id = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SearchHistory user={self.user_id} query='{self.query}'>"

    __table_args__ = (
        # Index for user search history queries
        Index(
            "ix_search_histories_user_workspace",
            "user_id",
            "workspace_id",
            "created_at",
        ),
    )
