"""Workspace schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WorkspaceBase(BaseModel):
    """Base workspace schema."""

    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    """Workspace creation schema."""

    pass


class WorkspaceUpdate(BaseModel):
    """Workspace update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    active_project_id: Optional[UUID] = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response schema."""

    id: UUID
    owner_id: UUID
    active_project_id: Optional[UUID] = None
    stats: dict
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response schema."""

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    last_active_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
