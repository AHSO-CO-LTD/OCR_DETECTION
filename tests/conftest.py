"""
Pytest configuration and shared fixtures for OCR Detection tests.
Provides mocks for external dependencies (database, camera, PLC, dongle, config).
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# ============================================================================
# PLATFORM-SPECIFIC MOCKING (Windows DLL loading on macOS/Linux)
# ============================================================================

# Mock Windows-specific ctypes.windll for non-Windows platforms
if not sys.platform.startswith('win'):
    # Mock the windll attribute for ctypes module
    import ctypes
    if not hasattr(ctypes, 'windll'):
        ctypes.windll = MagicMock()


# ============================================================================
# Mock modules and classes that are hard to import/use in test environment
# ============================================================================
import sys
from unittest.mock import MagicMock, patch

# Pre-mock external/complex dependencies to avoid import errors
MODULES_TO_MOCK = [
    'Deep_Learning_Tool',      # Has complex PyTorch dependencies
    'pymcprotocol',            # PLC protocol library (not in requirements)
    'form_UI',                 # UI form files
    'form_UI.Ui_test_form',    # Generated UI module
]

for module_name in MODULES_TO_MOCK:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

# Patch DatabaseConnection to prevent database connection attempts at import time
# Main_Screen.py does: db = DatabaseConnection() at module level, which fails without MySQL
import lib.Database
original_db_connection = lib.Database.DatabaseConnection
lib.Database.DatabaseConnection = MagicMock(return_value=MagicMock())

# ============================================================================
# SESSION-SCOPED FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def qapp():
    """
    Create QApplication once per test session.
    Required by pytest-qt for all PyQt5 tests.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Note: Don't delete QApplication, it will cause issues with PyQt5


# ============================================================================
# MODULE-SCOPED FIXTURES - Dongle Mocks
# ============================================================================

@pytest.fixture
def mock_dongle_success(mocker):
    """
    Mock initialize_secure_dongle to return True (success).
    """
    return mocker.patch(
        "lib.Global.initialize_secure_dongle",
        return_value=True
    )


@pytest.fixture
def mock_dongle_failure(mocker):
    """
    Mock initialize_secure_dongle to return False (failure).
    """
    return mocker.patch(
        "lib.Global.initialize_secure_dongle",
        return_value=False
    )


@pytest.fixture
def mock_dongle_exception(mocker):
    """
    Mock initialize_secure_dongle to raise an exception.
    """
    return mocker.patch(
        "lib.Global.initialize_secure_dongle",
        side_effect=Exception("Dongle initialization failed")
    )


# ============================================================================
# MODULE-SCOPED FIXTURES - Config File Mocks
# ============================================================================

@pytest.fixture
def mock_config_file_exists(mocker):
    """
    Mock os.path.exists to return True for config.yaml check.
    """
    return mocker.patch("os.path.exists", return_value=True)


@pytest.fixture
def mock_config_file_missing(mocker):
    """
    Mock os.path.exists to return False (config file missing).
    """
    return mocker.patch("os.path.exists", return_value=False)


# ============================================================================
# MODULE-SCOPED FIXTURES - Database Mocks
# ============================================================================

@pytest.fixture
def mock_db_config():
    """
    Mock database configuration.
    Returns test database config dictionary.
    """
    return {
        "host": "localhost",
        "port": 3306,
        "user": "test_user",
        "password": "test_password",
        "database": "test_db"
    }


@pytest.fixture
def mock_db_config_loader(mocker, mock_db_config):
    """
    Mock _load_db_config to return test configuration.
    """
    return mocker.patch(
        "lib.Database._load_db_config",
        return_value=mock_db_config
    )


@pytest.fixture
def mock_pymysql_connected(mocker):
    """
    Mock pymysql.connect() that successfully returns a connection.
    """
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.return_value = (1,)  # SELECT 1 result
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__.return_value = None

    mock_connection.__enter__.return_value = mock_connection
    mock_connection.__exit__.return_value = None

    return mocker.patch(
        "pymysql.connect",
        return_value=mock_connection
    )


@pytest.fixture
def mock_pymysql_connection_error(mocker):
    """
    Mock pymysql.connect() that raises OperationalError (connection failed).
    """
    import pymysql
    return mocker.patch(
        "pymysql.connect",
        side_effect=pymysql.err.OperationalError("Connection refused")
    )


@pytest.fixture
def mock_pymysql_query_error(mocker):
    """
    Mock pymysql.connect() that succeeds but cursor.execute raises DatabaseError.
    """
    import pymysql
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = pymysql.err.DatabaseError("Query failed")
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__.return_value = None

    mock_connection.__enter__.return_value = mock_connection
    mock_connection.__exit__.return_value = None

    return mocker.patch(
        "pymysql.connect",
        return_value=mock_connection
    )


