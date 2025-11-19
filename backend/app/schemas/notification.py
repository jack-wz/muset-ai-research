"""Notification schemas."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Notification creation schema."""

    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    workspace_id: Optional[UUID] = Field(None, description="Related workspace ID")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional data")
    action_url: Optional[str] = Field(None, description="Action URL")
    action_label: Optional[str] = Field(None, description="Action button label")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: UUID = Field(..., description="Notification ID")
    user_id: UUID = Field(..., description="User ID")
    workspace_id: Optional[UUID] = Field(None, description="Workspace ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Title")
    message: str = Field(..., description="Message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    action_url: Optional[str] = Field(None, description="Action URL")
    action_label: Optional[str] = Field(None, description="Action label")
    read: bool = Field(..., description="Read status")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    delivered: bool = Field(..., description="Delivered status")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    email_sent: bool = Field(..., description="Email sent status")
    email_sent_at: Optional[datetime] = Field(None, description="Email sent timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response schema."""

    notifications: list[NotificationResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total count")
    unread_count: int = Field(..., description="Unread count")


class NotificationPreferenceUpdate(BaseModel):
    """Notification preference update schema."""

    email_enabled: Optional[bool] = Field(None, description="Enable email notifications")
    in_app_enabled: Optional[bool] = Field(None, description="Enable in-app notifications")
    desktop_enabled: Optional[bool] = Field(None, description="Enable desktop notifications")
    type_preferences: Optional[Dict[str, Any]] = Field(None, description="Per-type preferences")
    quiet_hours_enabled: Optional[bool] = Field(None, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")


class NotificationPreferenceResponse(BaseModel):
    """Notification preference response schema."""

    id: UUID = Field(..., description="Preference ID")
    user_id: UUID = Field(..., description="User ID")
    email_enabled: bool = Field(..., description="Email enabled")
    in_app_enabled: bool = Field(..., description="In-app enabled")
    desktop_enabled: bool = Field(..., description="Desktop enabled")
    type_preferences: Dict[str, Any] = Field(default_factory=dict, description="Type preferences")
    quiet_hours_enabled: bool = Field(..., description="Quiet hours enabled")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True


class MarkAsReadRequest(BaseModel):
    """Mark as read request schema."""

    notification_ids: list[UUID] = Field(..., description="Notification IDs to mark as read")


class UnreadCountResponse(BaseModel):
    """Unread count response schema."""

    count: int = Field(..., description="Number of unread notifications")
