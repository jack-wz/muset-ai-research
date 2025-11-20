"""Page schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PageBase(BaseModel):
    """Base page schema."""

    title: str = Field(..., min_length=1, max_length=255)
    tiptap_content: Optional[Dict[str, Any]] = None
    status: Optional[str] = "draft"
    tags: Optional[List[str]] = None


class PageCreate(PageBase):
    """Page creation schema."""

    pass


class PageUpdate(BaseModel):
    """Page update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    tiptap_content: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class PageResponse(PageBase):
    """Page response schema."""

    id: UUID
    workspace_id: UUID
    slug: Optional[str] = None
    summary: Optional[str] = None
    cover_image: Optional[str] = None
    word_count: int = 0
    linked_plan_id: Optional[UUID] = None
    linked_files: List[str] = Field(default_factory=list)
    linked_memories: List[str] = Field(default_factory=list)
    outline: List[Any] = Field(default_factory=list)
    ai_edited_sections: List[Any] = Field(default_factory=list)
    last_edited_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