@pytest.fixture
def mock_pymysql_timeout(mocker):
    """
    Mock pymysql.connect() that times out.
    """
    return mocker.patch(
        "pymysql.connect",
        side_effect=TimeoutError("Connection timeout")
    )


# ============================================================================
# MODULE-SCOPED FIXTURES - Camera Mocks
# ============================================================================

@pytest.fixture
def mock_camera_sdk_found(mocker):
    """
    Mock pypylon camera SDK that finds devices.
    """
    # Mock the pypylon module
    mock_pylon = MagicMock()
    mock_factory = MagicMock()
    mock_device = MagicMock()

    mock_factory.GetInstance.return_value = mock_factory
    mock_factory.EnumerateDevices.return_value = [mock_device]
    mock_pylon.TlFactory = mock_factory

    return mocker.patch("pypylon.pylon", mock_pylon)


@pytest.fixture
def mock_camera_sdk_not_found(mocker):
    """
    Mock pypylon camera SDK that returns empty device list.
    """
    mock_pylon = MagicMock()
    mock_factory = MagicMock()

    mock_factory.GetInstance.return_value = mock_factory
    mock_factory.EnumerateDevices.return_value = []
    mock_pylon.TlFactory = mock_factory

    return mocker.patch("pypylon.pylon", mock_pylon)


@pytest.fixture
def mock_camera_sdk_import_error(mocker):
    """
    Mock pypylon import that raises ImportError.
    """
    return mocker.patch(
        "pypylon.pylon",
        side_effect=ImportError("pypylon not installed")
    )


@pytest.fixture
def mock_camera_exception(mocker):
    """
    Mock pypylon that raises a generic exception.
    """
    mock_pylon = MagicMock()
    mock_factory = MagicMock()

    mock_factory.GetInstance.return_value = mock_factory
    mock_factory.EnumerateDevices.side_effect = Exception("Camera enumeration failed")
    mock_pylon.TlFactory = mock_factory

    return mocker.patch("pypylon.pylon", mock_pylon)


# ============================================================================
# MODULE-SCOPED FIXTURES - PLC/Modbus Mocks
# ============================================================================

@pytest.fixture
def mock_modbus_tcp_client_connected(mocker):
    """
    Mock ModbusTcpClient that connects and reads successfully.
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = True
    mock_response = MagicMock()
    mock_response.isError.return_value = False
    mock_client.read_coils.return_value = mock_response
    mock_client.close.return_value = None

    return mocker.patch(
        "pymodbus.client.ModbusTcpClient",
        return_value=mock_client
    )


@pytest.fixture
def mock_modbus_tcp_client_connection_failed(mocker):
    """
    Mock ModbusTcpClient that fails to connect.
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = False
    mock_client.close.return_value = None

    return mocker.patch(
        "pymodbus.client.ModbusTcpClient",
        return_value=mock_client
    )


@pytest.fixture
def mock_modbus_tcp_client_read_failed(mocker):
    """
    Mock ModbusTcpClient that connects but read fails.
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = True
    mock_response = MagicMock()
    mock_response.isError.return_value = True
    mock_client.read_coils.return_value = mock_response
    mock_client.close.return_value = None

    return mocker.patch(
        "pymodbus.client.ModbusTcpClient",
        return_value=mock_client
    )


@pytest.fixture
def mock_modbus_tcp_client_read_timeout(mocker):
    """
    Mock ModbusTcpClient that times out during read.
    """
    mock_client = MagicMock()
    mock_client.connect.return_value = True
    mock_client.read_coils.side_effect = TimeoutError("Read timeout")
    mock_client.close.return_value = None

    return mocker.patch(
        "pymodbus.client.ModbusTcpClient",
        return_value=mock_client
    )


@pytest.fixture
def mock_modbus_import_error(mocker):
    """
    Mock pymodbus import that raises ImportError.
    """
    return mocker.patch(
        "pymodbus.client.ModbusTcpClient",
        side_effect=ImportError("pymodbus not installed")
    )


# ============================================================================
# FUNCTION-SCOPED FIXTURES - Qt Specific
# ============================================================================

@pytest.fixture
def qt_widget(qapp):
    """
    Create a basic Qt widget for testing (cleaned up after each test).
    """
    from PyQt5.QtWidgets import QWidget
    widget = QWidget()
    yield widget
    widget.close()


# ============================================================================
# TEST MARKERS AND HELPERS
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers",
        "unit: Mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: Mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "threading: Mark test as testing threading behavior"
    )
    config.addinivalue_line(
        "markers",
        "signal: Mark test as testing signal emission"
    )
