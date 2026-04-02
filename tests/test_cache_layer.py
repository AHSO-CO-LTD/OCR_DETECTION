"""
Unit tests for CacheLayer (Query Result Caching with TTL).

Coverage targets: 90%+ for cache management and TTL logic.
Tests verify: caching, expiration, metrics, thread safety, LRU eviction.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from lib.CacheLayer import CacheLayer, CacheEntry, CacheMetrics, QueryCacheManager, cached


# ============================================================================
# TEST GROUP 1: INITIALIZATION (2 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_layer_init_default():
    """Verify CacheLayer initializes with correct defaults"""
    cache = CacheLayer()

    assert cache.max_size == 1000
    assert len(cache._cache) == 0
    assert len(cache._access_times) == 0
    assert cache._metrics.total_hits == 0
    assert cache._metrics.total_misses == 0


@pytest.mark.unit
def test_cache_layer_init_custom_size():
    """Verify CacheLayer accepts custom max size"""
    cache = CacheLayer(max_size=100)

    assert cache.max_size == 100


# ============================================================================
# TEST GROUP 2: SET & GET (4 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_set_and_get():
    """Verify set and get work together"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)
    result = cache.get("key1")

    assert result == "value1"


@pytest.mark.unit
def test_cache_get_nonexistent():
    """Verify get returns None for non-existent key"""
    cache = CacheLayer()

    result = cache.get("nonexistent")

    assert result is None
    assert cache._metrics.total_misses == 1


@pytest.mark.unit
def test_cache_get_expired():
    """Verify get returns None for expired entry"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=0)  # TTL = 0 = already expired
    time.sleep(0.01)

    result = cache.get("key1")

    assert result is None
    assert cache._metrics.total_misses == 1


@pytest.mark.unit
def test_cache_hit_counter():
    """Verify hit counter increments correctly"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)

    # First get = hit
    cache.get("key1")
    assert cache._metrics.total_hits == 1

    # Second get = hit
    cache.get("key1")
    assert cache._metrics.total_hits == 2


# ============================================================================
# TEST GROUP 3: EXISTS & CLEAR (4 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_exists_valid():
    """Verify exists returns True for valid key"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)

    assert cache.exists("key1") is True


@pytest.mark.unit
def test_cache_exists_expired():
    """Verify exists returns False for expired key"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=0)
    time.sleep(0.01)

    assert cache.exists("key1") is False


@pytest.mark.unit
def test_cache_clear():
    """Verify clear removes specific key"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)
    cache.set("key2", "value2", ttl=60)

    cache.clear("key1")

    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"


@pytest.mark.unit
def test_cache_clear_all():
    """Verify clear_all removes all entries"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)
    cache.set("key2", "value2", ttl=60)

    cache.clear_all()

    assert len(cache._cache) == 0
    assert cache.get("key1") is None
    assert cache.get("key2") is None


# ============================================================================
# TEST GROUP 4: PATTERN CLEARING (2 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_clear_pattern():
    """Verify clear_pattern removes matching keys"""
    cache = CacheLayer()

    cache.set("user:1", "data1", ttl=60)
    cache.set("user:2", "data2", ttl=60)
    cache.set("settings:theme", "dark", ttl=60)

    cleared = cache.clear_pattern("user:")

    assert cleared == 2
    assert cache.get("user:1") is None
    assert cache.get("user:2") is None
    assert cache.get("settings:theme") == "dark"


