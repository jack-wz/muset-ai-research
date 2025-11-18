"""Tests for monitoring and logging."""
import logging
import pytest
from unittest.mock import MagicMock, patch

from app.core.logging import CustomJsonFormatter, LogContext, get_logger, setup_logging
from app.core.metrics import (
    MetricsCollector,
    metrics_collector,
    track_ai_request,
    track_cache_operation,
    track_database_query,
    track_error,
    track_request,
    track_time,
)


class TestLogging:
    """Test logging functionality."""

    def test_setup_logging_json(self):
        """Test JSON logging setup."""
        setup_logging(level="INFO", format_type="json")

        logger = logging.getLogger()
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_text(self):
        """Test text logging setup."""
        setup_logging(level="DEBUG", format_type="text")

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_get_logger(self):
        """Test getting logger."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"

    def test_log_context(self):
        """Test log context manager."""
        logger = get_logger("test")

        with LogContext(logger, user_id="123", request_id="abc"):
            # Context should be active
            pass

        # Context should be cleaned up

    def test_custom_json_formatter(self):
        """Test custom JSON formatter."""
        formatter = CustomJsonFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        log_dict = {}
        formatter.add_fields(log_dict, record, {})

        assert "timestamp" in log_dict
        assert "level" in log_dict
        assert "logger" in log_dict
        assert "source" in log_dict
        assert "process" in log_dict
        assert "thread" in log_dict


class TestMetrics:
    """Test metrics collection."""

    def test_metrics_collector_record_event(self):
        """Test recording metric events."""
        collector = MetricsCollector()

        collector.record_event(
            name="test_metric",
            value=10.0,
            tags={"type": "test"},
        )

        assert len(collector.events) == 1
        event = collector.events[0]
        assert event.name == "test_metric"
        assert event.value == 10.0
        assert event.tags["type"] == "test"

    def test_metrics_collector_aggregates(self):
        """Test metric aggregation."""
        collector = MetricsCollector()

        # Record multiple events
        collector.record_event("test", 10.0)
        collector.record_event("test", 20.0)
        collector.record_event("test", 30.0)

        agg = collector.get_aggregate("test")
        assert agg["count"] == 3
        assert agg["sum"] == 60.0
        assert agg["min"] == 10.0
        assert agg["max"] == 30.0
        assert agg["avg"] == 20.0

    def test_metrics_collector_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()

        collector.record_event("test", 10.0)
        assert len(collector.events) == 1

        collector.clear_events()
        assert len(collector.events) == 0

        collector.record_event("test", 10.0)
        collector.clear_aggregates()
        assert len(collector.aggregates) == 0

    def test_track_request(self):
        """Test tracking HTTP requests."""
        track_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration=0.5,
        )

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "http_request"]
        assert len(events) > 0

    def test_track_ai_request(self):
        """Test tracking AI requests."""
        track_ai_request(
            model="gpt-4",
            duration=2.5,
            status="success",
            input_tokens=100,
            output_tokens=200,
        )

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "ai_request"]
        assert len(events) > 0

    def test_track_database_query(self):
        """Test tracking database queries."""
        track_database_query(
            operation="select",
            table="users",
            duration=0.01,
        )

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "database_query"]
        assert len(events) > 0

    def test_track_cache_operation(self):
        """Test tracking cache operations."""
        track_cache_operation(operation="get", status="hit")

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "cache_operation"]
        assert len(events) > 0

    def test_track_error(self):
        """Test tracking errors."""
        track_error(category="authentication", severity="high")

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "error"]
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_track_time_context(self):
        """Test time tracking context manager."""
        import asyncio

        with track_time("test_operation", tags={"type": "test"}):
            await asyncio.sleep(0.1)

        # Verify event was recorded
        events = [e for e in metrics_collector.events if e.name == "test_operation"]
        assert len(events) > 0
        assert events[-1].value >= 0.1


class TestMetricsIntegration:
    """Test metrics integration."""

    def test_prometheus_metrics_exist(self):
        """Test Prometheus metrics are defined."""
        from app.core.metrics import (
            active_requests,
            ai_request_count,
            ai_request_duration,
            ai_token_usage,
            cache_operations,
            database_query_count,
            database_query_duration,
            error_count,
            request_count,
            request_duration,
        )

        # Verify all metrics are defined
        assert active_requests is not None
        assert ai_request_count is not None
        assert ai_request_duration is not None
        assert ai_token_usage is not None
        assert cache_operations is not None
        assert database_query_count is not None
        assert database_query_duration is not None
        assert error_count is not None
        assert request_count is not None
        assert request_duration is not None
