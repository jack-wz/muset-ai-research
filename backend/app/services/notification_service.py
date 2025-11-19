"""Notification service for creating and managing notifications."""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference
from app.models.user import User


class NotificationService:
    """
    Service for managing notifications.

    Handles notification creation, delivery tracking, and user preferences.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize notification service.

        Args:
            session: Database session
        """
        self.session = session
        # WebSocket manager will be injected
        self.websocket_manager = None

    def set_websocket_manager(self, manager: Any) -> None:
        """
        Set WebSocket manager for real-time notifications.

        Args:
            manager: WebSocket manager instance
        """
        self.websocket_manager = manager

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        workspace_id: Optional[UUID] = None,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: User ID to send notification to
            type: Notification type
            title: Notification title
            message: Notification message
            workspace_id: Optional workspace context
            data: Additional notification data
            action_url: Optional action URL
            action_label: Optional action label
            expires_in_days: Optional expiration in days

        Returns:
            Created Notification instance
        """
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create notification
        notification = Notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type=type,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            action_label=action_label,
            expires_at=expires_at,
        )

        self.session.add(notification)
        await self.session.flush()

        # Check user preferences and send
        await self._send_notification(notification)

        return notification

    async def _send_notification(self, notification: Notification) -> None:
        """
        Send notification through appropriate channels based on user preferences.

        Args:
            notification: Notification to send
        """
        # Get user preferences
        prefs = await self.get_user_preferences(notification.user_id)

        # Check if in quiet hours
        if prefs and prefs.is_in_quiet_hours():
            # Don't send during quiet hours
            return

        # Send in-app notification via WebSocket
        if prefs and prefs.should_send_in_app(notification.type):
            await self._send_websocket(notification)

        # Send email notification (if configured)
        if prefs and prefs.should_send_email(notification.type):
            await self._send_email(notification)

    async def _send_websocket(self, notification: Notification) -> None:
        """
        Send notification via WebSocket.

        Args:
            notification: Notification to send
        """
        if not self.websocket_manager:
            return

        # Format notification data
        data = {
            "id": str(notification.id),
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "data": notification.data,
            "action_url": notification.action_url,
            "action_label": notification.action_label,
            "created_at": notification.created_at.isoformat(),
        }

        # Send to user via WebSocket
        try:
            await self.websocket_manager.send_to_user(
                str(notification.user_id),
                {"event": "notification", "data": data},
            )
            notification.mark_as_delivered()
        except Exception as e:
            print(f"Failed to send WebSocket notification: {e}")

    async def _send_email(self, notification: Notification) -> None:
        """
        Send notification via email.

        Args:
            notification: Notification to send
        """
        # TODO: Implement email sending
        # This would integrate with an email service (SendGrid, SES, etc.)
        # For now, just mark as sent
        notification.mark_email_sent()

    async def get_user_preferences(
        self, user_id: UUID
    ) -> Optional[NotificationPreference]:
        """
        Get user notification preferences.

        Args:
            user_id: User ID

        Returns:
            NotificationPreference instance or None
        """
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_preferences(
        self,
        user_id: UUID,
        email_enabled: Optional[bool] = None,
        in_app_enabled: Optional[bool] = None,
        desktop_enabled: Optional[bool] = None,
        type_preferences: Optional[Dict[str, Any]] = None,
        quiet_hours_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
    ) -> NotificationPreference:
        """
        Create or update user notification preferences.

        Args:
            user_id: User ID
            email_enabled: Enable email notifications
            in_app_enabled: Enable in-app notifications
            desktop_enabled: Enable desktop notifications
            type_preferences: Per-type preferences
            quiet_hours_enabled: Enable quiet hours
            quiet_hours_start: Quiet hours start time
            quiet_hours_end: Quiet hours end time

        Returns:
            NotificationPreference instance
        """
        prefs = await self.get_user_preferences(user_id)

        if prefs:
            # Update existing preferences
            if email_enabled is not None:
                prefs.email_enabled = email_enabled
            if in_app_enabled is not None:
                prefs.in_app_enabled = in_app_enabled
            if desktop_enabled is not None:
                prefs.desktop_enabled = desktop_enabled
            if type_preferences is not None:
                prefs.type_preferences = type_preferences
            if quiet_hours_enabled is not None:
                prefs.quiet_hours_enabled = quiet_hours_enabled
            if quiet_hours_start is not None:
                prefs.quiet_hours_start = quiet_hours_start
            if quiet_hours_end is not None:
                prefs.quiet_hours_end = quiet_hours_end
        else:
            # Create new preferences
            prefs = NotificationPreference(
                user_id=user_id,
                email_enabled=email_enabled if email_enabled is not None else True,
                in_app_enabled=in_app_enabled if in_app_enabled is not None else True,
                desktop_enabled=desktop_enabled if desktop_enabled is not None else False,
                type_preferences=type_preferences or {},
                quiet_hours_enabled=quiet_hours_enabled or False,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )
            self.session.add(prefs)

        await self.session.flush()
        return prefs

    async def get_notifications(
        self,
        user_id: UUID,
        read: Optional[bool] = None,
        type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get user notifications.

        Args:
            user_id: User ID
            read: Filter by read status
            type: Filter by notification type
            limit: Maximum number of notifications
            offset: Pagination offset

        Returns:
            List of Notification instances
        """
        stmt = select(Notification).where(Notification.user_id == user_id)

        if read is not None:
            stmt = stmt.where(Notification.read == read)

        if type:
            stmt = stmt.where(Notification.type == type)

        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(
        self, notification_id: UUID, user_id: UUID
    ) -> Optional[Notification]:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)

        Returns:
            Updated Notification or None if not found
        """
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            notification.mark_as_read()
            await self.session.flush()

        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        # Get all unread notifications
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.read == False,
            )
        )
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()

        # Mark as read
        count = 0
        for notification in notifications:
            notification.mark_as_read()
            count += 1

        await self.session.flush()
        return count

    async def delete_notification(
        self, notification_id: UUID, user_id: UUID
    ) -> bool:
        """
        Delete notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)

        Returns:
            True if deleted, False if not found
        """
        stmt = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            await self.session.delete(notification)
            await self.session.flush()
            return True

        return False

    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: User ID

        Returns:
            Number of unread notifications
        """
        from sqlalchemy import func

        stmt = select(func.count()).where(
            and_(
                Notification.user_id == user_id,
                Notification.read == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    # Helper methods for creating common notification types

    async def notify_quota_low(
        self, user_id: UUID, quota_percentage: float
    ) -> Notification:
        """Create quota low notification."""
        return await self.create_notification(
            user_id=user_id,
            type="quota_low",
            title="AI Chat Quota Running Low",
            message=f"You have {quota_percentage:.0f}% of your AI chat quota remaining.",
            action_url="/settings/subscription",
            action_label="Upgrade Plan",
            expires_in_days=7,
        )

    async def notify_subscription_expiring(
        self, user_id: UUID, days_remaining: int
    ) -> Notification:
        """Create subscription expiration notification."""
        return await self.create_notification(
            user_id=user_id,
            type="subscription_expire",
            title="Subscription Expiring Soon",
            message=f"Your subscription will expire in {days_remaining} days.",
            action_url="/settings/subscription",
            action_label="Renew Now",
            expires_in_days=days_remaining,
        )

    async def notify_task_complete(
        self, user_id: UUID, task_name: str, workspace_id: Optional[UUID] = None
    ) -> Notification:
        """Create task completion notification."""
        return await self.create_notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type="task_complete",
            title="Task Completed",
            message=f'Task "{task_name}" has been completed successfully.',
            expires_in_days=3,
        )

    async def notify_mention(
        self,
        user_id: UUID,
        mentioned_by: str,
        location: str,
        workspace_id: Optional[UUID] = None,
    ) -> Notification:
        """Create mention notification."""
        return await self.create_notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type="mention",
            title="You were mentioned",
            message=f"{mentioned_by} mentioned you in {location}.",
            expires_in_days=7,
        )
