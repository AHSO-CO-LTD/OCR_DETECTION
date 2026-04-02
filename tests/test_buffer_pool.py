"""
Unit tests for BufferPool (Memory-Efficient Buffer Reuse).

Coverage targets: 90%+ for buffer management and circular queue logic.
Tests verify: buffer allocation, reuse, metrics, thread safety.
"""

import pytest
import numpy as np
import threading
import time
from unittest.mock import Mock, patch

from lib.BufferPool import BufferPool, BufferPoolFactory, BufferMetrics


# ============================================================================
# TEST GROUP 1: INITIALIZATION (3 tests)
# ============================================================================

@pytest.mark.unit
def test_buffer_pool_init_default_config():
    """
    Verify BufferPool initializes with correct default configuration.
    """
    pool = BufferPool()

    # Verify default values
    assert pool.height == 1536
    assert pool.width == 2048
    assert pool.channels == 3
    assert pool.pool_size == 5
    assert pool.dtype == np.uint8

    # Verify memory calculation
    expected_bytes = 1536 * 2048 * 3
    assert pool.bytes_per_frame == expected_bytes
    assert pool.total_pool_memory_mb > 0


@pytest.mark.unit
def test_buffer_pool_init_custom_config():
    """
    Verify BufferPool accepts custom configuration.
    """
    pool = BufferPool(height=720, width=1280, channels=3, pool_size=10)

    assert pool.height == 720
    assert pool.width == 1280
    assert pool.pool_size == 10


@pytest.mark.unit
def test_buffer_pool_init_creates_buffers():
    """
    Verify BufferPool pre-allocates all buffers.
    """
    pool = BufferPool(height=100, width=100, pool_size=5)

    # Verify all buffers are allocated
    assert len(pool._buffers) == 5
    for buffer in pool._buffers:
        assert isinstance(buffer, np.ndarray)
        assert buffer.shape == (100, 100, 3)
        assert buffer.dtype == np.uint8


# ============================================================================
# TEST GROUP 2: GET NEXT BUFFER & CIRCULAR QUEUE (4 tests)
# ============================================================================

@pytest.mark.unit
def test_get_next_buffer_cycles():
    """
    Verify get_next_buffer cycles through all buffers.
    """
    pool = BufferPool(height=50, width=50, pool_size=3)

    # Get 6 buffers (2 full cycles)
    buffers = [pool.get_next_buffer() for _ in range(6)]

    # Should cycle: 0 → 1 → 2 → 0 → 1 → 2
    assert buffers[0] is pool._buffers[0]
    assert buffers[1] is pool._buffers[1]
    assert buffers[2] is pool._buffers[2]
    assert buffers[3] is pool._buffers[0]  # Cycles back
    assert buffers[4] is pool._buffers[1]
    assert buffers[5] is pool._buffers[2]


@pytest.mark.unit
def test_get_next_buffer_returns_numpy_array():
    """
    Verify get_next_buffer returns valid numpy array.
    """
    pool = BufferPool(height=100, width=100, pool_size=2)

    buffer = pool.get_next_buffer()

    assert isinstance(buffer, np.ndarray)
    assert buffer.shape == (100, 100, 3)
    assert buffer.dtype == np.uint8


@pytest.mark.unit
def test_get_current_buffer():
    """
    Verify get_current_buffer returns current without advancing.
    """
    pool = BufferPool(pool_size=3)

    # Get next advances index
    buf1 = pool.get_next_buffer()
    assert pool._current_index == 1

    # Get current doesn't advance
    buf_curr = pool.get_current_buffer()
    assert pool._current_index == 1

    # Current should be next buffer (index 1)
    assert buf_curr is pool._buffers[1]


@pytest.mark.unit
def test_get_buffer_by_index():
    """
    Verify get_buffer_by_index retrieves specific buffer.
    """
    pool = BufferPool(pool_size=5)

    buf2 = pool.get_buffer_by_index(2)
    assert buf2 is pool._buffers[2]

    # Invalid indices return None
    assert pool.get_buffer_by_index(-1) is None
    assert pool.get_buffer_by_index(10) is None


# ============================================================================
# TEST GROUP 3: COPY DATA TO BUFFER (3 tests)
# ============================================================================

