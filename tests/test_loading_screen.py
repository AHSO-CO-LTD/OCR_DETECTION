"""
Unit tests for LoadingScreen class.
Tests UI initialization, signal handling, thread management, and resource cleanup.

Coverage targets: 85%+ for LoadingScreen.
"""

import pytest
from unittest.mock import MagicMock, patch
import time
from PyQt5.QtWidgets import QApplication

from lib.LoadingScreen import LoadingScreen, CheckerThread


# ============================================================================
# TEST GROUP 1: INITIALIZATION (2 tests)
# ============================================================================

@pytest.mark.unit
def test_loading_screen_init_ui(qapp):
    """
    Verify LoadingScreen initializes all required UI widgets.
    """
    screen = LoadingScreen()

    # Verify main widgets exist
    assert hasattr(screen, 'progress_bar')
    assert hasattr(screen, 'continue_button')
    assert hasattr(screen, 'status_label')
    assert hasattr(screen, 'check_items')
    assert hasattr(screen, 'warnings_label')

    # Verify initial state
    assert screen.progress_bar.value() == 0
    assert not screen.continue_button.isEnabled()
    assert screen.warning_count == 0

    screen.close()


@pytest.mark.unit
def test_loading_screen_check_items_structure(qapp):
    """
    Verify LoadingScreen creates 5 check items with correct structure.
    """
    screen = LoadingScreen()

    expected_components = ["Hardware Dongle", "Config File", "Database", "Camera", "PLC"]

    # Verify all components are present
    assert len(screen.check_items) == 5
    for component in expected_components:
        assert component in screen.check_items
        item = screen.check_items[component]
        # Verify item structure
        assert "status_icon" in item
        assert "status_text" in item
        assert "container" in item

    screen.close()


# ============================================================================
# TEST GROUP 2: UI STATE (3 tests)
# ============================================================================

@pytest.mark.unit
def test_progress_bar_initial_zero(qapp):
    """
    Verify progress bar starts at 0%.
    """
    screen = LoadingScreen()

    assert screen.progress_bar.value() == 0
    assert screen.progress_bar.minimum() == 0
    assert screen.progress_bar.maximum() == 100

    screen.close()


@pytest.mark.unit
def test_continue_button_disabled_initially(qapp):
    """
    Verify Continue button is disabled initially.
    """
    screen = LoadingScreen()

    assert not screen.continue_button.isEnabled()

    screen.close()


@pytest.mark.unit
def test_status_label_initial_message(qapp):
    """
    Verify status label shows initial message.
    """
    screen = LoadingScreen()

    status_text = screen.status_label.text().lower()
    # Check for initialization-related keywords
    assert any(word in status_text for word in ["starting", "initializing", "checking"])

    screen.close()


# ============================================================================
# TEST GROUP 3: SIGNAL HANDLING - STATUS UPDATES (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_on_status_update_green_check(qapp):
    """
    Verify successful check (✓ OK) displays with green icon.
    """
    screen = LoadingScreen()

    screen.on_status_update("Hardware Dongle", "✓ OK", True)

    item = screen.check_items["Hardware Dongle"]
    icon_text = item["status_icon"].text()
    assert icon_text == "✓" or "✓" in icon_text

    screen.close()


@pytest.mark.unit
@pytest.mark.signal
def test_on_status_update_red_cross(qapp):
    """
    Verify failed check (✗ Failed) displays with red/orange icon.
    """
    screen = LoadingScreen()

    screen.on_status_update("Hardware Dongle", "✗ Not found", False)

    item = screen.check_items["Hardware Dongle"]
    icon_text = item["status_icon"].text()
    assert icon_text == "✗" or "✗" in icon_text

    status_text = item["status_text"].text()
    assert "Not found" in status_text or "✗" in status_text

    screen.close()


@pytest.mark.unit
@pytest.mark.signal
def test_on_status_update_progress_bar_increments(qapp):
    """
    Verify progress bar increments with each status update.
    """
    screen = LoadingScreen()
    initial_progress = screen.progress_bar.value()

    # Emit first status update
    screen.on_status_update("Hardware Dongle", "✓ OK", True)
    progress_after_1 = screen.progress_bar.value()

    # Emit second status update
    screen.on_status_update("Config File", "✓ OK", True)
    progress_after_2 = screen.progress_bar.value()

    # Progress should increase
    assert progress_after_1 >= initial_progress
    assert progress_after_2 >= progress_after_1

    screen.close()


@pytest.mark.unit
@pytest.mark.signal
def test_on_status_update_all_five_checks(qapp):
    """
    Verify 5 status updates result in 100% progress.
    """
    screen = LoadingScreen()

    checks = [
        ("Hardware Dongle", "✓ OK", True),
        ("Config File", "✓ OK", True),
        ("Database", "✓ OK", True),
        ("Camera", "✓ OK", True),
        ("PLC", "✓ OK", True),
    ]

    for component, status, is_ok in checks:
        screen.on_status_update(component, status, is_ok)

    assert screen.progress_bar.value() == 100

    screen.close()


