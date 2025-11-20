"""Pages API endpoints."""
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.page import Page
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.page import PageCreate, PageResponse, PageUpdate

router = APIRouter()


def check_workspace_access(
    workspace_id: UUID,
    user_id: UUID,
    db: Session,
) -> Workspace:
    """Check if user has access to workspace.

    Args:
        workspace_id: Workspace ID
        user_id: User ID
        db: Database session

    Returns:
        Workspace if user has access

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
    is_owner = workspace.owner_id == user_id
    is_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
        is not None
    )

    if not (is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return workspace


@router.get("", response_model=List[PageResponse])
def get_pages(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get all pages in a workspace.

    Args:
        workspace_id: Workspace ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of pages
    """
    check_workspace_access(workspace_id, current_user.id, db)

    pages = (
        db.query(Page)
        .filter(Page.workspace_id == workspace_id)
        .order_by(Page.updated_at.desc())
        .all()
    )

    return pages


@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create_page(
    workspace_id: UUID,
    page_data: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new page.

    Args:
        workspace_id: Workspace ID
        page_data: Page creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created page
    """
    check_workspace_access(workspace_id, current_user.id, db)

    new_page = Page(
        workspace_id=workspace_id,
        title=page_data.title,
        tiptap_content=page_data.tiptap_content or {},
        last_edited_by=current_user.id,
    )

    db.add(new_page)
    db.commit()
    db.refresh(new_page)

    return new_page


@router.get("/{page_id}", response_model=PageResponse)
def get_page(
    workspace_id: UUID,
    page_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get page by ID.

    Args:
        workspace_id: Workspace ID
        page_id: Page ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Page details
    """
    check_workspace_access(workspace_id, current_user.id, db)

    page = (
        db.query(Page)
        .filter(Page.id == page_id, Page.workspace_id == workspace_id)
        .first()
    )

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    return page


@router.patch("/{page_id}", response_model=PageResponse)
def update_page(
    workspace_id: UUID,
    page_id: UUID,
    page_data: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update page.

    Args:
        workspace_id: Workspace ID
        page_id: Page ID
        page_data: Page update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated page
    """
    check_workspace_access(workspace_id, current_user.id, db)

    page = (
        db.query(Page)
        .filter(Page.id == page_id, Page.workspace_id == workspace_id)
        .first()
    )

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Update fields
    if page_data.title is not None:
        page.title = page_data.title
    if page_data.tiptap_content is not None:
        page.tiptap_content = page_data.tiptap_content
    if page_data.status is not None:
        page.status = page_data.status
    if page_data.tags is not None:
        page.tags = page_data.tags

    page.last_edited_by = current_user.id

    db.commit()
    db.refresh(page)

    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    workspace_id: UUID,
    page_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete page.

    Args:
        workspace_id: Workspace ID
        page_id: Page ID
        db: Database session
        current_user: Current authenticated user
    """
    check_workspace_access(workspace_id, current_user.id, db)

    page = (
        db.query(Page)
        .filter(Page.id == page_id, Page.workspace_id == workspace_id)
        .first()
    )

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    db.delete(page)
    db.commit()
