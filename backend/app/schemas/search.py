"""Search schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query schema."""

    query: str = Field(..., min_length=1, description="Search query string")
    content_types: Optional[List[str]] = Field(
        None, description="Filter by content types (page, chat_message, file)"
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchResultItem(BaseModel):
    """Single search result item."""

    id: UUID = Field(..., description="Search index ID")
    content_type: str = Field(..., description="Type of content (page, chat_message, file)")
    content_id: UUID = Field(..., description="ID of the actual content")
    title: str = Field(..., description="Title of the content")
    description: Optional[str] = Field(None, description="Description or summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    url: Optional[str] = Field(None, description="URL to access the content")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchResponse(BaseModel):
    """Search response schema."""

    results: List[SearchResultItem] = Field(default_factory=list, description="Search results")
    total: int = Field(..., description="Total number of results")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    query: str = Field(..., description="Search query used")


class SearchHistoryItem(BaseModel):
    """Search history item schema."""

    id: UUID = Field(..., description="History entry ID")
    query: str = Field(..., description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters applied")
    results_count: Dict[str, Any] = Field(default_factory=dict, description="Results count")
    clicked_result_id: Optional[UUID] = Field(None, description="ID of clicked result")
    created_at: datetime = Field(..., description="Search timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchHistoryResponse(BaseModel):
    """Search history response schema."""

    history: List[SearchHistoryItem] = Field(default_factory=list, description="Search history")
    total: int = Field(..., description="Total number of history entries")


class IndexContentRequest(BaseModel):
    """Request to index specific content."""

    content_type: str = Field(..., description="Type of content to index")
    content_id: UUID = Field(..., description="ID of content to index")


class IndexContentResponse(BaseModel):
    """Response after indexing content."""

    success: bool = Field(..., description="Whether indexing was successful")
    message: str = Field(..., description="Status message")
    index_id: Optional[UUID] = Field(None, description="Created index ID")
