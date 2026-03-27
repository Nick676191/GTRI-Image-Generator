import os

from iqtools.analysismanager import AnalysisManager
from iqtools.datastructures.iqdata import IQData
from iqtools.datastructures.configsettings import TimeSettings
from iqtools.plotting.timeplotter import TimePlotter

default_settings = {
    "input_file": "example-data\\s1_pulsed_with_fm.iq",
    "filename": "testsweep",
    "output_dir": os.path.join(os.getcwd(), "test-data"),

    "trigger_type": "Free Run",
    "trigger_delay_sec": 0.0001,
    "trigger_level_dBm": -30,
    "analysis_duration_sec": 0.1,
    "analysis_delay_sec": 0.0,
    "pwr_min_dbm": -80,
    "pwr_max_dbm": 0,
    "sweep_window_sec": 0.002,
    "plot_option": "Static Window",
    "save_output_figures": True
}

plot_options = [
    "Interactive HTML",
    "Static Window",
]

trigger_type = [
    "Free Run",
    "Triggered"
]

figure_options = [
    "iqpower", "Total IQ Power vs Time",
    "iqvolts", "Total IQ Voltage vs Time",
    "iqphase", "Total IQ Phase vs Time",
    "osc", "Oscillogram",
    "sweep", "Sweep window playback animation",
    "bothtime", "Playback animation and Oscillogram",
]

class TimeManager(AnalysisManager):
    """
    Class to manage analysis of iqdata
    providing interface bridge to each
    analysis capability
    """
    def __init__(self, settings=None, data = None):
        """
        Initialization of parameters
        """
        super().__init__(settings, data)
        self.analysis_type = "time"

    def initialize_settings(self, settings):
        timesettings = TimeSettings()
        if settings == None:
            timesettings.deserialize(default_settings)
        else:
            timesettings.deserialize(settings)
        self.settings = timesettings

    def execute(self, plots=[]):
        if type(plots) is not list and type(plots) is not set:
            plots = [plots]
        if not plots:
            return
        self.check_output_directory()
        if self.data is None:
            self.data = IQData()
            self.head = self.importiq()
        self.processcommand(plots)

    def processcommand(self, plots):
        plotter = TimePlotter(self.settings, self.data)
        plotter.params.plot_selection = plots
        plotter.create_plot()
