import os

from iqtools.analysismanager import AnalysisManager
from iqtools.datastructures.iqdata import IQData
from iqtools.datastructures.configsettings import FrequencySettings
from iqtools.datastructures.configsettings import FrequencyPlots
from iqtools.plotting.frequencyplotter import FrequencyPlotter

# "rbw_hz": (3 * (10 ** 3)),        Resolution BW: FFT window size, lower RBW's allow better
#                                   signal separation at the expense of decreased time accuracy
#
# "span_hz": (10 * (10 ** 6)),      Span: Width of frequency spectrum that will be shown when plotting. 
#                                   Theoretical limit is the original recorded IQ width
#
# "f_c": 0,                         **
#
# "f_c_iq_hz": 1 * (10 ** 9),       IQ Center Frequency: Center frequency
#
# "pwr_min_dbm": -100,               Power limit min: Set the power ranges that the plot will show. 
#                                   Spectogram = heatmap distribution, spectrum = y-axis
#
# "pwr_max_dbm": 0,                  Power limit max: ^
#
# "tot_anal_dur_s": 1.0,            Total Analysis Duration: Length of recording that will be plotted
#
# "anal_del_s": 0.0,                Analysis Delay: Offset from the begining of recording
#
# "bb_duc_choice": "Baseband (BB)", Baseband and digital upconverter choice: Baseband will center plots at zero HZ
#                                                                            Upshift Frequency to IQ Center to IQ Center 
#                                                                            will center plots at the IQ center frequency
#
# "opt_rbw_hz_flag": False,         Optimize RBW for FFT: This will optimize the current selected RBW value for the utilized 
#                                                         Matlab FFT algorithm by calculating the nearest power of two number
#                                                         to the current selected RBW. This does NOT select an RBW that is 
#                                                         necessarily ideal for the user, only one that is ideal for processing time.
#
# "freq_fig_choice": "Spectrogram", Frquency Figure Choice
#
# "plt_style": 2,                   Plot Style: 1 = SpectralHTMLPlt w/ iqtools.frequency.HTML_Plot.spectrogram_html_only
#                                               2 = pyqt5 window w/ iqtools.frequency.Matplotlib_Plot.Matplotlib_Plot_Window
#
# "save_output_figures": True       Save output figures
#

default_settings = {
    "input_file": "example-data\\s1_pulsed_with_fm.iq",
    "filename": "test",
    "output_dir": os.path.join(os.getcwd(), "test-data"),

    "rbw_hz": 10000,
    "span_hz": 60000000,
    "f_c_iq_hz": 1500000000,
    "pwr_min_dbm": -100,
    "pwr_max_dbm": 0,
    "analysis_duration_sec": 4.0,
    "analysis_delay_sec": 0.0,
    "bb_duc_choice": "BASEBAND",
    "opt_rbw_hz_flag": False,
    "real_time_gif": False,
    "plot_option": "Static Window",
    "save_output_figures": True
}


class FrequencyManager(AnalysisManager):
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
        self.analysis_type = "frequency"

    def initialize_settings(self, settings: dict):
        freqsettings = FrequencySettings()
        if settings == None:
            freqsettings.deserialize(default_settings)
        else:
            freqsettings.deserialize(settings)
        self.settings = freqsettings

    def execute(self, plots = []):
        if type(plots) is not list and type(plots) is not set:
            plots = [plots]
        if not plots:
            return
        self.check_output_directory()
        if self.data is None:
            self.data = IQData()
            self.head = self.importiq()
        self.settings.center_freq_hz = self.data.centerghz / 1e9
        self.processcommand(plots)

    def processcommand(self, plots):
        plotter = FrequencyPlotter(self.settings, self.data)
        plotter.params.plot_selection = plots
        plotter.create_plot()
