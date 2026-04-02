"""
CacheLayer: Query Result Caching with TTL

Eliminates redundant database queries by caching results with configurable
Time-To-Live (TTL). Significantly reduces database load and latency.

Problem: Current implementation queries DB on every request
  - User list loaded each time Authentication window opens
  - User details queried on every detail load
  - No caching = 50-200ms latency per query
  - Multiple identical queries in quick succession

Solution: Time-based cache with automatic expiration
  - User list: 60s TTL (doesn't change frequently)
  - User details: 30s TTL (infrequent updates)
  - Settings: 5s TTL (cached config values)

Expected Impact:
  - Database latency: 150ms → 5ms (97% reduction for cache hits)
  - Query reduction: 40% fewer roundtrips
  - Load time: First load 150ms, subsequent <5ms (via cache)
"""

import time
import threading
from typing import Any, Optional, Callable, Dict, Tuple
from functools import wraps
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    value: Any
    created_at: float
    ttl_seconds: int
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has exceeded TTL"""
        return (time.time() - self.created_at) > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_hits: int = 0
    total_misses: int = 0
    total_evictions: int = 0
    current_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total = self.total_hits + self.total_misses
        if total == 0:
            return 0.0
        return (self.total_hits / total) * 100


class CacheLayer:
    """
    TTL-based query result cache.

    Stores query results with automatic expiration. Thread-safe using RLock.

    Usage:
    ```python
    cache = CacheLayer()

    # Cache a query result with 60s TTL
    cache.set("user_list", user_data, ttl=60)

    # Retrieve (returns None if expired)
    data = cache.get("user_list")
    if data is None:
        # Cache miss, query database
        data = User.get_column("UserName")
        cache.set("user_list", data, ttl=60)

    # Check if key exists and is valid
    if cache.exists("user_list"):
        data = cache.get("user_list")

    # Clear specific key or all
    cache.clear("user_list")
    cache.clear_all()
    ```
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize cache layer.

        Args:
            max_size: Maximum number of cache entries before LRU eviction
        """
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._metrics = CacheMetrics()
        self._access_times: Dict[str, float] = {}  # For LRU tracking

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 60)
        """
        with self._lock:
            # Check if need to evict (LRU)
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl,
                hit_count=0
            )
            self._access_times[key] = time.time()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Returns None if:
        - Key doesn't exist
        - Entry has expired

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._lock:
            if key not in self._cache:
                self._metrics.total_misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                del self._access_times[key]
                self._metrics.total_misses += 1
                return None

            # Cache hit
            entry.hit_count += 1
            self._metrics.total_hits += 1
            self._access_times[key] = time.time()

            return entry.value

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and valid
        """
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                del self._access_times[key]
                return False

            return True

    def clear(self, key: str) -> None:
        """
        Clear a specific cache entry.

        Args:
            key: Cache key to clear
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]

    def clear_all(self) -> None:
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern (prefix match).

        Args:
            pattern: Key prefix to match

        Returns:
            Number of keys cleared
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
            return len(keys_to_delete)

    def get_entry_info(self, key: str) -> Optional[dict]:
        """
        Get detailed information about a cache entry.

        Args:
            key: Cache key

        Returns:
            Dictionary with entry metadata or None
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            return {
                "key": key,
                "value_type": type(entry.value).__name__,
                "age_seconds": entry.age_seconds(),
                "ttl_seconds": entry.ttl_seconds,
                "is_expired": entry.is_expired(),
                "hit_count": entry.hit_count,
                "time_to_expiry": max(0, entry.ttl_seconds - entry.age_seconds())
            }

    def get_metrics(self) -> dict:
        """
        Get cache performance metrics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_hits = self._metrics.total_hits
            total_misses = self._metrics.total_misses

            return {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate_percent": f"{self._metrics.hit_rate:.1f}%",
                "total_evictions": self._metrics.total_evictions,
                "size_percent": f"{(len(self._cache) / self.max_size * 100):.1f}%"
            }

    def get_stats(self) -> str:
        """
        Get human-readable cache statistics.

        Returns:
            Formatted string with cache info
        """
        metrics = self.get_metrics()

        return f"""
CacheLayer Stats:
  Cache Size: {metrics['current_size']}/{metrics['max_size']} ({metrics['size_percent']})
  Hit Rate: {metrics['hit_rate_percent']} ({metrics['total_hits']} hits, {metrics['total_misses']} misses)
  Evictions: {metrics['total_evictions']}
""".strip()

    def _evict_lru(self) -> None:
        """
        Evict Least Recently Used entry.

        Called internally when cache reaches max size.
        """
        if not self._access_times:
            return

        # Find key with oldest access time
        lru_key = min(self._access_times, key=self._access_times.get)

        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._metrics.total_evictions += 1

    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        with self._lock:
            self._metrics = CacheMetrics()


