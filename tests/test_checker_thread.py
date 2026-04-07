"""
Unit tests for CheckerThread class.
Tests individual hardware/IO check methods and overall thread orchestration.

Coverage targets: 90%+ for CheckerThread.run() and check_* methods.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import time

from lib.LoadingScreen import CheckerThread


# ============================================================================
# TEST GROUP 1: INITIALIZATION (2 tests)
# ============================================================================

@pytest.mark.unit
def test_checker_thread_init_default_state(qapp):
    """
    Verify CheckerThread initializes with correct default state.
    """
    thread = CheckerThread()

    # Verify initial state
    assert thread.warning_count == 0
    assert thread.checks_completed == 0
    assert thread.config_path == "config.yaml"
    assert thread.total_checks == 5
    assert not thread.isRunning()


@pytest.mark.unit
def test_checker_thread_custom_config_path(qapp):
    """
    Verify CheckerThread accepts custom config path.
    """
    custom_path = "/custom/path/config.yaml"
    thread = CheckerThread(config_path=custom_path)

    assert thread.config_path == custom_path


# ============================================================================
# TEST GROUP 2: DONGLE CHECK (3 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_dongle_success(qapp, mock_dongle_success, signal_capture):
    """
    Test successful dongle check emits status update with ✓ OK.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_dongle()

    # Verify signal emitted with correct parameters
    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Hardware Dongle"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_dongle_failure(qapp, mock_dongle_failure, signal_capture):
    """
    Test failed dongle check emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_dongle()

    # Verify signal emitted and warning counted
    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Hardware Dongle"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_dongle_exception(qapp, mock_dongle_exception, signal_capture):
    """
    Test dongle exception is caught and warning_count incremented.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_dongle()

    # Verify exception handled
    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Hardware Dongle"
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


# ============================================================================
# TEST GROUP 3: CONFIG CHECK (3 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_config_exists(qapp, mock_config_file_exists, signal_capture):
    """
    Test config file existence check emits status update with ✓ OK.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_config()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Config File"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_config_missing(qapp, mock_config_file_missing, signal_capture):
    """
    Test missing config file emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_config()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Config File"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_config_exception(qapp, signal_capture, mocker):
    """
    Test os.path.exists exception is caught and handled.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    # Mock os.path.exists to raise exception
    mocker.patch("os.path.exists", side_effect=Exception("Permission denied"))

    thread._check_config()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Config File"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 4: DATABASE CHECK (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_database_connected(qapp, mock_db_config_loader, mock_pymysql_connected, signal_capture):
    """
    Test successful database connection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_database()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Database"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_operational_error(qapp, mock_db_config_loader, mock_pymysql_connection_error, signal_capture):
    """
    Test database connection failure emits status update with ✗ Connection failed.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_database()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Database"
    assert "connection failed" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_query_error(qapp, mock_db_config_loader, mock_pymysql_query_error, signal_capture):
    """
    Test database query failure emits status update.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_database()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Database"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_timeout(qapp, mock_db_config_loader, mock_pymysql_timeout, signal_capture):
    """
    Test database connection timeout emits status update with ✗ error message.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_database()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Database"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 5: CAMERA CHECK (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_found(qapp, mock_camera_sdk_found, signal_capture):
    """
    Test successful camera detection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_camera()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Camera"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_not_found(qapp, mock_camera_sdk_not_found, signal_capture):
    """
    Test no cameras found emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_camera()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Camera"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_sdk_not_installed(qapp, mock_camera_sdk_import_error, signal_capture):
    """
    Test SDK ImportError emits status update with SDK error message.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_camera()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Camera"
    assert "SDK" in status or "not installed" in status.lower()
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_exception(qapp, mock_camera_exception, signal_capture):
    """
    Test camera enumeration exception is caught and handled.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_camera()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "Camera"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 6: PLC CHECK (5 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_connected(qapp, mock_db_config_loader, mock_modbus_tcp_client_connected, signal_capture):
    """
    Test successful Modbus TCP connection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_plc()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "PLC"
    assert "OK" in status or "✓" in status or "Ready" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_connection_failed(qapp, mock_db_config_loader, mock_modbus_tcp_client_connection_failed, signal_capture):
    """
    Test Modbus TCP connection failure emits error status.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_plc()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_read_failed(qapp, mock_db_config_loader, mock_modbus_tcp_client_read_failed, signal_capture):
    """
    Test Modbus read failure emits error status.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_plc()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_read_timeout(qapp, mock_db_config_loader, mock_modbus_tcp_client_read_timeout, signal_capture):
    """
    Test Modbus read timeout emits error status with timeout message.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_plc()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_plc_non_tcp_protocol(qapp, mock_db_config_loader_non_tcp, signal_capture):
    """
    Test non-TCP protocol emits status update with Ready (manual config).
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread._check_plc()

    signal_capture.assert_emitted_once()
    component, status, is_ok = signal_capture.get_last_emission()
    assert component == "PLC"
    assert "Ready" in status or "manual" in status.lower()
    assert is_ok == True
    assert thread.warning_count == 0


# ============================================================================
# TEST GROUP 7: THREAD ORCHESTRATION (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
def test_run_executes_all_checks(qapp, mock_dongle_success, mock_config_file_exists,
                                   mock_db_config_loader, mock_pymysql_connected,
                                   mock_camera_sdk_not_found, mock_modbus_tcp_client_connected,
                                   signal_capture):
    """
    Test that run() method executes all five check methods in sequence.
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread.run()

    # Should have 5 emissions (one for each check)
    assert len(signal_capture.signals) == 5
    assert thread.checks_completed == 5


@pytest.mark.unit
@pytest.mark.threading
def test_run_emits_checks_complete(qapp, mock_dongle_success, mock_config_file_exists,
                                     mock_db_config_loader, mock_pymysql_connected,
                                     mock_camera_sdk_not_found, mock_modbus_tcp_client_connected):
    """
    Test that run() emits checks_complete signal with warning count.
    """
    thread = CheckerThread()
    complete_called = []
    thread.checks_complete.connect(lambda count: complete_called.append(count))

    thread.run()

    assert len(complete_called) == 1
    assert isinstance(complete_called[0], int)


@pytest.mark.unit
@pytest.mark.threading
def test_run_progress_tracking(qapp, mock_dongle_success, mock_config_file_exists,
                                 mock_db_config_loader, mock_pymysql_connected,
                                 mock_camera_sdk_not_found, mock_modbus_tcp_client_connected,
                                 signal_capture):
    """
    Test that checks_completed increments correctly during run().
    """
    thread = CheckerThread()
    thread.status_update.connect(signal_capture.capture)

    thread.run()

    assert thread.checks_completed == 5
    assert thread.total_checks == 5


@pytest.mark.unit
@pytest.mark.threading
def test_run_warning_accumulation(qapp, mock_dongle_failure, mock_config_file_missing,
                                    mock_db_config_loader, mock_pymysql_connection_error,
                                    mock_camera_sdk_not_found, mock_modbus_tcp_client_connection_failed):
    """
    Test that warning_count accumulates across all failed checks.
    """
    thread = CheckerThread()

    thread.run()

    # 5 failures expected (all checks fail)
    assert thread.warning_count == 5
