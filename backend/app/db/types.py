"""Database types for cross-database compatibility."""
import json
import os
import uuid
from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator


class JSONType(TypeDecorator):
    """
    Cross-database JSON type.

    Uses JSONB for PostgreSQL for better performance,
    and JSON for other databases (including SQLite for testing).
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect) -> Any:
        """Process values before binding."""
        return value

    def process_result_value(self, value: Any, dialect) -> Any:
        """Process values from the database."""
        return value


class ArrayType(TypeDecorator):
    """
    Cross-database ARRAY type.

    Uses ARRAY for PostgreSQL, and JSON for other databases (SQLite for testing).
    This stores arrays as JSON in non-PostgreSQL databases.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        """
        Initialize the array type.

        Args:
            item_type: The type of items in the array (e.g., String, Integer)
        """
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        else:
            # Use JSON for SQLite and other databases
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect) -> Any:
        """Process values before binding."""
        if dialect.name == "postgresql":
            # PostgreSQL handles arrays natively
            return value
        else:
            # For SQLite, convert to JSON string
            if value is None:
                return None
            return value  # JSON type handles serialization

    def process_result_value(self, value: Any, dialect) -> Any:
        """Process values from the database."""
        if dialect.name == "postgresql":
            # PostgreSQL returns arrays natively
            return value
        else:
            # For SQLite, JSON type handles deserialization
            return value if value is not None else []


# For convenience, export a function that returns the appropriate type
def get_json_type():
    """
    Get the appropriate JSON type for the current environment.

    This function checks the database URL to determine whether to use
    JSONB (PostgreSQL) or JSON (SQLite/others).
    """
    # Check environment or use JSONType which handles this automatically
    database_url = os.getenv("DATABASE_URL", "")

    if "postgresql" in database_url or "postgres" in database_url:
        return JSONB
    else:
        return JSON


class UUIDType(TypeDecorator):
    """
    Cross-database UUID type.

    Uses PostgreSQL UUID for PostgreSQL, and CHAR(36) for other databases (SQLite).
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect) -> Any:
        """Process values before binding."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # Convert UUID to string for SQLite
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        """Process values from the database."""
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            # Convert string back to UUID for SQLite
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value) if value else None


# Export types
__all__ = ["JSONType", "ArrayType", "UUIDType", "get_json_type"]