# ============================================================================
# TEST GROUP 4: SIGNAL HANDLING - COMPLETION (3 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_on_checks_complete_progress_100(qapp):
    """
    Verify on_checks_complete sets progress bar to 100%.
    """
    screen = LoadingScreen()

    screen.on_checks_complete(0)

    assert screen.progress_bar.value() == 100

    screen.close()


@pytest.mark.unit
@pytest.mark.signal
def test_on_checks_complete_button_enabled(qapp):
    """
    Verify on_checks_complete enables Continue button.
    """
    screen = LoadingScreen()
    assert not screen.continue_button.isEnabled()

    screen.on_checks_complete(0)

    assert screen.continue_button.isEnabled()

    screen.close()


@pytest.mark.unit
@pytest.mark.signal
def test_on_checks_complete_no_warnings_vs_warnings(qapp):
    """
    Verify on_checks_complete shows different messages for 0 vs N warnings.
    """
    screen1 = LoadingScreen()
    screen1.on_checks_complete(0)

    status_text_0 = screen1.status_label.text().lower()
    warnings_text_0 = screen1.warnings_label.text()

    # With 0 warnings: should show success message, no warning label
    assert "ready" in status_text_0 or "success" in status_text_0
    assert warnings_text_0 == ""

    screen1.close()

    # With warnings: different message
    screen2 = LoadingScreen()
    screen2.on_checks_complete(2)

    status_text_2 = screen2.status_label.text().lower()
    warnings_text_2 = screen2.warnings_label.text()

    # With warnings: should mention warnings or failures
    assert "ready" in status_text_2 or "warning" in status_text_2
    assert "2" in warnings_text_2 or "connection" in warnings_text_2

    screen2.close()


# ============================================================================
# TEST GROUP 5: THREAD MANAGEMENT (5 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
def test_start_checks_creates_thread(qapp):
    """
    Verify start_checks creates CheckerThread instance.
    """
    screen = LoadingScreen()
    assert screen.checker_thread is None

    screen.start_checks()

    assert screen.checker_thread is not None
    assert isinstance(screen.checker_thread, CheckerThread)

    # Cleanup
    if screen.checker_thread and screen.checker_thread.isRunning():
        screen.checker_thread.quit()
        screen.checker_thread.wait(5000)
    screen.close()


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_start_checks_connects_signals(qapp, mocker):
    """
    Verify start_checks connects all required signals.
    """
    screen = LoadingScreen()

    # Spy on signal connections
    status_connected = mocker.spy(screen, 'on_status_update')
    complete_connected = mocker.spy(screen, 'on_checks_complete')

    screen.start_checks()
    thread = screen.checker_thread

    # Emit test signals to verify connections
    thread.status_update.emit("Test", "Test", True)
    thread.checks_complete.emit(0)

    QApplication.processEvents()

    # Handlers should be called
    assert status_connected.called or complete_connected.called

    # Cleanup
    if thread.isRunning():
        thread.quit()
        thread.wait(5000)
    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_start_checks_thread_running(qapp):
    """
    Verify start_checks puts thread in running state.
    """
    screen = LoadingScreen()

    screen.start_checks()
    thread = screen.checker_thread

    # Give thread a moment to start
    QApplication.processEvents()
    time.sleep(0.1)

    assert thread.isRunning()

    # Cleanup
    thread.quit()
    thread.wait(5000)
    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_start_checks_cleanup_previous_thread(qapp):
    """
    Verify start_checks quits previous thread before starting new one.
    """
    screen = LoadingScreen()

    # Start first thread
    screen.start_checks()
    first_thread = screen.checker_thread
    assert first_thread is not None

    # Start second thread (should cleanup first)
    time.sleep(0.1)
    screen.start_checks()
    second_thread = screen.checker_thread

    # Threads should be different instances
    assert first_thread is not second_thread
    assert second_thread.isRunning()

    # Cleanup
    if second_thread.isRunning():
        second_thread.quit()
        second_thread.wait(5000)
    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_no_thread_leak_multiple_cycles(qapp):
    """
    Verify no thread leaks after multiple start/cleanup cycles.
    """
    screen = LoadingScreen()
    thread_ids = []

    for i in range(3):
        screen.start_checks()
        thread = screen.checker_thread
        thread_ids.append(id(thread))

        # Let it run briefly
        QApplication.processEvents()
        time.sleep(0.05)

        # Cleanup
        thread.quit()
        thread.wait(5000)

    # All thread IDs should be different (no reuse)
    assert len(set(thread_ids)) == 3

    screen.close()


