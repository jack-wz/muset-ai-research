"""Custom middleware for the application."""
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import active_requests, track_request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from the application
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # Get client IP
        client_host = request.client.host if request.client else "unknown"

        # Increment active requests
        active_requests.inc()

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log request details
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"Client: {client_host}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "client_host": client_host,
                },
            )

            # Track metrics
            track_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration=process_time,
            )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s - "
                f"Client: {client_host}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "process_time": process_time,
                    "client_host": client_host,
                },
            )

            # Track error metrics
            track_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=500,
                duration=process_time,
            )

            raise

        finally:
            # Decrement active requests
            active_requests.dec()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response from the application
        """
        # Get client identifier (IP address)
        client_host = request.client.host if request.client else "unknown"

        # Get current time
        current_time = time.time()

        # Initialize or get request history
        if client_host not in self.request_counts:
            self.request_counts[client_host] = []

        # Remove old requests (older than 1 minute)
        self.request_counts[client_host] = [
            req_time
            for req_time in self.request_counts[client_host]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.request_counts[client_host]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for client: {client_host}",
                extra={"client_host": client_host},
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitError",
                    "message": "Too many requests. Please try again later.",
                },
            )

        # Add current request
        self.request_counts[client_host].append(current_time)

        # Process request
        return await call_next(request)
