"""
Module Docstring
"""
import time
import threading
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QGraphicsObject

from data.ppi_data_manager import PPIData
from ph3_tools import fileio

PPI_PARAMETERS = {}

class TrackController(QGraphicsObject):
    """
    Description
    """
    update_plot = pyqtSignal(bool)

    def __init__(self, gui, az_scan_rate, ppi_params=None):
        super().__init__()
        self.gui = gui
        self.tracks = None
        self.scenario_time = 0.0
        self.az_step_size = 45
        self.az_scan_rate = az_scan_rate
        self.playback_rate_s = az_scan_rate / (360 / self.az_step_size)
        self.update_rate_s = 2
        self.ppi_data = None
        self._is_interrupted = False
        self._is_started = True

        if ppi_params is not None:
            self.ppi_params = ppi_params
        else:
            self.ppi_params = PPI_PARAMETERS

        self.establish_connections()

    def establish_connections(self):
        self.gui.pb_load_scenario.clicked.connect(self.import_scenario_file)
        self.gui.pb_play.clicked.connect(self.play_scenario)
        self.gui.pb_pause.clicked.connect(self.pause_scenario)
        self.gui.pb_reset.clicked.connect(self.reset_ppi_display)
        self.gui.pb_skip_backward.clicked.connect(self.skip_back)
        self.gui.pb_skip_forward.clicked.connect(self.skip_forward)
        self.gui.pb_seek_to_time.clicked.connect(self.seek_time)
        self.gui.pb_cbar_apply.clicked.connect(self.update_cbar)
        self.gui.pb_az_step_apply.clicked.connect(self.update_az_step_size)
        # self.gui.cb_update_rate.currentTextChanged.connect(self.update_rate_change)
        
        self.update_plot.connect(self.update_ppi_display)

    def import_scenario_file(self):
        self.ppi_data = PPIData()
        file = self._open_scenario_file()
        self.ppi_data.file = file
        self.ppi_data.import_data()

        self.gui.le_scenario_length.setText(str(round(self.ppi_data.timestamp_array[-1], 2)))
        self.gui.le_az_resolution.setText(str(round(self.ppi_data.azimuth_step_size, 2)))
        self.gui.le_range_bin_size.setText(str(round(self.ppi_data.range_bin_size, 2)))
        self.gui.le_max_range.setText(str(round(self.ppi_data.max_range, 2)))

        self.reset_ppi_display()

    def _open_scenario_file(self):
        try:
            file = ""
            file, _ = QtWidgets.QFileDialog.getOpenFileName(
                caption="Dwell List Data File", filter="Data files (*.csv)",
            )
            # Check to make sure it's not empty
            if fileio.file_is_valid(file):
                self.gui.le_selected_file.setText(file)
            else:
                fileio.show_message_box("Error", "File does not exist.")
        except (FileNotFoundError, KeyError):
            fileio.show_message_box("Error", "File does not exist.")
        
        return file


    def play_scenario(self):
        self._is_interrupted = False
        self._runner = threading.Thread(target=self._service_loop)
        self._runner.start()
        self._is_started = True

        self.gui.pb_play.setEnabled(False)
        self.gui.pb_pause.setEnabled(True)
        self.gui.pb_reset.setEnabled(True)

    def pause_scenario(self):
        self._is_interrupted = True
        self._is_started = False
        
        self.gui.pb_play.setEnabled(True)
        self.gui.pb_pause.setEnabled(False)

    def reset_ppi_display(self):
        self._is_interrupted = True
        self._is_started = False
        self.scenario_time = 0.0

        self.gui.widget_ppi_plot.ppi_canvas.draw_canvas(self.ppi_data)
        self.gui.le_current_time.setText(str(self.scenario_time))

        self.gui.pb_play.setEnabled(True)
        self.gui.pb_pause.setEnabled(False)
        self.gui.pb_reset.setEnabled(False)
    
    def update_az_step_size(self):
        self.az_step_size = int(self.gui.le_az_step_size.text())
        self.playback_rate_s = self.az_scan_rate / (360 / self.az_step_size)

    def skip_back(self):
        skip_time = float(self.gui.le_increment.text())
        self.scenario_time -= skip_time
        if self.scenario_time < 0:
            self.scenario_time = 0.0

    def skip_forward(self):
        skip_time = float(self.gui.le_increment.text())
        self.scenario_time += skip_time      

    def seek_time(self):
        seek_time = float(self.gui.le_seek_to_time.text())
        self.scenario_time = seek_time
        if self.scenario_time < 0:
            self.scenario_time = 0.0
        self.update_ppi_callback()

    def update_cbar(self):
        vmin = float(self.gui.le_cbar_min.text())
        vmax = float(self.gui.le_cbar_max.text())
        self.gui.widget_ppi_plot.ppi_canvas.update_vlims(vmin, vmax)
        max_range = float(self.gui.le_max_range.text())
        self.gui.widget_ppi_plot.ppi_canvas.update_max_range(max_range)

        self.update_ppi_callback()

    def update_ppi_callback(self):
        self.update_plot.emit(True)

    @pyqtSlot(bool)
    def update_ppi_display(self):
        self.scenario_time += self.playback_rate_s
        beam_data = self.ppi_data.get_beam_data(self.scenario_time, self.az_scan_rate)
        powers = self.ppi_data.generate_data(self.scenario_time, self.az_scan_rate)
        self.gui.widget_ppi_plot.ppi_canvas.update_canvas(beam_data, powers)
        self.gui.le_current_time.setText(str(self.scenario_time))
    
    def quit(self):
        """
        Description
        """
        self._is_interrupted = True
        self._is_started = False
    
    def _service_loop(self):
        while not self._is_interrupted:
            self.update_ppi_callback()
            time.sleep(self.update_rate_s)