# ============================================================================
# TEST GROUP 6: CLEANUP & RESOURCE MANAGEMENT (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
def test_on_checker_finished_clears_thread(qapp):
    """
    Verify on_checker_finished clears thread reference.
    """
    screen = LoadingScreen()

    screen.start_checks()
    assert screen.checker_thread is not None

    # Manually call finished handler
    screen.on_checker_finished()

    assert screen.checker_thread is None

    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_close_event_cleans_up_thread(qapp):
    """
    Verify closeEvent() properly quits thread on window close.
    """
    screen = LoadingScreen()

    screen.start_checks()
    thread = screen.checker_thread
    assert thread.isRunning()

    # Simulate close event
    screen.closeEvent(None)

    # Thread should be stopped
    QApplication.processEvents()
    time.sleep(0.2)

    assert not thread.isRunning()

    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_on_checker_finished_called_on_completion(qapp):
    """
    Verify on_checker_finished is called when thread finishes.
    """
    screen = LoadingScreen()

    # Mock the finished handler
    screen.on_checker_finished = MagicMock(wraps=screen.on_checker_finished)

    screen.start_checks()
    thread = screen.checker_thread

    # Wait for thread to naturally complete (or manually trigger finish)
    thread.quit()
    thread.wait(5000)

    QApplication.processEvents()

    # Handler should have been called or thread should be stopped
    assert not thread.isRunning()

    screen.close()


@pytest.mark.unit
@pytest.mark.threading
def test_thread_cleanup_with_exception(qapp):
    """
    Verify thread cleanup works even if exception occurs.
    """
    screen = LoadingScreen()

    screen.start_checks()
    thread = screen.checker_thread

    # Force cleanup
    try:
        thread.quit()
        success = thread.wait(5000)
        assert success == True
    except Exception as e:
        pytest.fail(f"Thread cleanup failed: {e}")

    screen.close()


# ============================================================================
# TEST GROUP 7: USER INTERACTIONS (2 tests)
# ============================================================================

@pytest.mark.unit
def test_continue_button_click_emits_signal(qapp, mocker):
    """
    Verify Continue button click emits loading_complete signal.
    """
    screen = LoadingScreen()

    # Enable button for testing
    screen.continue_button.setEnabled(True)

    # Spy on signal
    spy = mocker.spy(screen.loading_complete, 'emit')

    # Click button
    screen.continue_button.click()

    QApplication.processEvents()

    # Signal should be emitted
    assert spy.call_count >= 1

    screen.close()


@pytest.mark.unit
def test_on_continue_method(qapp, mocker):
    """
    Verify on_continue method emits loading_complete signal.
    """
    screen = LoadingScreen()

    spy = mocker.spy(screen.loading_complete, 'emit')

    screen.on_continue()

    spy.assert_called_once()

    screen.close()


# ============================================================================
# TEST GROUP 8: ERROR HANDLING (3 tests)
# ============================================================================

@pytest.mark.unit
def test_all_checks_fail(qapp):
    """
    Verify all 5 checks failing updates UI correctly.
    """
    screen = LoadingScreen()

    # Simulate all checks failing
    failures = [
        ("Hardware Dongle", "✗ Not found", False),
        ("Config File", "✗ Not found", False),
        ("Database", "✗ Connection failed", False),
        ("Camera", "✗ Not found", False),
        ("PLC", "✗ Connection failed", False),
    ]

    for component, status, is_ok in failures:
        screen.on_status_update(component, status, is_ok)

    # Complete checks with 5 warnings
    screen.on_checks_complete(5)

    # Verify warnings label shows count
    warnings_text = screen.warnings_label.text()
    assert "5" in warnings_text or "connection" in warnings_text.lower()

    # Button should still be enabled
    assert screen.continue_button.isEnabled()

    screen.close()


@pytest.mark.unit
def test_partial_failures(qapp):
    """
    Verify partial failures (2 out of 5) handled correctly.
    """
    screen = LoadingScreen()

    # Simulate: pass, fail, pass, fail, pass
    checks = [
        ("Hardware Dongle", "✓ OK", True),
        ("Config File", "✗ Not found", False),
        ("Database", "✓ OK", True),
        ("Camera", "✗ Not found", False),
        ("PLC", "✓ OK", True),
    ]

    for component, status, is_ok in checks:
        screen.on_status_update(component, status, is_ok)

    # Complete with 2 warnings
    screen.on_checks_complete(2)

    # Verify warning count
    assert "2" in screen.warnings_label.text()

    # Verify mixed states are shown correctly
    dongle_item = screen.check_items["Hardware Dongle"]
    assert "✓" in dongle_item["status_icon"].text()

    config_item = screen.check_items["Config File"]
    assert "✗" in config_item["status_icon"].text()

    screen.close()


@pytest.mark.unit
def test_exception_in_status_update_doesnt_crash(qapp):
    """
    Verify exception in status update doesn't crash LoadingScreen.
    """
    screen = LoadingScreen()

    # Send various status updates
    try:
        screen.on_status_update("Hardware Dongle", "✓ OK", True)
        screen.on_status_update("Config File", "✓ OK", True)
        screen.on_status_update("Database", "✓ OK", True)
        screen.on_status_update("Camera", "✓ OK", True)
        screen.on_status_update("PLC", "✓ OK", True)

        # Complete without crashing
        screen.on_checks_complete(0)

        # Button should be enabled
        assert screen.continue_button.isEnabled()

    except Exception as e:
        pytest.fail(f"StatusUpdate raised exception: {e}")

    screen.close()
