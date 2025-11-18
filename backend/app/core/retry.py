"""Retry strategies and error recovery mechanisms."""
import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union

from app.core.exceptions import (
    DatabaseError,
    ExternalServiceError,
    MCPConnectionError,
    MusetException,
    NetworkError,
    RateLimitError,
    TimeoutError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy:
    """Base retry strategy."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(self.initial_delay * (self.exponential_base ** attempt), self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay


class CircuitBreaker:
    """Circuit breaker pattern for error recovery."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Call function with circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open
        """
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker recovered to closed state")
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            raise e


async def retry_async(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    retry_on: tuple[Type[Exception], ...] = (
        NetworkError,
        TimeoutError,
        DatabaseError,
        ExternalServiceError,
        MCPConnectionError,
    ),
    strategy: Optional[RetryStrategy] = None,
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments
        max_retries: Maximum number of retries
        retry_on: Tuple of exception types to retry on
        strategy: Retry strategy to use
        **kwargs: Keyword arguments

    Returns:
        Function result

    Raises:
        Exception: If all retries fail
    """
    if strategy is None:
        strategy = RetryStrategy(max_retries=max_retries)

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except retry_on as e:
            last_exception = e
            if attempt < max_retries:
                delay = strategy.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
        except Exception as e:
            # Don't retry on other exceptions
            logger.error(f"Non-retryable exception: {str(e)}")
            raise

    if last_exception:
        raise last_exception


def retry(
    max_retries: int = 3,
    retry_on: tuple[Type[Exception], ...] = (
        NetworkError,
        TimeoutError,
        DatabaseError,
        ExternalServiceError,
        MCPConnectionError,
    ),
    strategy: Optional[RetryStrategy] = None,
):
    """Decorator for retrying async functions.

    Args:
        max_retries: Maximum number of retries
        retry_on: Tuple of exception types to retry on
        strategy: Retry strategy to use

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(
                func,
                *args,
                max_retries=max_retries,
                retry_on=retry_on,
                strategy=strategy,
                **kwargs,
            )
        return wrapper
    return decorator


class ErrorRecovery:
    """Error recovery mechanisms."""

    def __init__(self):
        """Initialize error recovery."""
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> CircuitBreaker:
        """Get or create circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Recovery timeout in seconds

        Returns:
            Circuit breaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return self.circuit_breakers[name]

    async def recover_from_error(
        self,
        error: Exception,
        recovery_actions: Optional[list[Callable[[], Any]]] = None,
    ) -> bool:
        """Attempt to recover from an error.

        Args:
            error: Error to recover from
            recovery_actions: List of recovery actions to attempt

        Returns:
            True if recovery successful, False otherwise
        """
        if recovery_actions is None:
            recovery_actions = []

        logger.info(f"Attempting to recover from error: {str(error)}")

        for i, action in enumerate(recovery_actions):
            try:
                logger.info(f"Executing recovery action {i + 1}/{len(recovery_actions)}")
                if asyncio.iscoroutinefunction(action):
                    await action()
                else:
                    action()
                logger.info(f"Recovery action {i + 1} successful")
                return True
            except Exception as e:
                logger.warning(f"Recovery action {i + 1} failed: {str(e)}")
                continue

        logger.error("All recovery actions failed")
        return False


# Global error recovery instance
error_recovery = ErrorRecovery()
