import os

from iqtools.analysismanager import AnalysisManager
from iqtools.datastructures.iqdata import IQData
from iqtools.datastructures.configsettings import PDWSettings

from iqtools.plotting.pdwrunner import PdwRunner


default_settings = {
    "input_file": "example-data\\s1_pulsed_with_fm.iq",
    "filename": "test",
    "output_dir": os.path.join(os.getcwd(), "test-data"),

    "trigger_level_dbm": -30,
    "hyst_bool": False,
    "hyst_level": 3,
    "analysis_dur_sec": 1,
    "analysis_del_sec": 0,
    "analysis_duration_sec": 1,
    "analysis_start_sec": 0,
    "plot_option": "Static Window",
    "figure_type": "Pulse Width vs Time",
    "save_output_figures": True
}

plot_options = [
    "Interactive HTML",
    "Static Window",
]


figure_options = [
    "pulse_width",
    "pri",
    "power",
    "phase",
    "frequency",
    "pdw"
]


class PdwManager(AnalysisManager):
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
        self.plotter = None
        self.pdws_made = False

    def initialize_settings(self, settings):
        freqsettings = PDWSettings()
        if settings == None:
            freqsettings.deserialize(default_settings)
        else:
            freqsettings.deserialize(settings)
        self.settings = freqsettings

    def _prepare_runner(self):
        self.check_output_directory()
        if self.data is None:
            self.data = IQData()
            self.head = self.importiq()
        self.plotter = PdwRunner(self.settings, self.data)

    def generate_pdws(self):
        self._prepare_runner()
        self.plotter.generate_pdws()
        self.pdws_made = True

    def execute(self, plots):
        if type(plots) is not list and type(plots) is not set:
            plots = [plots]
        if not plots:
            return
        if not self.pdws_made:
            self.generate_pdws()
        self.plotter.params.plot_selection = plots
        self.plotter.create_plot()
