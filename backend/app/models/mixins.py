"""SQLAlchemy model mixins for common fields."""
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func


class UUIDMixin:
    """Mixin for UUID primary key."""

    __allow_unmapped__ = True

    @declared_attr
    def id(cls):  # type: ignore
        """UUID primary key."""
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    __allow_unmapped__ = True

    @declared_attr
    def created_at(cls):  # type: ignore
        """Record creation timestamp."""
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):  # type: ignore
        """Record last update timestamp."""
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class BaseMixin(UUIDMixin, TimestampMixin):
    """Base mixin combining UUID and timestamp fields."""

    __allow_unmapped__ = True


class WorkspaceMixin:
    """Mixin for models that belong to a workspace."""

    __allow_unmapped__ = True

    @declared_attr
    def workspace_id(cls):  # type: ignore
        """Workspace foreign key."""
        return Column(
            UUID(as_uuid=True),
            nullable=False,
            index=True,
        )