def cached(ttl: int = 60):
    """
    Decorator for caching function results with TTL.

    Usage:
    ```python
    cache = CacheLayer()

    @cached(ttl=60)
    def get_users():
        return User.get_column("UserName")

    # First call: queries DB
    users = get_users()

    # Second call (within 60s): returns cached result
    users = get_users()

    # After 60s: queries DB again
    ```
    """
    cache_instance = CacheLayer()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and args
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss: call function
            result = func(*args, **kwargs)

            # Store in cache
            cache_instance.set(cache_key, result, ttl=ttl)

            return result

        # Attach cache instance to wrapper for external access
        wrapper.cache = cache_instance

        return wrapper

    return decorator


class QueryCacheManager:
    """
    High-level manager for query caching with predefined cache strategies.

    Provides convenient caching for common query patterns:
    - User list: 60s TTL
    - User details: 30s TTL
    - Settings: 5s TTL
    """

    def __init__(self):
        """Initialize query cache manager"""
        self.cache = CacheLayer(max_size=1000)

        # Cache key prefixes
        self.USERS_LIST = "users:list"
        self.USER_DETAIL = "user:detail"
        self.SETTINGS = "settings"

        # Default TTLs
        self.TTL_USERS_LIST = 60  # 1 minute
        self.TTL_USER_DETAIL = 30  # 30 seconds
        self.TTL_SETTINGS = 5  # 5 seconds

    def get_users_list(self, fetch_func) -> list:
        """
        Get cached user list or fetch from DB.

        Args:
            fetch_func: Function to call if cache miss (e.g., User.get_column)

        Returns:
            List of users
        """
        if self.cache.exists(self.USERS_LIST):
            return self.cache.get(self.USERS_LIST)

        # Cache miss: fetch from DB
        users = fetch_func()
        self.cache.set(self.USERS_LIST, users, ttl=self.TTL_USERS_LIST)

        return users

    def get_user_detail(self, user_id: str, fetch_func) -> Optional[dict]:
        """
        Get cached user detail or fetch from DB.

        Args:
            user_id: User identifier
            fetch_func: Function to call if cache miss

        Returns:
            User detail dict or None
        """
        key = f"{self.USER_DETAIL}:{user_id}"

        if self.cache.exists(key):
            return self.cache.get(key)

        # Cache miss: fetch from DB
        user = fetch_func(user_id)
        if user:
            self.cache.set(key, user, ttl=self.TTL_USER_DETAIL)

        return user

    def get_settings(self, fetch_func) -> dict:
        """
        Get cached settings or fetch from config.

        Args:
            fetch_func: Function to call if cache miss

        Returns:
            Settings dictionary
        """
        if self.cache.exists(self.SETTINGS):
            return self.cache.get(self.SETTINGS)

        # Cache miss: fetch from config
        settings = fetch_func()
        self.cache.set(self.SETTINGS, settings, ttl=self.TTL_SETTINGS)

        return settings

    def invalidate_users_list(self) -> None:
        """Invalidate user list cache (call after user changes)"""
        self.cache.clear(self.USERS_LIST)

    def invalidate_user_detail(self, user_id: str) -> None:
        """Invalidate specific user detail cache"""
        key = f"{self.USER_DETAIL}:{user_id}"
        self.cache.clear(key)

    def invalidate_all_user_details(self) -> None:
        """Invalidate all user detail caches"""
        count = self.cache.clear_pattern(self.USER_DETAIL)
        return count

    def invalidate_settings(self) -> None:
        """Invalidate settings cache (call after config change)"""
        self.cache.clear(self.SETTINGS)

    def get_stats(self) -> str:
        """Get cache manager statistics"""
        return self.cache.get_stats()
