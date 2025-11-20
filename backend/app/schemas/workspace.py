"""Workspace schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    """Base workspace schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    """Workspace creation schema."""

    pass


class WorkspaceUpdate(BaseModel):
    """Workspace update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response schema."""

    id: UUID
    owner_id: UUID
    last_accessed_at: Optional[datetime] = None
    active_project_id: Optional[UUID] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
