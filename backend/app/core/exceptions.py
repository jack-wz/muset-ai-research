"""Custom exceptions and error handlers."""
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class MusetException(Exception):
    """Base exception for Muset application."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        """Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(MusetException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error."""
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(MusetException):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied"):
        """Initialize authorization error."""
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(MusetException):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        """Initialize not found error."""
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationError(MusetException):
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        """Initialize validation error."""
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileNotFoundError(MusetException):
    """File not found error."""

    def __init__(self, message: str = "File not found"):
        """Initialize file not found error."""
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class PermissionDeniedError(MusetException):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied"):
        """Initialize permission denied error."""
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class MCPConnectionError(MusetException):
    """MCP server connection error."""

    def __init__(self, message: str = "MCP connection error"):
        """Initialize MCP connection error."""
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class MCPToolConversionError(MusetException):
    """MCP tool conversion error."""

    def __init__(self, message: str = "MCP tool conversion error"):
        """Initialize MCP tool conversion error."""
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class SkillLoadError(MusetException):
    """Skill loading error."""

    def __init__(self, message: str = "Skill load error"):
        """Initialize skill load error."""
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class SkillValidationError(MusetException):
    """Skill validation error."""

    def __init__(self, message: str = "Skill validation error"):
        """Initialize skill validation error."""
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


async def muset_exception_handler(request: Request, exc: MusetException) -> JSONResponse:
    """Handle Muset custom exceptions.

    Args:
        request: FastAPI request
        exc: Muset exception

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": str(request.url),
        },
    )
