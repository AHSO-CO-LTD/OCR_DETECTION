"""
Unit tests for QTimerPollHandler.

Coverage targets: 85%+ for polling handler.
Tests verify: Timer functionality, adaptive intervals, error handling, statistics.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtCore import QTimer, Qt

from lib.QTimerPollHandler import (
    QTimerPollHandler,
    AdaptiveQTimerPollHandler,
    BatchQTimerPollHandler
)


@pytest.fixture(autouse=True)
def qapp_fixture(qapp):
    """Ensure QApplication is available for all tests"""
    return qapp


class TestQTimerPollHandlerBasic:
    """Test basic QTimerPollHandler functionality"""

    def teardown_method(self):
        """Clean up after each test"""
        # Force Qt event loop processing to catch any pending exceptions
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_init_default(self):
        """Verify initialization with defaults"""
        handler = QTimerPollHandler()

        assert handler.poll_interval_ms == 2
        assert handler.is_running is False
        assert handler._poll_count == 0
        assert handler._error_count == 0
        assert handler.timer is not None

    def test_init_custom_interval(self):
        """Verify initialization with custom interval"""
        handler = QTimerPollHandler(poll_interval_ms=5)

        assert handler.poll_interval_ms == 5

    def test_start_stop(self):
        """Verify start/stop functionality"""
        handler = QTimerPollHandler()

        assert handler.is_running is False
        handler.start()
        assert handler.is_running is True

        handler.stop()
        assert handler.is_running is False

    def test_multiple_start_stop(self):
        """Verify multiple start/stop cycles"""
        handler = QTimerPollHandler()

        for _ in range(3):
            handler.start()
            assert handler.is_running is True

            handler.stop()
            assert handler.is_running is False

    def test_is_active(self):
        """Verify is_active() method"""
        handler = QTimerPollHandler()

        assert handler.is_active() is False

        handler.start()
        assert handler.is_active() is True

        handler.stop()
        assert handler.is_active() is False


class TestQTimerPollHandlerStatistics:
    """Test statistics tracking"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_get_stats_initial(self):
        """Verify initial statistics"""
        handler = QTimerPollHandler()

        stats = handler.get_stats()

        assert stats['total_polls'] == 0
        assert stats['total_errors'] == 0
        assert stats['start_time'] is None
        assert stats['stop_time'] is None

    def test_poll_count_increments(self):
        """Verify poll count increments"""
        handler = QTimerPollHandler()
        handler.poll_tick.connect(lambda: None)

        handler.start()
        assert handler.get_poll_count() == 0

        # Simulate timer ticks
        for expected_count in range(1, 4):
            handler._on_timer_tick()
            assert handler.get_poll_count() == expected_count

    def test_error_count_increments(self):
        """Verify error count increments"""
        handler = QTimerPollHandler()

        # Connect signal that will raise exception
        def raise_error():
            raise ZeroDivisionError("test error")

        handler.poll_tick.connect(raise_error)
        handler.start()
        handler._on_timer_tick()

        assert handler.get_error_count() == 1

    def test_stats_after_stop(self):
        """Verify stats are recorded after stop"""
        handler = QTimerPollHandler()
        handler.poll_tick.connect(lambda: None)

        handler.start()
        handler._on_timer_tick()
        handler._on_timer_tick()
        handler.stop()

        stats = handler.get_stats()

        assert stats['total_polls'] == 2
        assert stats['start_time'] is not None
        assert stats['stop_time'] is not None


class TestQTimerPollHandlerInterval:
    """Test interval management"""

    def test_set_interval_when_stopped(self):
        """Verify set_interval works when stopped"""
        handler = QTimerPollHandler(poll_interval_ms=2)

        handler.set_interval(5)

        assert handler.poll_interval_ms == 5

    def test_set_interval_when_running(self):
        """Verify set_interval is ignored when running"""
        handler = QTimerPollHandler(poll_interval_ms=2)
        handler.start()

        handler.set_interval(5)

        # Should not change while running
        assert handler.poll_interval_ms == 2

        handler.stop()


