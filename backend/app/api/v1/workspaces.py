"""Workspace API endpoints."""
from datetime import datetime
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter()


@router.get("", response_model=List[WorkspaceResponse])
def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all workspaces for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of workspaces
    """
    # Get workspaces owned by user
    owned_workspaces = (
        db.query(Workspace)
        .filter(Workspace.owner_id == current_user.id)
        .all()
    )

    # Get workspaces where user is a member
    member_workspaces = (
        db.query(Workspace)
        .join(WorkspaceMember)
        .filter(WorkspaceMember.user_id == current_user.id)
        .filter(Workspace.owner_id != current_user.id)
        .all()
    )

    return owned_workspaces + member_workspaces


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new workspace.

    Args:
        workspace_data: Workspace creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created workspace
    """
    new_workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=current_user.id,
        last_accessed_at=datetime.utcnow(),
    )

    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)

    return new_workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get workspace by ID.

    Args:
        workspace_id: Workspace ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Workspace details

    Raises:
        HTTPException: If workspace not found or user doesn't have access
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # Check if user has access
    is_owner = workspace.owner_id == current_user.id
    is_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
        is not None
    )

    if not (is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update last accessed time
    workspace.last_accessed_at = datetime.utcnow()
    db.commit()

    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: UUID,
    workspace_data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update workspace.

    Args:
        workspace_id: Workspace ID
        workspace_data: Workspace update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated workspace

    Raises:
        HTTPException: If workspace not found or user is not owner
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owner can update",
        )

    # Update fields
    if workspace_data.name is not None:
        workspace.name = workspace_data.name
    if workspace_data.description is not None:
        workspace.description = workspace_data.description
    if workspace_data.icon is not None:
        workspace.icon = workspace_data.icon

    db.commit()
    db.refresh(workspace)

    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete workspace.

    Args:
        workspace_id: Workspace ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If workspace not found or user is not owner
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owner can delete",
        )

    db.delete(workspace)
    db.commit()
