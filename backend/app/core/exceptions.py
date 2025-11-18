"""Custom exceptions and error handlers."""
import logging
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error categories for classification."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    DATABASE = "database"
    NETWORK = "network"
    TIMEOUT = "timeout"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MusetException(Exception):
    """Base exception for Muset application."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retryable: bool = False,
    ):
        """Initialize exception.

        Args:
            message: Error message for logging
            status_code: HTTP status code
            category: Error category
            severity: Error severity
            details: Additional error details
            user_message: User-friendly error message
            retryable: Whether the operation can be retried
        """
        self.message = message
        self.status_code = status_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or self._generate_user_message()
        self.retryable = retryable
        super().__init__(self.message)

    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        # Override in subclasses for specific messages
        return "An error occurred. Please try again later."


class AuthenticationError(MusetException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed", details: Optional[dict[str, Any]] = None):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="Authentication failed. Please check your credentials and try again.",
            retryable=False,
        )


class AuthorizationError(MusetException):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied", details: Optional[dict[str, Any]] = None):
        """Initialize authorization error."""
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="You don't have permission to access this resource.",
            retryable=False,
        )


class NotFoundError(MusetException):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found", resource_type: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize not found error."""
        user_msg = f"The requested {resource_type} was not found." if resource_type else "The requested resource was not found."
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class ValidationError(MusetException):
    """Validation error."""

    def __init__(self, message: str = "Validation error", field: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize validation error."""
        user_msg = f"Invalid value for {field}." if field else "The provided data is invalid."
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class ConflictError(MusetException):
    """Resource conflict error."""

    def __init__(self, message: str = "Resource conflict", details: Optional[dict[str, Any]] = None):
        """Initialize conflict error."""
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message="The resource already exists or conflicts with an existing resource.",
            retryable=False,
        )


class RateLimitError(MusetException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, details: Optional[dict[str, Any]] = None):
        """Initialize rate limit error."""
        if retry_after:
            user_msg = f"Too many requests. Please try again in {retry_after} seconds."
        else:
            user_msg = "Too many requests. Please slow down and try again later."

        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=user_msg,
            retryable=True,
        )


class DatabaseError(MusetException):
    """Database error."""

    def __init__(self, message: str = "Database error", details: Optional[dict[str, Any]] = None):
        """Initialize database error."""
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            user_message="A database error occurred. Please try again later.",
            retryable=True,
        )


class NetworkError(MusetException):
    """Network error."""

    def __init__(self, message: str = "Network error", details: Optional[dict[str, Any]] = None):
        """Initialize network error."""
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message="A network error occurred. Please check your connection and try again.",
            retryable=True,
        )


class TimeoutError(MusetException):
    """Timeout error."""

    def __init__(self, message: str = "Operation timed out", timeout: Optional[float] = None, details: Optional[dict[str, Any]] = None):
        """Initialize timeout error."""
        user_msg = f"The operation timed out after {timeout} seconds." if timeout else "The operation timed out."

        details = details or {}
        if timeout:
            details["timeout"] = timeout

        super().__init__(
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=user_msg,
            retryable=True,
        )


class ExternalServiceError(MusetException):
    """External service error."""

    def __init__(self, message: str = "External service error", service: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize external service error."""
        user_msg = f"An error occurred with {service} service." if service else "An error occurred with an external service."
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=user_msg,
            retryable=True,
        )


class FileNotFoundError(MusetException):
    """File not found error."""

    def __init__(self, message: str = "File not found", file_path: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize file not found error."""
        user_msg = f"File not found: {file_path}" if file_path else "The requested file was not found."
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class PermissionDeniedError(MusetException):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied", resource: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize permission denied error."""
        user_msg = f"Permission denied for {resource}." if resource else "You don't have permission to perform this action."
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class MCPConnectionError(MusetException):
    """MCP server connection error."""

    def __init__(self, message: str = "MCP connection error", server: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize MCP connection error."""
        user_msg = f"Failed to connect to MCP server: {server}" if server else "Failed to connect to MCP server."
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=user_msg,
            retryable=True,
        )


class MCPToolConversionError(MusetException):
    """MCP tool conversion error."""

    def __init__(self, message: str = "MCP tool conversion error", tool: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize MCP tool conversion error."""
        user_msg = f"Failed to convert MCP tool: {tool}" if tool else "Failed to convert MCP tool."
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class SkillLoadError(MusetException):
    """Skill loading error."""

    def __init__(self, message: str = "Skill load error", skill: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize skill load error."""
        user_msg = f"Failed to load skill: {skill}" if skill else "Failed to load skill."
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


class SkillValidationError(MusetException):
    """Skill validation error."""

    def __init__(self, message: str = "Skill validation error", skill: Optional[str] = None, details: Optional[dict[str, Any]] = None):
        """Initialize skill validation error."""
        user_msg = f"Skill validation failed: {skill}" if skill else "Skill validation failed."
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=user_msg,
            retryable=False,
        )


async def muset_exception_handler(request: Request, exc: MusetException) -> JSONResponse:
    """Handle Muset custom exceptions.

    Args:
        request: FastAPI request
        exc: Muset exception

    Returns:
        JSON response with error details
    """
    # Log error with appropriate level based on severity
    log_message = f"{exc.category.value}: {exc.message}"
    if exc.severity == ErrorSeverity.CRITICAL:
        logger.critical(log_message, extra={"details": exc.details, "path": str(request.url)})
    elif exc.severity == ErrorSeverity.HIGH:
        logger.error(log_message, extra={"details": exc.details, "path": str(request.url)})
    elif exc.severity == ErrorSeverity.MEDIUM:
        logger.warning(log_message, extra={"details": exc.details, "path": str(request.url)})
    else:
        logger.info(log_message, extra={"details": exc.details, "path": str(request.url)})

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.user_message,
            "category": exc.category.value,
            "severity": exc.severity.value,
            "retryable": exc.retryable,
            "details": exc.details,
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
    # Log unexpected exceptions as critical
    logger.critical(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={"path": str(request.url)},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "category": ErrorCategory.INTERNAL.value,
            "severity": ErrorSeverity.CRITICAL.value,
            "retryable": False,
            "path": str(request.url),
        },
    )
