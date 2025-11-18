"""Page schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PageBase(BaseModel):
    """Base page schema."""

    title: str
    summary: Optional[str] = None
    status: str = "draft"
    tags: list[str] = []


class PageCreate(PageBase):
    """Page creation schema."""

    workspace_id: UUID
    tiptap_content: dict = {}


class PageUpdate(BaseModel):
    """Page update schema."""

    title: Optional[str] = None
    summary: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None
    tiptap_content: Optional[dict] = None
    outline: Optional[list[dict]] = None


class PageResponse(PageBase):
    """Page response schema."""

    id: UUID
    workspace_id: UUID
    slug: Optional[str] = None
    cover_image: Optional[str] = None
    tiptap_content: dict
    word_count: int
    linked_plan_id: Optional[UUID] = None
    linked_files: list[str]
    linked_memories: list[str]
    outline: list[dict]
    ai_edited_sections: list[dict]
    last_edited_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
