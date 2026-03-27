"""
Module Docstring
"""
import time
import threading
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QGraphicsObject

from hdf_data.blockdata import BlockData
from tools import fileio

PPI_PARAMETERS = {}

class PlotController(QGraphicsObject):
    """
    Description
    """
    update_plot = pyqtSignal(bool)

    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.block_data = None

        self.establish_connections()

    def establish_connections(self):
        print('establish')
        self.gui.pb_load_scenario.clicked.connect(self.import_block_file)
        self.gui.pb_plot.clicked.connect(self.plot_dwell)

    def import_block_file(self):
        self.block_data = BlockData()
        file = self._open_scenario_file()
        self.block_data.file = file
        self.block_data.import_data()

        self.gui.cb_select_dwell.clear()
        self.gui.cb_select_dwell.addItems(self.block_data.dwells)
        self.gui.cb_select_dwell.setEnabled(True)
        self.gui.pb_plot.setEnabled(True)
    
    def _open_scenario_file(self):
        try:
            file = ""
            file, _ = QtWidgets.QFileDialog.getOpenFileName(
                caption="Block Data File", filter="Data files (*.hdf5)",
            )
            # Check to make sure it's not empty
            if fileio.file_is_valid(file):
                self.gui.le_selected_file.setText(file)
            else:
                fileio.show_message_box("Error", "File does not exist.")
        except (FileNotFoundError, KeyError):
            fileio.show_message_box("Error", "File does not exist.")
        
        return file
    
    def plot_dwell(self):
        dwell = self.gui.cb_select_dwell.currentText()
        self.block_data.get_dwell_iq(dwell)

        self.gui.widget_plot.Plot(self.block_data.timestamps, self.block_data.powers)


    def quit(self):
        """
        Description
        """
