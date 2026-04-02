"""
Integration tests for StackUI class.
Tests screen management, transitions, and signal routing.

Coverage targets: 85%+ for StackUI.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication

from lib.StackUI import StackedWidget
from lib.Login_Screen import LoginScreen
from lib.LoadingScreen import LoadingScreen
from lib.Global import signal


# ============================================================================
# TEST GROUP 1: SCREEN MANAGEMENT (3 tests)
# ============================================================================

@pytest.mark.integration
def test_screen_indices_correct(qapp, mocker):
    """
    Verify correct screen indices (Login=0, Loading=1, Main=2).
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Verify widgets at each index
    assert isinstance(stack.widget(0), LoginScreen)
    assert isinstance(stack.widget(1), LoadingScreen)
    # Main screen is mocked, so just verify it exists
    assert stack.widget(2) is not None

    stack.close()


@pytest.mark.integration
def test_all_screens_added(qapp, mocker):
    """
    Verify all 3 screens are added to stacked widget.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    assert stack.count() == 3

    stack.close()


@pytest.mark.integration
def test_initial_screen_is_login(qapp, mocker):
    """
    Verify LoginScreen (index 0) is shown initially.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    assert stack.currentIndex() == 0
    assert isinstance(stack.currentWidget(), LoginScreen)

    stack.close()


# ============================================================================
# TEST GROUP 2: SCREEN TRANSITIONS (3 tests)
# ============================================================================

@pytest.mark.integration
@pytest.mark.signal
def test_switch_to_loading_screen(qapp, mocker):
    """
    Verify signal.switch_screen(1) shows LoadingScreen and starts checks.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Mock start_checks method
    mocker.patch.object(stack.loading_screen, 'start_checks')

    # Emit switch signal
    signal.switch_screen.emit(1)

    QApplication.processEvents()

    # Verify LoadingScreen is shown
    assert stack.currentIndex() == 1
    assert isinstance(stack.currentWidget(), LoadingScreen)

    # Verify start_checks was called
    stack.loading_screen.start_checks.assert_called_once()

    stack.close()


@pytest.mark.integration
@pytest.mark.signal
def test_switch_to_main_screen(qapp, mocker):
    """
    Verify loading_complete signal shows MainScreen (index 2).
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Start from loading screen
    signal.switch_screen.emit(1)
    QApplication.processEvents()

    assert stack.currentIndex() == 1

    # Emit loading_complete signal
    stack.loading_screen.loading_complete.emit()
    QApplication.processEvents()

    # Verify MainScreen is shown
    assert stack.currentIndex() == 2

    stack.close()


@pytest.mark.integration
@pytest.mark.signal
def test_switch_to_arbitrary_index(qapp, mocker):
    """
    Verify signal.switch_screen can switch between screens.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Switch to loading
    signal.switch_screen.emit(1)
    QApplication.processEvents()
    assert stack.currentIndex() == 1

    # Switch back to login
    signal.switch_screen.emit(0)
    QApplication.processEvents()
    assert stack.currentIndex() == 0
    assert isinstance(stack.currentWidget(), LoginScreen)

    stack.close()


# ============================================================================
# TEST GROUP 3: SIGNAL ROUTING (2 tests)
# ============================================================================

@pytest.mark.integration
@pytest.mark.signal
def test_switch_screen_signal_connected(qapp, mocker):
    """
    Verify switch_screen signal is connected to handler.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Spy on handler
    spy = mocker.spy(stack, 'on_switch_screen')

    signal.switch_screen.emit(1)
    QApplication.processEvents()

    # Handler should be called
    spy.assert_called_with(1)

    stack.close()


@pytest.mark.integration
@pytest.mark.signal
def test_loading_complete_signal_connected(qapp, mocker):
    """
    Verify LoadingScreen.loading_complete connects to show_main_screen.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Spy on handler
    spy = mocker.spy(stack, 'show_main_screen')

    # Emit signal
    stack.loading_screen.loading_complete.emit()
    QApplication.processEvents()

    # Handler should be called
    spy.assert_called()

    stack.close()


# ============================================================================
# TEST GROUP 4: INTEGRATION FLOW (2 tests)
# ============================================================================

@pytest.mark.integration
def test_loading_screen_lifecycle(qapp, mocker):
    """
    Verify complete flow: LoginScreen → LoadingScreen → MainScreen.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Step 1: Start at LoginScreen
    assert stack.currentIndex() == 0

    # Step 2: Emit switch to LoadingScreen
    signal.switch_screen.emit(1)
    QApplication.processEvents()
    assert stack.currentIndex() == 1

    # Step 3: LoadingScreen completes
    stack.show_main_screen()
    QApplication.processEvents()
    assert stack.currentIndex() == 2

    stack.close()


@pytest.mark.integration
@pytest.mark.signal
def test_signal_parameters_preserved(qapp, mocker):
    """
    Verify screen index parameter is preserved through signal chain.
    """
    # Mock MainScreen to avoid initialization
    mocker.patch("lib.StackUI.MainScreen")

    stack = StackedWidget()

    # Mock on_switch_screen to verify parameter
    mocker.patch.object(stack, 'on_switch_screen', wraps=stack.on_switch_screen)

    # Send index 1
    signal.switch_screen.emit(1)
    QApplication.processEvents()

    # Handler should receive correct index
    stack.on_switch_screen.assert_called_with(1)

    # Send index 0
    signal.switch_screen.emit(0)
    QApplication.processEvents()

    # Handler should receive correct index
    calls = stack.on_switch_screen.call_args_list
    assert calls[-1][0][0] == 0

    stack.close()