class TestAdaptiveQTimerPollHandler:
    """Test adaptive interval adjustment"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_init_adaptive(self):
        """Verify adaptive handler initialization"""
        handler = AdaptiveQTimerPollHandler(
            base_interval_ms=2,
            min_interval_ms=1,
            max_interval_ms=100
        )

        assert handler.min_interval_ms == 1
        assert handler.max_interval_ms == 100
        assert handler.current_interval_ms == 2

    def test_speedup_on_success(self):
        """Verify interval decreases on success"""
        handler = AdaptiveQTimerPollHandler(
            base_interval_ms=10,
            min_interval_ms=1,
            max_interval_ms=100
        )

        handler.start()

        # Trigger SUCCESS_THRESHOLD successes
        for _ in range(handler.SUCCESS_THRESHOLD):
            handler._on_timer_tick()

        # Should have sped up (decreased interval)
        assert handler.current_interval_ms < 10

    def test_backoff_on_error(self):
        """Verify interval increases on error"""
        handler = AdaptiveQTimerPollHandler(
            base_interval_ms=2,
            min_interval_ms=1,
            max_interval_ms=100
        )

        # Connect signal that will raise exception
        def raise_error():
            raise RuntimeError("test error")

        handler.poll_tick.connect(raise_error)
        handler.start()
        initial_interval = handler.current_interval_ms

        # Trigger ERROR_THRESHOLD errors
        for _ in range(handler.ERROR_THRESHOLD):
            handler._on_timer_tick()

        # Should have backed off (increased interval)
        assert handler.current_interval_ms > initial_interval

    def test_min_max_limits(self):
        """Verify min/max interval limits are respected"""
        handler = AdaptiveQTimerPollHandler(
            base_interval_ms=50,
            min_interval_ms=5,
            max_interval_ms=200
        )

        handler.start()

        # Force many speedups (should hit min limit)
        for _ in range(100):
            handler._on_timer_tick()

        assert handler.current_interval_ms >= handler.min_interval_ms

        # Force backoff to hit max limit
        def raise_error():
            raise RuntimeError("test error")

        handler.poll_tick.connect(raise_error)
        for _ in range(100):
            handler._on_timer_tick()

        assert handler.current_interval_ms <= handler.max_interval_ms

    def test_get_current_interval(self):
        """Verify get_current_interval() returns correct value"""
        handler = AdaptiveQTimerPollHandler(base_interval_ms=3)

        assert handler.get_current_interval() == 3

        handler.current_interval_ms = 7
        assert handler.get_current_interval() == 7


class TestBatchQTimerPollHandler:
    """Test batch polling functionality"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_init_batch(self):
        """Verify batch handler initialization"""
        handler = BatchQTimerPollHandler(batch_size=5, poll_interval_ms=2)

        assert handler.batch_size == 5
        assert handler.get_queue_size() == 0

    def test_add_to_batch(self):
        """Verify items can be added to batch"""
        handler = BatchQTimerPollHandler(batch_size=3)

        handler.add_to_batch("item1")
        handler.add_to_batch("item2")
        handler.add_to_batch("item3")

        assert handler.get_queue_size() == 3

    def test_batch_processing(self):
        """Verify batch is processed correctly"""
        handler = BatchQTimerPollHandler(batch_size=2)

        handler.add_to_batch("item1")
        handler.add_to_batch("item2")
        handler.add_to_batch("item3")

        handler.start()

        # First tick processes batch of 2
        handler._on_timer_tick()

        # Queue should have 1 item left
        assert handler.get_queue_size() == 1

    def test_get_pending_batches(self):
        """Verify get_pending_batches() calculation"""
        handler = BatchQTimerPollHandler(batch_size=3)

        handler.add_to_batch("item1")
        handler.add_to_batch("item2")
        handler.add_to_batch("item3")
        handler.add_to_batch("item4")
        handler.add_to_batch("item5")
        handler.add_to_batch("item6")

        # 6 items / batch_size 3 = 2 complete batches
        assert handler.get_pending_batches() == 2


class TestQTimerPollSignals:
    """Test signal emission"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_poll_tick_signal(self):
        """Verify poll_tick signal is emitted"""
        handler = QTimerPollHandler()

        signal_received = []
        handler.poll_tick.connect(lambda: signal_received.append(True))

        handler.start()
        handler._on_timer_tick()

        assert len(signal_received) == 1

    def test_poll_error_signal(self):
        """Verify poll_error signal on exception"""
        handler = QTimerPollHandler()

        error_messages = []
        handler.poll_error.connect(lambda msg: error_messages.append(msg))

        def raise_division_error():
            raise ZeroDivisionError("integer division or modulo by zero")

        handler.poll_tick.connect(raise_division_error)
        handler.start()
        handler._on_timer_tick()

        assert len(error_messages) == 1
        assert "division" in error_messages[0].lower()


class TestQTimerPerformance:
    """Performance and timing tests"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_non_blocking_behavior(self):
        """Verify timer is non-blocking"""
        handler = QTimerPollHandler(poll_interval_ms=2)

        # Track timing
        times = []

        def track_time():
            times.append(time.time())

        handler.poll_tick.connect(track_time)
        handler.start()

        # Trigger multiple ticks
        for _ in range(3):
            handler._on_timer_tick()

        handler.stop()

        # Should have completed quickly (not blocked)
        if len(times) >= 2:
            elapsed = times[-1] - times[0]
            assert elapsed < 0.1  # Should be < 100ms for 3 ticks

    def test_multiple_handlers_concurrent(self):
        """Verify multiple handlers can run concurrently"""
        handler1 = QTimerPollHandler(poll_interval_ms=2)
        handler2 = QTimerPollHandler(poll_interval_ms=3)

        # Use simple no-op functions
        def noop():
            pass

        handler1.poll_tick.connect(noop)
        handler2.poll_tick.connect(noop)

        handler1.start()
        handler2.start()

        # Both should run
        assert handler1.is_active() is True
        assert handler2.is_active() is True

        # Trigger ticks
        handler1._on_timer_tick()
        handler2._on_timer_tick()

        assert handler1.get_poll_count() == 1
        assert handler2.get_poll_count() == 1

        handler1.stop()
        handler2.stop()


class TestQTimerIntegration:
    """Integration tests"""

    def teardown_method(self):
        """Clean up after each test"""
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def test_complete_workflow(self):
        """Test complete start-poll-stop workflow"""
        handler = QTimerPollHandler(poll_interval_ms=2)

        poll_data = []
        handler.poll_tick.connect(lambda: poll_data.append("polled"))

        handler.start()
        assert handler.is_running is True

        # Simulate 5 polls
        for _ in range(5):
            handler._on_timer_tick()

        assert handler.get_poll_count() == 5
        assert len(poll_data) == 5

        handler.stop()
        assert handler.is_running is False

        stats = handler.get_stats()
        assert stats['total_polls'] == 5

    def test_error_recovery(self):
        """Test recovery from errors"""
        handler = QTimerPollHandler()

        attempt = [0]

        def failing_then_success():
            attempt[0] += 1
            if attempt[0] < 3:
                raise RuntimeError("Test error")

        handler.poll_tick.connect(failing_then_success)
        handler.start()

        # First two attempts fail
        handler._on_timer_tick()
        handler._on_timer_tick()

        # Third attempt succeeds
        handler._on_timer_tick()

        assert handler.get_error_count() == 2
        assert handler.get_poll_count() == 3

        handler.stop()