@pytest.mark.unit
def test_cache_clear_pattern_no_matches():
    """Verify clear_pattern with no matches"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)

    cleared = cache.clear_pattern("nonexistent:")

    assert cleared == 0
    assert cache.get("key1") == "value1"


# ============================================================================
# TEST GROUP 5: TTL & EXPIRATION (3 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_entry_expiration():
    """Verify CacheEntry correctly identifies expiration"""
    entry = CacheEntry(
        value="test",
        created_at=time.time() - 10,  # 10 seconds ago
        ttl_seconds=5
    )

    assert entry.is_expired() is True


@pytest.mark.unit
def test_cache_entry_age():
    """Verify CacheEntry.age_seconds() works"""
    entry = CacheEntry(
        value="test",
        created_at=time.time() - 2,
        ttl_seconds=60
    )

    age = entry.age_seconds()
    assert 1.9 < age < 2.1  # Allow small timing variance


@pytest.mark.unit
def test_cache_different_ttls():
    """Verify different TTLs work correctly"""
    cache = CacheLayer()

    cache.set("fast", "value1", ttl=0)
    cache.set("slow", "value2", ttl=60)

    # Fast one expires immediately
    assert cache.get("fast") is None

    # Slow one should still be valid
    assert cache.get("slow") == "value2"


# ============================================================================
# TEST GROUP 6: METRICS & STATS (3 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_metrics_hit_rate():
    """Verify hit rate calculation"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)

    # 2 hits
    cache.get("key1")
    cache.get("key1")

    # 1 miss
    cache.get("nonexistent")

    metrics = cache.get_metrics()

    # Hit rate = 2 / (2+1) = 66.7%
    assert "66.6" in metrics["hit_rate_percent"] or "66.7" in metrics["hit_rate_percent"]


