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
