"""
Module Docstring
"""

import sys
import os

# Third party libraries
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore

from ph0_controllers.main_controller import MainController
# from data.support_methods import import_json

def execute_ph0(file):
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app.setStyle("Fusion")
    form = MainController()
    form.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    execute_ph0(None)