@pytest.mark.unit
def test_copy_data_to_buffer_success():
    """
    Verify data copying works correctly.
    """
    pool = BufferPool(height=100, width=100, pool_size=2)

    # Create source data
    src_data = np.full((100, 100, 3), 42, dtype=np.uint8)

    # Copy to buffer
    result = pool.copy_data_to_buffer(src_data)

    assert result is True
    # First buffer should now contain 42
    assert np.all(pool._buffers[0] == 42)


@pytest.mark.unit
def test_copy_data_to_buffer_wrong_shape():
    """
    Verify shape validation in copy_data_to_buffer.
    """
    pool = BufferPool(height=100, width=100, pool_size=2)

    # Wrong shape data
    wrong_shape = np.zeros((50, 50, 3))

    result = pool.copy_data_to_buffer(wrong_shape)

    assert result is False


@pytest.mark.unit
def test_copy_data_to_buffer_specific_index():
    """
    Verify copying to specific buffer index.
    """
    pool = BufferPool(height=100, width=100, pool_size=3)

    src_data = np.full((100, 100, 3), 99, dtype=np.uint8)

    # Copy to buffer index 2
    result = pool.copy_data_to_buffer(src_data, buffer_index=2)

    assert result is True
    assert np.all(pool._buffers[2] == 99)


# ============================================================================
# TEST GROUP 4: METRICS TRACKING (4 tests)
# ============================================================================

@pytest.mark.unit
def test_metrics_reuse_counting():
    """
    Verify metrics count buffer reuses.
    """
    pool = BufferPool(pool_size=2)

    # Get 5 buffers (should count reuses)
    for _ in range(5):
        pool.get_next_buffer()

    metrics = pool.get_metrics()

    # 5 get_next_buffer calls = 5 reuses counted
    assert metrics["total_reuses"] == 5


@pytest.mark.unit
def test_metrics_per_buffer_reuse():
    """
    Verify metrics track reuses per buffer.
    """
    pool = BufferPool(pool_size=3)

    # Get 6 buffers: 0, 1, 2, 0, 1, 2
    for _ in range(6):
        pool.get_next_buffer()

    metrics = pool.get_metrics()

    # Each buffer should have 2 reuses
    assert metrics["reuse_counts"] == [2, 2, 2]


@pytest.mark.unit
def test_metrics_memory_saved():
    """
    Verify memory saved calculation.
    """
    pool = BufferPool(height=100, width=100, channels=3, pool_size=5)

    # Do 100 reuses
    for _ in range(100):
        pool.get_next_buffer()

    metrics = pool.get_metrics()

    # 100 reuses should show memory saved
    assert "memory_saved_mb" in metrics


@pytest.mark.unit
def test_reset_metrics():
    """
    Verify reset_metrics clears all statistics.
    """
    pool = BufferPool(pool_size=3)

    # Generate some metrics
    for _ in range(10):
        pool.get_next_buffer()

    assert pool._metrics.reuses == 10

    # Reset
    pool.reset_metrics()

    assert pool._metrics.reuses == 0
    assert all(count == 0 for count in pool._reuse_counts)


# ============================================================================
# TEST GROUP 5: GET METRICS & INFO (2 tests)
# ============================================================================

@pytest.mark.unit
def test_get_metrics_returns_dict():
    """
    Verify get_metrics returns valid dictionary.
    """
    pool = BufferPool()

    metrics = pool.get_metrics()

    assert isinstance(metrics, dict)
    assert "pool_size" in metrics
    assert "buffer_shape" in metrics
    assert "total_pool_memory_mb" in metrics
    assert "total_reuses" in metrics


@pytest.mark.unit
def test_get_pool_info_string():
    """
    Verify get_pool_info returns formatted string.
    """
    pool = BufferPool()

    info = pool.get_pool_info()

    assert isinstance(info, str)
    assert "BufferPool Info" in info
    assert "Pool Size" in info
    assert "Total Pool Memory" in info


