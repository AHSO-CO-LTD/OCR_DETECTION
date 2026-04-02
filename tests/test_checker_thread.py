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
def test_check_dongle_success(qapp, mock_dongle_success, mocker):
    """
    Test successful dongle check emits status update with ✓ OK.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_dongle()

    # Verify signal emitted with correct parameters
    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Hardware Dongle"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_dongle_failure(qapp, mock_dongle_failure, mocker):
    """
    Test failed dongle check emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_dongle()

    # Verify signal emitted and warning counted
    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Hardware Dongle"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_dongle_exception(qapp, mock_dongle_exception, mocker):
    """
    Test dongle exception is caught and warning_count incremented.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_dongle()

    # Verify exception handled
    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Hardware Dongle"
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


# ============================================================================
# TEST GROUP 3: CONFIG CHECK (3 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_config_exists(qapp, mock_config_file_exists, mocker):
    """
    Test config file existence check emits status update with ✓ OK.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_config()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Config File"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_config_missing(qapp, mock_config_file_missing, mocker):
    """
    Test missing config file emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_config()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Config File"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1
    assert thread.checks_completed == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_config_exception(qapp, mocker):
    """
    Test os.path.exists exception is caught and handled.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    # Mock os.path.exists to raise exception
    mocker.patch("os.path.exists", side_effect=Exception("Permission denied"))

    thread._check_config()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Config File"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 4: DATABASE CHECK (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_database_connected(qapp, mock_db_config_loader, mock_pymysql_connected, mocker):
    """
    Test successful database connection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_database()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Database"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_operational_error(qapp, mock_db_config_loader, mock_pymysql_connection_error, mocker):
    """
    Test database connection failure emits status update with ✗ Connection failed.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_database()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Database"
    assert "connection failed" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_query_error(qapp, mock_db_config_loader, mock_pymysql_query_error, mocker):
    """
    Test database query failure emits status update.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_database()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Database"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_database_timeout(qapp, mock_db_config_loader, mock_pymysql_timeout, mocker):
    """
    Test database connection timeout emits status update with ✗ error message.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_database()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Database"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 5: CAMERA CHECK (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_found(qapp, mock_camera_sdk_found, mocker):
    """
    Test successful camera detection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_camera()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Camera"
    assert "OK" in status or "✓" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_not_found(qapp, mock_camera_sdk_not_found, mocker):
    """
    Test no cameras found emits status update with ✗ Not found.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_camera()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Camera"
    assert "not found" in status.lower() or "✗" in status
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_sdk_not_installed(qapp, mock_camera_sdk_import_error, mocker):
    """
    Test SDK ImportError emits status update with SDK error message.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_camera()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Camera"
    assert "SDK" in status or "not installed" in status.lower()
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.signal
def test_check_camera_exception(qapp, mock_camera_exception, mocker):
    """
    Test camera enumeration exception is caught and handled.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_camera()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "Camera"
    assert is_ok == False
    assert thread.warning_count == 1


# ============================================================================
# TEST GROUP 6: PLC CHECK (5 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_connected(qapp, mock_db_config_loader, mock_modbus_tcp_client_connected, mocker):
    """
    Test successful Modbus TCP connection emits status update with ✓ OK.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_plc()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "PLC"
    assert "OK" in status or "✓" in status or "Ready" in status
    assert is_ok == True
    assert thread.warning_count == 0


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_connection_failed(qapp, mock_db_config_loader, mock_modbus_tcp_client_connection_failed, mocker):
    """
    Test Modbus TCP connection failure emits error status.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_plc()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_read_failed(qapp, mock_db_config_loader, mock_modbus_tcp_client_read_failed, mocker):
    """
    Test Modbus read failure emits error status.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_plc()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_modbus_read_timeout(qapp, mock_db_config_loader, mock_modbus_tcp_client_read_timeout, mocker):
    """
    Test Modbus read timeout emits error status.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    thread._check_plc()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "PLC"
    assert is_ok == False
    assert thread.warning_count == 1


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_check_plc_non_tcp_protocol(qapp, mocker):
    """
    Test non-TCP protocol (RTU/SLMP) emits status with ready indicator.
    """
    thread = CheckerThread()
    spy = mocker.spy(thread.status_update, 'emit')

    # Mock config to return non-TCP protocol
    mock_config = {
        "plc": {
            "protocol": "rtu",
            "host": "COM1"
        }
    }
    mocker.patch("lib.Database._load_db_config", return_value=mock_config)

    thread._check_plc()

    spy.assert_called_once()
    component, status, is_ok = spy.call_args[0]
    assert component == "PLC"
    # Non-TCP protocols are marked as ready (manual configuration)
    assert "Ready" in status or "manual" in status.lower()
    assert is_ok == True
    assert thread.warning_count == 0


