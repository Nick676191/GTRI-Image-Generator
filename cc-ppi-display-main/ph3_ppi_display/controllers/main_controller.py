"""
Module Docstring
"""

from PyQt5.QtWidgets import QMainWindow

from gui.ppi_gui import Ui_ppi_gui
from .track_controller import TrackController


class MainController(QMainWindow, Ui_ppi_gui):
    """
    Description
    """

    def __init__(self, az_scan_rate):
        super().__init__()
        self.setupUi(self)
        self.track_controller = None

        self.initialize_controllers(az_scan_rate)

    def initialize_controllers(self, az_scan_rate):
        """
        Description
        """
        self.track_controller = TrackController(self, az_scan_rate)

    def closeEvent(self, event):
        """
        Overriding close event
        """
        self.track_controller.quit()
        event.accept()
