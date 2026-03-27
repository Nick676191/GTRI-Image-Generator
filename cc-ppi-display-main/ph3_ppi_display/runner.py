"""
Module Docstring
"""

import sys
import os

# Third party libraries
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore

from controllers.main_controller import MainController
from data.support_methods import import_json

def execute_ph3(file):
    config = import_json(file)
    az_block_size = config["ph1_settings"]["radar"]["antenna_az_block_size_deg"]
    az_stare_time = config["ph1_settings"]["radar"]["az_stare_time_us"] / 1e6
    az_scan_rate = 360 / az_block_size * az_stare_time

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app.setStyle("Fusion")
    form = MainController(az_scan_rate)
    form.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    execute_ph3(None)
