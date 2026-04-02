from PyQt5 import QtWidgets

from lib.Main_Screen import MainScreen
from lib.Login_Screen import LoginScreen
from lib.LoadingScreen import LoadingScreen
from lib.Global import signal


class StackedWidget(QtWidgets.QStackedWidget):
    def __init__(self):
        super().__init__()
        self.login_screen = LoginScreen()
        self.loading_screen = LoadingScreen()
        self.main_screen = MainScreen()

        # Add screens to stacked widget
        self.addWidget(self.login_screen)    # index 0
        self.addWidget(self.loading_screen)  # index 1
        self.addWidget(self.main_screen)     # index 2

        self.set_event()

    def set_event(self):
        """Connect signals for screen transitions"""
        # Loading screen logic: switch to loading and start checks
        signal.switch_screen.connect(self.on_switch_screen)

        # Loading screen complete → show main screen
        self.loading_screen.loading_complete.connect(self.show_main_screen)

    def on_switch_screen(self, index):
        """Handle screen switch with loading screen logic"""
        # If switching to loading screen (index 1 from login), show it and start checks
        if index == 1:
            self.setCurrentIndex(index)
            self.loading_screen.start_checks()
        else:
            self.setCurrentIndex(index)

    def show_main_screen(self):
        """Switch to main screen after loading is complete"""
        self.setCurrentIndex(2)