"""Performance tests."""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.cache import CacheManager, CacheStrategy, cached


class TestCachePerformance:
    """Test cache performance."""

    @pytest.mark.asyncio
    async def test_cache_get_performance(self):
        """Test cache get performance."""
        cache = CacheManager()

        # Set up test data
        await cache.set("test_key", {"data": "test"}, expire=60)

        # Measure get performance
        start = time.time()
        for _ in range(100):
            await cache.get("test_key")
        duration = time.time() - start

        # Should complete 100 gets in less than 1 second
        assert duration < 1.0

        await cache.close()

    @pytest.mark.asyncio
    async def test_cache_set_performance(self):
        """Test cache set performance."""
        cache = CacheManager()

        # Measure set performance
        start = time.time()
        for i in range(100):
            await cache.set(f"test_key_{i}", {"data": f"test_{i}"}, expire=60)
        duration = time.time() - start

        # Should complete 100 sets in less than 2 seconds
        assert duration < 2.0

        await cache.close()

    @pytest.mark.asyncio
    async def test_cached_decorator_performance(self):
        """Test cached decorator performance."""
        call_count = 0

        @cached(key_prefix="test", expire=60)
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * 2

        # First call should execute function
        start = time.time()
        result1 = await expensive_function(5)
        duration1 = time.time() - start

        assert result1 == 10
        assert call_count == 1
        assert duration1 >= 0.1

        # Second call should use cache (much faster)
        start = time.time()
        result2 = await expensive_function(5)
        duration2 = time.time() - start

        assert result2 == 10
        assert call_count == 1  # Function not called again
        assert duration2 < 0.05  # Much faster than first call

    @pytest.mark.asyncio
    async def test_cache_aside_performance(self):
        """Test cache-aside strategy performance."""
        cache = CacheManager()
        call_count = 0

        async def fetch_data():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"data": "test"}

        # First call should fetch from source
        start = time.time()
        result1 = await CacheStrategy.cache_aside("test_key", fetch_data, expire=60)
        duration1 = time.time() - start

        assert result1["data"] == "test"
        assert call_count == 1
        assert duration1 >= 0.1

        # Second call should use cache
        start = time.time()
        result2 = await CacheStrategy.cache_aside("test_key", fetch_data, expire=60)
        duration2 = time.time() - start

        assert result2["data"] == "test"
        assert call_count == 1  # Not called again
        assert duration2 < 0.05

        await cache.close()


class TestRetryPerformance:
    """Test retry mechanism performance."""

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test retry performance with exponential backoff."""
        from app.core.retry import retry_async, RetryStrategy
        from app.core.exceptions import NetworkError

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Connection failed")
            return "success"

        strategy = RetryStrategy(
            max_retries=3,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False,
        )

        start = time.time()
        result = await retry_async(failing_func, max_retries=3, strategy=strategy)
        duration = time.time() - start

        assert result == "success"
        assert call_count == 3

        # Expected delays: 0 (first), 0.1 (retry 1), 0.2 (retry 2)
        # Total: 0.3 seconds + execution time
        assert 0.3 <= duration < 0.5


class TestConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations."""
        cache = CacheManager()

        async def set_and_get(key: str, value: str):
            await cache.set(key, value, expire=60)
            return await cache.get(key)

        # Run 50 concurrent operations
        start = time.time()
        tasks = [set_and_get(f"key_{i}", f"value_{i}") for i in range(50)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        # All results should be correct
        for i, result in enumerate(results):
            assert result == f"value_{i}"

        # Should complete in reasonable time
        assert duration < 2.0

        await cache.close()

    @pytest.mark.asyncio
    async def test_concurrent_retries(self):
        """Test concurrent retry operations."""
        from app.core.retry import retry_async
        from app.core.exceptions import NetworkError

        call_counts = {}

        async def failing_func(task_id: int):
            if task_id not in call_counts:
                call_counts[task_id] = 0
            call_counts[task_id] += 1

            if call_counts[task_id] < 2:
                raise NetworkError("Connection failed")
            return f"success_{task_id}"

        # Run 20 concurrent retry operations
        start = time.time()
        tasks = [retry_async(failing_func, task_id=i, max_retries=3) for i in range(20)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start

        # All should succeed
        for i, result in enumerate(results):
            assert result == f"success_{i}"

        # Should complete in reasonable time
        assert duration < 5.0


class TestMemoryUsage:
    """Test memory usage."""

    @pytest.mark.asyncio
    async def test_metrics_collector_memory(self):
        """Test metrics collector memory usage."""
        from app.core.metrics import MetricsCollector

        collector = MetricsCollector()

        # Record many events
        for i in range(10000):
            collector.record_event(
                name="test_metric",
                value=float(i),
                tags={"index": str(i)},
            )

        assert len(collector.events) == 10000

        # Clear and verify memory is released
        collector.clear_events()
        assert len(collector.events) == 0

        collector.clear_aggregates()
        assert len(collector.aggregates) == 0


class TestDatabaseQueryPerformance:
    """Test database query performance."""

    @pytest.mark.asyncio
    async def test_query_with_caching(self):
        """Test database query performance with caching."""
        cache = CacheManager()
        query_count = 0

        async def execute_query():
            nonlocal query_count
            query_count += 1
            await asyncio.sleep(0.1)  # Simulate database query
            return {"id": 1, "name": "Test User"}

        # First query (cache miss)
        start = time.time()
        result1 = await CacheStrategy.cache_aside("user:1", execute_query, expire=60)
        duration1 = time.time() - start

        assert result1["name"] == "Test User"
        assert query_count == 1
        assert duration1 >= 0.1

        # Subsequent queries (cache hit)
        total_duration = 0
        for _ in range(10):
            start = time.time()
            result = await CacheStrategy.cache_aside("user:1", execute_query, expire=60)
            total_duration += time.time() - start
            assert result["name"] == "Test User"

        assert query_count == 1  # Query executed only once
        assert total_duration < 0.5  # Much faster with cache

        await cache.close()