# ============================================================================
# TEST GROUP 6: THREAD SAFETY (2 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
def test_buffer_pool_thread_safe_get_next():
    """
    Verify get_next_buffer is thread-safe.
    """
    pool = BufferPool(pool_size=10)
    results = []

    def worker():
        for _ in range(100):
            buf = pool.get_next_buffer()
            results.append(id(buf))

    # Create 3 threads
    threads = [threading.Thread(target=worker) for _ in range(3)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 3 threads × 100 calls = 300 total calls
    assert len(results) == 300

    # All returned buffer IDs should be from the pool
    original_buffer_ids = {id(b) for b in pool._buffers}
    assert all(buf_id in original_buffer_ids for buf_id in results)


@pytest.mark.unit
@pytest.mark.threading
def test_buffer_pool_thread_safe_copy_data():
    """
    Verify copy_data_to_buffer is thread-safe.
    """
    pool = BufferPool(height=50, width=50, pool_size=5)
    errors = []

    def worker(thread_id):
        try:
            for i in range(50):
                data = np.full((50, 50, 3), thread_id * 10 + i, dtype=np.uint8)
                pool.copy_data_to_buffer(data)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


# ============================================================================
# TEST GROUP 7: STATIC UTILITY METHODS (2 tests)
# ============================================================================

@pytest.mark.unit
def test_calculate_pool_size():
    """
    Verify pool size calculation logic.
    """
    # At 30 FPS with 100ms inference
    size = BufferPool.calculate_pool_size(fps=30, inference_time_ms=100)

    # Should be at least 5
    assert size >= 5

    # At 60 FPS with 100ms inference (more frames queue up)
    size_60 = BufferPool.calculate_pool_size(fps=60, inference_time_ms=100)

    # Should be larger than 30 FPS case
    assert size_60 >= size


@pytest.mark.unit
def test_calculate_memory_usage():
    """
    Verify memory usage calculation.
    """
    memory_mb = BufferPool.calculate_memory_usage(
        height=1536, width=2048, channels=3, pool_size=5
    )

    # Manually calculate: 1536 * 2048 * 3 * 5 bytes / (1024*1024)
    expected = (1536 * 2048 * 3 * 5) / (1024 * 1024)

    assert abs(memory_mb - expected) < 0.01  # Allow small float error


# ============================================================================
# TEST GROUP 8: BUFFER POOL FACTORY (3 tests)
# ============================================================================

@pytest.mark.unit
def test_factory_create_for_resolution_basler_2k():
    """
    Verify factory creates pool for Basler 2K.
    """
    pool = BufferPoolFactory.create_for_resolution('BASLER_2K', pool_size=5)

    assert pool.height == 1536
    assert pool.width == 2048
    assert pool.pool_size == 5


@pytest.mark.unit
def test_factory_create_for_resolution_auto_pool_size():
    """
    Verify factory auto-calculates pool size.
    """
    pool = BufferPoolFactory.create_for_resolution(
        'FHD', pool_size=None, fps=30, inference_ms=100
    )

    assert pool.pool_size >= 5


@pytest.mark.unit
def test_factory_create_custom():
    """
    Verify factory creates custom pool.
    """
    pool = BufferPoolFactory.create_custom(
        height=720, width=1280, channels=3, pool_size=3
    )

    assert pool.height == 720
    assert pool.width == 1280
    assert pool.pool_size == 3


# ============================================================================
# TEST GROUP 9: BUFFER METRICS DATACLASS (1 test)
# ============================================================================

@pytest.mark.unit
def test_buffer_metrics_creation():
    """
    Verify BufferMetrics dataclass works correctly.
    """
    metrics = BufferMetrics(reuses=100, allocations=1, peak_memory_mb=47.5)

    assert metrics.reuses == 100
    assert metrics.allocations == 1
    assert metrics.peak_memory_mb == 47.5


# ============================================================================
# TEST GROUP 10: MEMORY EFFICIENCY VERIFICATION (2 tests)
# ============================================================================

@pytest.mark.unit
def test_fixed_memory_footprint():
    """
    Verify pool memory footprint is fixed regardless of usage.
    """
    pool = BufferPool(height=100, width=100, pool_size=5)

    initial_memory = pool.total_pool_memory_mb

    # Do many reuses
    for _ in range(10000):
        buf = pool.get_next_buffer()
        np.copyto(buf, np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))

    final_memory = pool.total_pool_memory_mb

    # Memory footprint should be identical
    assert initial_memory == final_memory


@pytest.mark.unit
def test_buffer_reuse_prevents_allocation():
    """
    Verify that reusing buffers doesn't create new allocations.
    """
    pool = BufferPool(height=100, width=100, pool_size=3)

    # Get references to original buffers
    original_ids = [id(buf) for buf in pool._buffers]

    # Get 100 buffers (many cycles)
    obtained_ids = [id(pool.get_next_buffer()) for _ in range(100)]

    # All obtained should be from original set (no new allocations)
    assert all(oid in original_ids for oid in obtained_ids)
