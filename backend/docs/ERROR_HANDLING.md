# Error Handling and Performance Optimization Guide

This document describes the error handling and performance optimization features implemented in the Muset AI Research platform.

## Table of Contents

1. [Error Handling](#error-handling)
2. [Retry Strategies](#retry-strategies)
3. [Caching](#caching)
4. [Monitoring](#monitoring)
5. [Performance Testing](#performance-testing)

## Error Handling

### Error Categories

The system classifies errors into the following categories:

- **AUTHENTICATION**: Authentication-related errors
- **AUTHORIZATION**: Authorization/permission errors
- **VALIDATION**: Input validation errors
- **NOT_FOUND**: Resource not found errors
- **CONFLICT**: Resource conflict errors
- **RATE_LIMIT**: Rate limiting errors
- **EXTERNAL_SERVICE**: External service errors
- **INTERNAL**: Internal server errors
- **DATABASE**: Database errors
- **NETWORK**: Network connectivity errors
- **TIMEOUT**: Operation timeout errors

### Error Severity Levels

- **LOW**: Minor issues that don't affect core functionality
- **MEDIUM**: Issues that may impact some functionality
- **HIGH**: Serious issues requiring attention
- **CRITICAL**: Critical failures requiring immediate action

### Using Custom Exceptions

```python
from app.core.exceptions import NotFoundError, ValidationError, DatabaseError

# Raise a not found error
raise NotFoundError(
    message="User not found",
    resource_type="user",
    details={"user_id": user_id}
)

# Raise a validation error
raise ValidationError(
    message="Invalid email format",
    field="email",
    details={"provided_email": email}
)

# Raise a database error
raise DatabaseError(
    message="Failed to connect to database",
    details={"error": str(e)}
)
```

### User-Friendly Error Messages

All exceptions automatically generate user-friendly error messages:

```json
{
  "error": "NotFoundError",
  "message": "The requested user was not found.",
  "category": "not_found",
  "severity": "low",
  "retryable": false,
  "details": {
    "user_id": "123"
  },
  "path": "/api/v1/users/123"
}
```

## Retry Strategies

### Automatic Retry with Exponential Backoff

```python
from app.core.retry import retry_async, RetryStrategy

# Use default retry strategy
result = await retry_async(
    my_async_function,
    arg1,
    arg2,
    max_retries=3
)

# Use custom retry strategy
strategy = RetryStrategy(
    max_retries=5,
    initial_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

result = await retry_async(
    my_async_function,
    arg1,
    arg2,
    strategy=strategy
)
```

### Retry Decorator

```python
from app.core.retry import retry

@retry(max_retries=3)
async def fetch_external_data():
    # This function will be retried up to 3 times
    # if it raises a retryable exception
    response = await http_client.get(url)
    return response.json()
```

### Circuit Breaker Pattern

```python
from app.core.retry import ErrorRecovery

recovery = ErrorRecovery()

# Get or create a circuit breaker
cb = recovery.get_circuit_breaker(
    name="external_api",
    failure_threshold=5,
    recovery_timeout=60
)

# Use circuit breaker
try:
    result = cb.call(my_function, arg1, arg2)
except Exception as e:
    # Circuit is open or function failed
    pass
```

### Error Recovery

```python
from app.core.retry import error_recovery

async def recovery_action_1():
    # Try to reconnect
    await reconnect_database()

async def recovery_action_2():
    # Try alternative approach
    await use_backup_database()

# Attempt recovery
success = await error_recovery.recover_from_error(
    error=exception,
    recovery_actions=[recovery_action_1, recovery_action_2]
)
```

## Caching

### Redis Cache Manager

```python
from app.core.cache import cache_manager

# Set value in cache
await cache_manager.set("user:123", user_data, expire=300)

# Get value from cache
user_data = await cache_manager.get("user:123")

# Delete from cache
await cache_manager.delete("user:123")

# Delete by pattern
deleted_count = await cache_manager.delete_pattern("user:*")
```

### Cache Decorator

```python
from app.core.cache import cached

@cached(key_prefix="user", expire=300)
async def get_user(user_id: int):
    # This function result will be cached for 5 minutes
    user = await db.query(User).filter(User.id == user_id).first()
    return user
```

### Cache Strategies

#### Cache-Aside (Lazy Loading)

```python
from app.core.cache import CacheStrategy

async def fetch_user_from_db(user_id: int):
    return await db.query(User).filter(User.id == user_id).first()

# Try cache first, then fetch if not found
user = await CacheStrategy.cache_aside(
    key=f"user:{user_id}",
    fetch_func=lambda: fetch_user_from_db(user_id),
    expire=300
)
```

#### Write-Through

```python
async def save_user_to_db(user_data):
    await db.execute(insert(User).values(**user_data))
    await db.commit()

# Write to both cache and database
success = await CacheStrategy.write_through(
    key=f"user:{user_id}",
    value=user_data,
    write_func=lambda data: save_user_to_db(data),
    expire=300
)
```

#### Write-Behind (Write-Back)

```python
async def save_user_to_db(user_data):
    await db.execute(insert(User).values(**user_data))
    await db.commit()

# Write to cache first, then asynchronously to database
success = await CacheStrategy.write_behind(
    key=f"user:{user_id}",
    value=user_data,
    write_func=lambda data: save_user_to_db(data),
    expire=300
)
```

## Monitoring

### Structured Logging

```python
from app.core.logging import get_logger, LogContext

logger = get_logger(__name__)

# Log with context
with LogContext(logger, user_id="123", request_id="abc"):
    logger.info("Processing request")
    logger.error("Error occurred", extra={"error_code": "E001"})
```

### Metrics Collection

```python
from app.core.metrics import (
    track_request,
    track_ai_request,
    track_database_query,
    track_cache_operation,
    track_error
)

# Track HTTP request
track_request(
    method="GET",
    endpoint="/api/users",
    status_code=200,
    duration=0.5
)

# Track AI request
track_ai_request(
    model="gpt-4",
    duration=2.5,
    status="success",
    input_tokens=100,
    output_tokens=200
)

# Track database query
track_database_query(
    operation="select",
    table="users",
    duration=0.01
)

# Track cache operation
track_cache_operation(operation="get", status="hit")

# Track error
track_error(category="authentication", severity="high")
```

### Prometheus Metrics

The application exposes Prometheus metrics at `/metrics`:

- `muset_http_requests_total`: Total HTTP requests
- `muset_http_request_duration_seconds`: HTTP request duration
- `muset_http_requests_active`: Active HTTP requests
- `muset_ai_requests_total`: Total AI requests
- `muset_ai_request_duration_seconds`: AI request duration
- `muset_ai_tokens_total`: Total AI tokens used
- `muset_database_queries_total`: Total database queries
- `muset_database_query_duration_seconds`: Database query duration
- `muset_cache_operations_total`: Total cache operations
- `muset_errors_total`: Total errors

## Performance Testing

### Running Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_error_handling.py

# Run specific test
pytest tests/test_error_handling.py::TestRetryAsync::test_retry_async_success
```

### Running Load Tests with Locust

```bash
# Start Locust
locust -f tests/locustfile.py

# Open browser and navigate to http://localhost:8089
# Configure number of users and spawn rate
# Start swarming

# Run headless mode
locust -f tests/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 1m
```

### Performance Benchmarks

Expected performance metrics:

- **API Response Time**: < 100ms (p95)
- **AI Response Time**: < 5s (p95)
- **Database Query Time**: < 50ms (p95)
- **Cache Get Time**: < 10ms (p95)
- **Cache Hit Rate**: > 80%
- **Concurrent Requests**: 100+ (simultaneous)
- **Throughput**: 1000+ requests/second

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/muset/app.log

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Performance
REQUEST_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=100
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Error Recovery
ENABLE_CIRCUIT_BREAKER=true
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Retry
MAX_RETRIES=3
RETRY_INITIAL_DELAY=1.0
RETRY_MAX_DELAY=60.0

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
```

## Best Practices

1. **Always use appropriate exception types** for different error scenarios
2. **Provide detailed error messages** for logging, but user-friendly messages for clients
3. **Use retry mechanisms** for transient failures (network, timeouts, etc.)
4. **Implement circuit breakers** for external service calls
5. **Cache frequently accessed data** to reduce database load
6. **Monitor metrics** to identify performance bottlenecks
7. **Set appropriate cache expiration times** based on data volatility
8. **Use structured logging** for better log analysis
9. **Track error rates** to identify systemic issues
10. **Regular performance testing** to ensure system scalability
