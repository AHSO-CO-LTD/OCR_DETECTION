from PyQt5 import QtWidgets

from Main_Screen import MainScreen
from Login_Screen import LoginScreen
from LoadingScreen import LoadingScreen
from Global import signal

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
        signal.switch_screen.connect(self.switch_screen)

        # Loading screen → show loading and start checks
        signal.switch_screen.connect(self.on_switch_screen)

        # Loading screen complete → show main screen
        self.loading_screen.loading_complete.connect(self.show_main_screen)

    def switch_screen(self, index):
        self.setCurrentIndex(index)

    def on_switch_screen(self, index):
        """Handle screen switch with loading screen logic"""
        # If switching to loading screen (index 1 from login), start checks
        if index == 1:
            self.setCurrentIndex(index)
            self.loading_screen.start_checks()

    def show_main_screen(self):
        """Switch to main screen after loading is complete"""
        self.setCurrentIndex(2)