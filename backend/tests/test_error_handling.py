"""Tests for error handling system."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import (
    AuthenticationError,
    DatabaseError,
    ErrorCategory,
    ErrorSeverity,
    ExternalServiceError,
    MCPConnectionError,
    MusetException,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from app.core.retry import (
    CircuitBreaker,
    ErrorRecovery,
    RetryStrategy,
    retry,
    retry_async,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_muset_exception_base(self):
        """Test base Muset exception."""
        exc = MusetException(
            message="Test error",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
        )

        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.category == ErrorCategory.INTERNAL
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is False
        assert exc.user_message is not None

    def test_authentication_error(self):
        """Test authentication error."""
        exc = AuthenticationError(message="Invalid token")

        assert exc.message == "Invalid token"
        assert exc.status_code == 401
        assert exc.category == ErrorCategory.AUTHENTICATION
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is False
        assert "Authentication failed" in exc.user_message

    def test_not_found_error(self):
        """Test not found error."""
        exc = NotFoundError(message="User not found", resource_type="user")

        assert exc.message == "User not found"
        assert exc.status_code == 404
        assert exc.category == ErrorCategory.NOT_FOUND
        assert exc.severity == ErrorSeverity.LOW
        assert "user" in exc.user_message

    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError(message="Invalid email", field="email")

        assert exc.message == "Invalid email"
        assert exc.status_code == 422
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.severity == ErrorSeverity.LOW
        assert "email" in exc.user_message

    def test_rate_limit_error(self):
        """Test rate limit error."""
        exc = RateLimitError(message="Too many requests", retry_after=60)

        assert exc.message == "Too many requests"
        assert exc.status_code == 429
        assert exc.category == ErrorCategory.RATE_LIMIT
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.retryable is True
        assert exc.details["retry_after"] == 60
        assert "60 seconds" in exc.user_message

    def test_database_error(self):
        """Test database error."""
        exc = DatabaseError(message="Connection failed")

        assert exc.message == "Connection failed"
        assert exc.status_code == 500
        assert exc.category == ErrorCategory.DATABASE
        assert exc.severity == ErrorSeverity.CRITICAL
        assert exc.retryable is True

    def test_network_error(self):
        """Test network error."""
        exc = NetworkError(message="Connection timeout")

        assert exc.message == "Connection timeout"
        assert exc.status_code == 503
        assert exc.category == ErrorCategory.NETWORK
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is True

    def test_timeout_error(self):
        """Test timeout error."""
        exc = TimeoutError(message="Request timeout", timeout=30.0)

        assert exc.message == "Request timeout"
        assert exc.status_code == 504
        assert exc.category == ErrorCategory.TIMEOUT
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.retryable is True
        assert exc.details["timeout"] == 30.0

    def test_external_service_error(self):
        """Test external service error."""
        exc = ExternalServiceError(message="API error", service="OpenAI")

        assert exc.message == "API error"
        assert exc.status_code == 503
        assert exc.category == ErrorCategory.EXTERNAL_SERVICE
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.retryable is True
        assert "OpenAI" in exc.user_message


class TestRetryStrategy:
    """Test retry strategies."""

    def test_retry_strategy_delay(self):
        """Test retry strategy delay calculation."""
        strategy = RetryStrategy(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Test exponential backoff
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0

    def test_retry_strategy_max_delay(self):
        """Test retry strategy maximum delay."""
        strategy = RetryStrategy(
            max_retries=10,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False,
        )

        # Delay should not exceed max_delay
        assert strategy.get_delay(10) == 10.0

    def test_retry_strategy_jitter(self):
        """Test retry strategy with jitter."""
        strategy = RetryStrategy(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True,
        )

        # With jitter, delay should be randomized
        delay = strategy.get_delay(1)
        assert 1.0 <= delay <= 4.0


class TestRetryAsync:
    """Test async retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test successful retry."""
        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(success_func, max_retries=3)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_with_retries(self):
        """Test retry with failures then success."""
        call_count = 0

        async def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Connection failed")
            return "success"

        result = await retry_async(retry_func, max_retries=3)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_all_fail(self):
        """Test retry when all attempts fail."""
        call_count = 0

        async def fail_func():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Connection failed")

        with pytest.raises(NetworkError):
            await retry_async(fail_func, max_retries=2)

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_async_non_retryable_error(self):
        """Test retry with non-retryable error."""
        call_count = 0

        async def fail_func():
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid input")

        with pytest.raises(ValidationError):
            await retry_async(fail_func, max_retries=2)

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry decorator."""
        call_count = 0

        @retry(max_retries=2)
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Connection failed")
            return "success"

        result = await decorated_func()

        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_closed(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "closed"

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        def fail_func():
            raise Exception("Error")

        # Trigger failures to open circuit
        for _ in range(3):
            try:
                cb.call(fail_func)
            except Exception:
                pass

        assert cb.state == "open"

        # Circuit should be open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            cb.call(fail_func)

    def test_circuit_breaker_half_open(self):
        """Test circuit breaker half-open state."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def fail_func():
            raise Exception("Error")

        # Open circuit
        for _ in range(2):
            try:
                cb.call(fail_func)
            except Exception:
                pass

        assert cb.state == "open"

        # Wait for recovery timeout
        import time
        time.sleep(0.2)

        # Should be half-open now
        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "closed"


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_error_recovery_success(self):
        """Test successful error recovery."""
        recovery = ErrorRecovery()

        recovery_called = False

        async def recovery_action():
            nonlocal recovery_called
            recovery_called = True

        success = await recovery.recover_from_error(
            Exception("Test error"),
            recovery_actions=[recovery_action],
        )

        assert success is True
        assert recovery_called is True

    @pytest.mark.asyncio
    async def test_error_recovery_failure(self):
        """Test failed error recovery."""
        recovery = ErrorRecovery()

        async def failing_recovery():
            raise Exception("Recovery failed")

        success = await recovery.recover_from_error(
            Exception("Test error"),
            recovery_actions=[failing_recovery],
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_error_recovery_multiple_actions(self):
        """Test error recovery with multiple actions."""
        recovery = ErrorRecovery()

        actions_called = []

        async def action1():
            actions_called.append(1)
            raise Exception("Action 1 failed")

        async def action2():
            actions_called.append(2)
            # Success

        success = await recovery.recover_from_error(
            Exception("Test error"),
            recovery_actions=[action1, action2],
        )

        assert success is True
        assert actions_called == [1, 2]

    def test_get_circuit_breaker(self):
        """Test getting circuit breaker."""
        recovery = ErrorRecovery()

        cb1 = recovery.get_circuit_breaker("test1")
        cb2 = recovery.get_circuit_breaker("test1")
        cb3 = recovery.get_circuit_breaker("test2")

        # Should return same instance for same name
        assert cb1 is cb2

        # Should return different instance for different name
        assert cb1 is not cb3