# ============================================================================
# TEST GROUP 7: RUN() METHOD & SIGNALS (4 tests)
# ============================================================================

@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_run_executes_all_checks(qapp, mocker):
    """
    Verify run() method executes all 5 checks sequentially.
    """
    thread = CheckerThread()

    # Mock all check methods
    mocker.patch.object(thread, '_check_dongle')
    mocker.patch.object(thread, '_check_config')
    mocker.patch.object(thread, '_check_database')
    mocker.patch.object(thread, '_check_camera')
    mocker.patch.object(thread, '_check_plc')

    # Mock the signals
    spy_complete = mocker.spy(thread.checks_complete, 'emit')

    thread.run()

    # Verify all checks were called
    thread._check_dongle.assert_called_once()
    thread._check_config.assert_called_once()
    thread._check_database.assert_called_once()
    thread._check_camera.assert_called_once()
    thread._check_plc.assert_called_once()

    # Verify completion signal emitted
    spy_complete.assert_called_once()


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_run_emits_checks_complete(qapp, mocker):
    """
    Verify run() emits checks_complete signal with warning_count.
    """
    thread = CheckerThread()
    thread.warning_count = 2  # Simulate 2 failed checks

    # Mock all check methods
    mocker.patch.object(thread, '_check_dongle')
    mocker.patch.object(thread, '_check_config')
    mocker.patch.object(thread, '_check_database')
    mocker.patch.object(thread, '_check_camera')
    mocker.patch.object(thread, '_check_plc')

    spy = mocker.spy(thread.checks_complete, 'emit')

    thread.run()

    spy.assert_called_once_with(2)


@pytest.mark.unit
@pytest.mark.threading
def test_run_progress_tracking(qapp, mocker):
    """
    Verify run() increments checks_completed counter.
    """
    thread = CheckerThread()
    assert thread.checks_completed == 0

    # Mock all check methods
    mocker.patch.object(thread, '_check_dongle')
    mocker.patch.object(thread, '_check_config')
    mocker.patch.object(thread, '_check_database')
    mocker.patch.object(thread, '_check_camera')
    mocker.patch.object(thread, '_check_plc')

    mocker.patch.object(thread, 'status_update')
    mocker.patch.object(thread, 'checks_complete')

    thread.run()

    # After 5 checks, checks_completed should be 5
    assert thread.checks_completed == 5


@pytest.mark.unit
@pytest.mark.threading
@pytest.mark.signal
def test_run_warning_accumulation(qapp, mocker):
    """
    Verify run() accumulates warning_count across multiple failures.
    """
    thread = CheckerThread()
    assert thread.warning_count == 0

    # Mock checks to emit status with failures
    def mock_check_fail():
        thread.warning_count += 1
        thread.checks_completed += 1

    def mock_check_pass():
        thread.checks_completed += 1

    mocker.patch.object(thread, '_check_dongle', side_effect=mock_check_fail)
    mocker.patch.object(thread, '_check_config', side_effect=mock_check_pass)
    mocker.patch.object(thread, '_check_database', side_effect=mock_check_fail)
    mocker.patch.object(thread, '_check_camera', side_effect=mock_check_pass)
    mocker.patch.object(thread, '_check_plc', side_effect=mock_check_fail)

    mocker.patch.object(thread.status_update, 'emit')
    mocker.patch.object(thread.checks_complete, 'emit')

    thread.run()

    # After 5 checks with 3 failures
    assert thread.checks_completed == 5
    assert thread.warning_count == 3
