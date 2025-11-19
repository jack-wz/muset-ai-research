"""Notification API endpoints."""
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.notification import (
    MarkAsReadRequest,
    NotificationCreate,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService
from app.services.websocket_manager import connection_manager

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    read: Optional[bool] = Query(None, description="Filter by read status"),
    type: Optional[str] = Query(None, description="Filter by notification type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user notifications.

    Args:
        read: Filter by read status
        type: Filter by notification type
        limit: Maximum number of results
        offset: Pagination offset
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of notifications
    """
    service = NotificationService(db)

    # Get notifications
    notifications = await service.get_notifications(
        user_id=current_user.id,
        read=read,
        type=type,
        limit=limit,
        offset=offset,
    )

    # Get unread count
    unread_count = await service.get_unread_count(current_user.id)

    return {
        "notifications": notifications,
        "total": len(notifications),
        "unread_count": unread_count,
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get count of unread notifications.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Unread count
    """
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)

    return {"count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark notification as read.

    Args:
        notification_id: Notification ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated notification

    Raises:
        HTTPException: If notification not found
    """
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id, current_user.id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    await db.commit()
    return notification


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark all notifications as read.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success response with count
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.id)

    await db.commit()

    return {
        "success": True,
        "message": f"Marked {count} notifications as read",
        "count": count,
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete notification.

    Args:
        notification_id: Notification ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If notification not found
    """
    service = NotificationService(db)
    deleted = await service.delete_notification(notification_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    await db.commit()

    return {
        "success": True,
        "message": "Notification deleted successfully",
    }


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user notification preferences.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Notification preferences
    """
    service = NotificationService(db)
    prefs = await service.get_user_preferences(current_user.id)

    if not prefs:
        # Create default preferences
        prefs = await service.create_or_update_preferences(user_id=current_user.id)
        await db.commit()

    return prefs


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update notification preferences.

    Args:
        preferences: Preference updates
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated preferences
    """
    service = NotificationService(db)

    prefs = await service.create_or_update_preferences(
        user_id=current_user.id,
        email_enabled=preferences.email_enabled,
        in_app_enabled=preferences.in_app_enabled,
        desktop_enabled=preferences.desktop_enabled,
        type_preferences=preferences.type_preferences,
        quiet_hours_enabled=preferences.quiet_hours_enabled,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
    )

    await db.commit()
    return prefs


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
) -> None:
    """
    WebSocket endpoint for real-time notifications.

    Args:
        websocket: WebSocket connection
        token: Authentication token
    """
    # TODO: Validate token and get user_id
    # For now, using placeholder
    user_id = "test-user-id"

    await connection_manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
