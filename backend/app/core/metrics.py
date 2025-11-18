"""Metrics collection and monitoring."""
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary


# Define metrics
request_count = Counter(
    "muset_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "muset_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

active_requests = Gauge(
    "muset_http_requests_active",
    "Number of active HTTP requests",
)

ai_request_count = Counter(
    "muset_ai_requests_total",
    "Total AI requests",
    ["model", "status"],
)

ai_request_duration = Histogram(
    "muset_ai_request_duration_seconds",
    "AI request duration in seconds",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

ai_token_usage = Counter(
    "muset_ai_tokens_total",
    "Total AI tokens used",
    ["model", "type"],  # type: input, output
)

database_query_count = Counter(
    "muset_database_queries_total",
    "Total database queries",
    ["operation", "table"],
)

database_query_duration = Histogram(
    "muset_database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

cache_operations = Counter(
    "muset_cache_operations_total",
    "Total cache operations",
    ["operation", "status"],  # operation: get, set, delete; status: hit, miss, success, error
)

error_count = Counter(
    "muset_errors_total",
    "Total errors",
    ["category", "severity"],
)


@dataclass
class MetricEvent:
    """Metric event data."""

    name: str
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Centralized metrics collector."""

    def __init__(self):
        """Initialize metrics collector."""
        self.events: list[MetricEvent] = []
        self.aggregates: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "sum": 0.0, "min": float("inf"), "max": float("-inf")}
        )

    def record_event(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a metric event.

        Args:
            name: Event name
            value: Event value
            tags: Event tags
            metadata: Event metadata
        """
        event = MetricEvent(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            metadata=metadata or {},
        )
        self.events.append(event)

        # Update aggregates
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted((tags or {}).items()))}"
        agg = self.aggregates[key]
        agg["count"] += 1
        agg["sum"] += value
        agg["min"] = min(agg["min"], value)
        agg["max"] = max(agg["max"], value)
        agg["avg"] = agg["sum"] / agg["count"]

    def get_aggregate(self, name: str, tags: Optional[dict[str, str]] = None) -> dict[str, Any]:
        """Get aggregate metrics.

        Args:
            name: Event name
            tags: Event tags

        Returns:
            Aggregate metrics
        """
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted((tags or {}).items()))}"
        return self.aggregates.get(key, {})

    def clear_events(self) -> None:
        """Clear recorded events."""
        self.events = []

    def clear_aggregates(self) -> None:
        """Clear aggregates."""
        self.aggregates.clear()


# Global metrics collector
metrics_collector = MetricsCollector()


@contextmanager
def track_time(
    metric_name: str,
    tags: Optional[dict[str, str]] = None,
    prometheus_metric: Optional[Any] = None,
):
    """Context manager to track execution time.

    Args:
        metric_name: Metric name
        tags: Metric tags
        prometheus_metric: Prometheus metric to update

    Yields:
        None
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics_collector.record_event(metric_name, duration, tags)

        if prometheus_metric:
            if tags:
                prometheus_metric.labels(**tags).observe(duration)
            else:
                prometheus_metric.observe(duration)


def track_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """Track HTTP request metrics.

    Args:
        method: HTTP method
        endpoint: Endpoint path
        status_code: Response status code
        duration: Request duration in seconds
    """
    request_count.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    metrics_collector.record_event(
        "http_request",
        duration,
        {"method": method, "endpoint": endpoint, "status": str(status_code)},
    )


def track_ai_request(
    model: str,
    duration: float,
    status: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """Track AI request metrics.

    Args:
        model: AI model name
        duration: Request duration in seconds
        status: Request status (success, error)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    ai_request_count.labels(model=model, status=status).inc()
    ai_request_duration.labels(model=model).observe(duration)

    if input_tokens > 0:
        ai_token_usage.labels(model=model, type="input").inc(input_tokens)

    if output_tokens > 0:
        ai_token_usage.labels(model=model, type="output").inc(output_tokens)

    metrics_collector.record_event(
        "ai_request",
        duration,
        {"model": model, "status": status},
        {"input_tokens": input_tokens, "output_tokens": output_tokens},
    )


def track_database_query(operation: str, table: str, duration: float) -> None:
    """Track database query metrics.

    Args:
        operation: Query operation (select, insert, update, delete)
        table: Table name
        duration: Query duration in seconds
    """
    database_query_count.labels(operation=operation, table=table).inc()
    database_query_duration.labels(operation=operation, table=table).observe(duration)
    metrics_collector.record_event(
        "database_query",
        duration,
        {"operation": operation, "table": table},
    )


def track_cache_operation(operation: str, status: str) -> None:
    """Track cache operation metrics.

    Args:
        operation: Cache operation (get, set, delete)
        status: Operation status (hit, miss, success, error)
    """
    cache_operations.labels(operation=operation, status=status).inc()
    metrics_collector.record_event(
        "cache_operation",
        1.0,
        {"operation": operation, "status": status},
    )


def track_error(category: str, severity: str) -> None:
    """Track error metrics.

    Args:
        category: Error category
        severity: Error severity
    """
    error_count.labels(category=category, severity=severity).inc()
    metrics_collector.record_event(
        "error",
        1.0,
        {"category": category, "severity": severity},
    )
