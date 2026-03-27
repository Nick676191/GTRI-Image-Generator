"""
Module Docstring
"""

from PyQt5.QtWidgets import QMainWindow

from ph0_gui.plotter import Ui_plotter
from .plot_controller import PlotController


class MainController(QMainWindow, Ui_plotter):
    """
    Description
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.plot_controller = None

        self.initialize_controllers()

    def initialize_controllers(self):
        """
        Description
        """
        self.plot_controller = PlotController(self)

    def closeEvent(self, event):
        """
        Overriding close event
        """
        self.plot_controller.quit()
        event.accept()