@pytest.mark.unit
def test_cache_get_entry_info():
    """Verify get_entry_info returns detailed info"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)
    cache.get("key1")  # Increment hit count

    info = cache.get_entry_info("key1")

    assert info["key"] == "key1"
    assert info["value_type"] == "str"
    assert info["hit_count"] >= 1
    assert info["is_expired"] is False


@pytest.mark.unit
def test_cache_stats_string():
    """Verify stats string is formatted correctly"""
    cache = CacheLayer()

    cache.set("key1", "value1", ttl=60)

    stats = cache.get_stats()

    assert "CacheLayer Stats" in stats
    assert "Cache Size" in stats
    assert "Hit Rate" in stats


# ============================================================================
# TEST GROUP 7: LRU EVICTION (2 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_lru_eviction():
    """Verify LRU eviction when cache is full"""
    cache = CacheLayer(max_size=3)

    # Fill cache
    cache.set("key1", "value1", ttl=60)
    time.sleep(0.01)
    cache.set("key2", "value2", ttl=60)
    time.sleep(0.01)
    cache.set("key3", "value3", ttl=60)

    assert len(cache._cache) == 3

    # Add 4th key: should evict LRU (key1)
    cache.set("key4", "value4", ttl=60)

    assert len(cache._cache) == 3
    assert cache.get("key1") is None  # key1 was evicted
    assert cache.get("key4") == "value4"  # key4 is present


@pytest.mark.unit
def test_cache_lru_access_time_update():
    """Verify access time updates on cache hit"""
    cache = CacheLayer(max_size=2)

    cache.set("key1", "value1", ttl=60)
    cache.set("key2", "value2", ttl=60)

    # Access key1 (update its access time)
    cache.get("key1")
    time.sleep(0.01)

    # Add key3: should evict key2 (older access time)
    cache.set("key3", "value3", ttl=60)

    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None


# ============================================================================
# TEST GROUP 8: THREAD SAFETY (2 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
def test_cache_thread_safe_set_get():
    """Verify cache is thread-safe for concurrent set/get"""
    cache = CacheLayer()
    errors = []

    def worker(thread_id):
        try:
            for i in range(100):
                key = f"thread_{thread_id}_key_{i}"
                value = f"value_{i}"
                cache.set(key, value, ttl=60)
                result = cache.get(key)
                assert result == value
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


@pytest.mark.unit
@pytest.mark.threading
def test_cache_thread_safe_clear():
    """Verify cache clear is thread-safe"""
    cache = CacheLayer()
    errors = []

    # Populate cache
    for i in range(50):
        cache.set(f"key_{i}", f"value_{i}", ttl=60)

    def worker():
        try:
            for i in range(10):
                cache.clear(f"key_{i}")
                cache.get(f"key_{i}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker) for _ in range(3)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


# ============================================================================
# TEST GROUP 9: QUERY CACHE MANAGER (5 tests)
# ============================================================================

@pytest.mark.unit
def test_query_cache_manager_get_users_list():
    """Verify QueryCacheManager caches user list"""
    manager = QueryCacheManager()
    fetch_func = Mock(return_value=["user1", "user2"])

    # First call: cache miss, calls fetch_func
    result1 = manager.get_users_list(fetch_func)
    assert result1 == ["user1", "user2"]
    assert fetch_func.call_count == 1

    # Second call: cache hit, doesn't call fetch_func
    result2 = manager.get_users_list(fetch_func)
    assert result2 == ["user1", "user2"]
    assert fetch_func.call_count == 1  # Still 1


@pytest.mark.unit
def test_query_cache_manager_get_user_detail():
    """Verify QueryCacheManager caches user detail"""
    manager = QueryCacheManager()
    fetch_func = Mock(return_value={"id": 1, "name": "John"})

    result1 = manager.get_user_detail("user1", fetch_func)
    assert result1 == {"id": 1, "name": "John"}

    result2 = manager.get_user_detail("user1", fetch_func)
    assert result2 == {"id": 1, "name": "John"}
    assert fetch_func.call_count == 1


@pytest.mark.unit
def test_query_cache_manager_invalidate_users():
    """Verify invalidating user list cache"""
    manager = QueryCacheManager()
    fetch_func = Mock(return_value=["user1"])

    manager.get_users_list(fetch_func)
    assert fetch_func.call_count == 1

    manager.invalidate_users_list()

    manager.get_users_list(fetch_func)
    assert fetch_func.call_count == 2  # Called again after invalidation


@pytest.mark.unit
def test_query_cache_manager_invalidate_user_detail():
    """Verify invalidating specific user detail"""
    manager = QueryCacheManager()
    fetch_func = Mock(return_value={"id": 1})

    manager.get_user_detail("user1", fetch_func)
    assert fetch_func.call_count == 1

    manager.invalidate_user_detail("user1")

    manager.get_user_detail("user1", fetch_func)
    assert fetch_func.call_count == 2


@pytest.mark.unit
def test_query_cache_manager_invalidate_all_user_details():
    """Verify invalidating all user details"""
    manager = QueryCacheManager()
    fetch_func = Mock(return_value={"id": 1})

    manager.get_user_detail("user1", fetch_func)
    manager.get_user_detail("user2", fetch_func)

    count = manager.invalidate_all_user_details()

    assert count == 2


# ============================================================================
# TEST GROUP 10: DECORATOR (2 tests)
# ============================================================================

@pytest.mark.unit
def test_cached_decorator():
    """Verify @cached decorator works"""
    call_count = [0]

    @cached(ttl=60)
    def get_data(key):
        call_count[0] += 1
        return f"data_{key}"

    # First call: executes function
    result1 = get_data("test")
    assert result1 == "data_test"
    assert call_count[0] == 1

    # Second call: uses cache
    result2 = get_data("test")
    assert result2 == "data_test"
    assert call_count[0] == 1  # Not called again


@pytest.mark.unit
def test_cached_decorator_different_args():
    """Verify decorator creates separate cache entries for different args"""
    call_count = [0]

    @cached(ttl=60)
    def get_data(key):
        call_count[0] += 1
        return f"data_{key}"

    result1 = get_data("key1")
    result2 = get_data("key2")

    assert result1 == "data_key1"
    assert result2 == "data_key2"
    assert call_count[0] == 2  # Different args = separate cache entries


# ============================================================================
# TEST GROUP 11: CACHE ENTRY (2 tests)
# ============================================================================

@pytest.mark.unit
def test_cache_entry_creation():
    """Verify CacheEntry creation"""
    entry = CacheEntry(
        value="test_value",
        created_at=time.time(),
        ttl_seconds=60
    )

    assert entry.value == "test_value"
    assert entry.ttl_seconds == 60
    assert entry.hit_count == 0


@pytest.mark.unit
def test_cache_metrics_creation():
    """Verify CacheMetrics creation"""
    metrics = CacheMetrics(total_hits=10, total_misses=5)

    assert metrics.total_hits == 10
    assert metrics.total_misses == 5
    assert metrics.hit_rate == 66.66666666666666  # 10 / (10+5)
