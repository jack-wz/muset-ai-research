"""Custom middleware for the application."""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


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
        start_time = time.time()

        # Get client IP
        client_host = request.client.host if request.client else "unknown"

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request details
        print(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s "
            f"- Client: {client_host}"
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)

        return response
