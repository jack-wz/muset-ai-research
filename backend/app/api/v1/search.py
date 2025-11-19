"""Search API endpoints."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.file import ContextFile
from app.models.page import Page
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.search import (
    IndexContentRequest,
    IndexContentResponse,
    SearchHistoryResponse,
    SearchQuery,
    SearchResponse,
)
from app.services.search_service import SearchService

router = APIRouter()


async def get_user_workspace(
    workspace_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Workspace:
    """
    Verify user has access to workspace.

    Args:
        workspace_id: Workspace ID
        current_user: Current user
        db: Database session

    Returns:
        Workspace if user has access

    Raises:
        HTTPException: If workspace not found or user doesn't have access
    """
    # Check if user owns the workspace
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # Check if user is owner or member
    if workspace.owner_id != current_user.id:
        # Check membership
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace",
            )

    return workspace


@router.post("/workspaces/{workspace_id}/search", response_model=SearchResponse)
async def search_workspace(
    workspace_id: UUID,
    search_query: SearchQuery,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Perform full-text search in workspace.

    Args:
        workspace_id: Workspace ID
        search_query: Search query parameters
        current_user: Current authenticated user
        db: Database session

    Returns:
        Search results

    Raises:
        HTTPException: If workspace not found or access denied
    """
    # Verify workspace access
    await get_user_workspace(workspace_id, current_user, db)

    # Create search service
    search_service = SearchService(db)

    # Perform search
    results = await search_service.search(
        workspace_id=workspace_id,
        query=search_query.query,
        content_types=search_query.content_types,
        limit=search_query.limit,
        offset=search_query.offset,
    )

    # Save search history
    await search_service.save_search_history(
        user_id=current_user.id,
        workspace_id=workspace_id,
        query=search_query.query,
        filters={"content_types": search_query.content_types},
        results_count=results["total"],
    )

    await db.commit()

    return results


@router.get("/workspaces/{workspace_id}/search/history", response_model=SearchHistoryResponse)
async def get_search_history(
    workspace_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user search history for workspace.

    Args:
        workspace_id: Workspace ID
        limit: Maximum number of history entries
        current_user: Current authenticated user
        db: Database session

    Returns:
        Search history

    Raises:
        HTTPException: If workspace not found or access denied
    """
    # Verify workspace access
    await get_user_workspace(workspace_id, current_user, db)

    # Create search service
    search_service = SearchService(db)

    # Get search history
    history = await search_service.get_search_history(
        user_id=current_user.id,
        workspace_id=workspace_id,
        limit=limit,
    )

    return {
        "history": history,
        "total": len(history),
    }


@router.post("/workspaces/{workspace_id}/index", response_model=IndexContentResponse)
async def index_content(
    workspace_id: UUID,
    request: IndexContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Index specific content for searching.

    Args:
        workspace_id: Workspace ID
        request: Index request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Index response

    Raises:
        HTTPException: If content not found or access denied
    """
    # Verify workspace access
    await get_user_workspace(workspace_id, current_user, db)

    # Create search service
    search_service = SearchService(db)

    # Index based on content type
    index = None

    if request.content_type == "page":
        # Get page
        stmt = select(Page).where(
            Page.id == request.content_id,
            Page.workspace_id == workspace_id,
        )
        result = await db.execute(stmt)
        page = result.scalar_one_or_none()

        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found",
            )

        index = await search_service.index_page(page)

    elif request.content_type == "chat_message":
        # Get chat message and session
        stmt = select(ChatMessage).where(ChatMessage.id == request.content_id)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat message not found",
            )

        # Get session
        stmt = select(ChatSession).where(
            ChatSession.id == message.session_id,
            ChatSession.workspace_id == workspace_id,
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        index = await search_service.index_chat_message(message, session)

    elif request.content_type == "file":
        # Get file
        stmt = select(ContextFile).where(
            ContextFile.id == request.content_id,
            ContextFile.workspace_id == workspace_id,
        )
        result = await db.execute(stmt)
        file = result.scalar_one_or_none()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        index = await search_service.index_file(file)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {request.content_type}",
        )

    await db.commit()

    return {
        "success": True,
        "message": f"Successfully indexed {request.content_type}",
        "index_id": index.id if index else None,
    }


@router.delete("/workspaces/{workspace_id}/index/{content_type}/{content_id}")
async def delete_index(
    workspace_id: UUID,
    content_type: str,
    content_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete search index for content.

    Args:
        workspace_id: Workspace ID
        content_type: Type of content
        content_id: ID of content
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If workspace not found or access denied
    """
    # Verify workspace access
    await get_user_workspace(workspace_id, current_user, db)

    # Create search service
    search_service = SearchService(db)

    # Delete index
    deleted = await search_service.delete_index(content_type, content_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Index not found",
        )

    await db.commit()

    return {
        "success": True,
        "message": "Index deleted successfully",
    }
