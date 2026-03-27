import pandas as pd

from iqtools.plotting.simple_plotter import MplPlotter, PlotlyPlotter
from iqtools.plotting.generalrunner import GeneralRunner
from iqtools.plotting.detectionalgorithms import detect_pulse # , cw_detection
from iqtools.datastructures.configsettings import PDWSettings, PDWPlots, PlotOutput

pd.options.mode.chained_assignment = None  # default='warn'

PLOTTER_TYPES = {
    PlotOutput.HTML: PlotlyPlotter,
    PlotOutput.STATIC: MplPlotter
}


class PdwRunner(GeneralRunner):
    def __init__(self, params, data):
        super().__init__(params, data)
        self.is_cw = False
        self.iqdata = data
        self.sig_data = self.iqdata.iqdf
        self.params: PDWSettings = params
        self.pulse_df: pd.DataFrame = None
        self.pdws_made = False

    # def _check_if_continuous_wave(self):
    #     deltatime = 1 / self.iqdata.samplefreq
    #     self.is_cw = cw_detection(self.sig_data, deltatime, self.params.trigger_level_dbm, self.params.analysis_del_sec)

    def generate_pdws(self):
        self.add_output_file_name()
        deltatime = 1 / self.iqdata.samplefreq
        self.pulse_df = detect_pulse(self.sig_data, deltatime, self.params)
        # self.pulse_df.to_csv(path_or_buf=f"{self.params.output_file}.csv")
        self.pdws_made = True

    def create_plot(self):
        # self._check_if_continuous_wave()
        if not self.pdws_made:
            self.generate_pdws()
        self.plotter = PLOTTER_TYPES[self.params.plot_output]()
        for plot in self.params.plot_selection:
            if plot == PDWPlots.PW:
                self.plot_pulse_width()
            elif plot == PDWPlots.PRI:
                self.plot_pri()
            elif plot == PDWPlots.POWER:
                self.plot_pulse_power()
            elif plot == PDWPlots.PHASE:
                self.plot_pulse_phase()
            elif plot == PDWPlots.FREQUENCY:
                self.plot_pulse_frequency()

    def plot_pulse_width(self):
        title = "Pulse Width over Time"
        x_data = self.pulse_df["pulse_start_time"]
        x_axis = "Time (us)"
        y_data = [self.pulse_df["pulse_width"]]
        y_axis = "Time (us)"
        file = f"{self.params.output_file}_pdw_pw"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def plot_pri(self):
        title = "PRI over Time"
        x_data = self.pulse_df["pulse_start_time"][1:]
        x_axis = "Time (us)"
        y_data = [self.pulse_df["pri"][1:]]
        y_axis = "Time (us)"
        file = f"{self.params.output_file}_pdw_pri"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def plot_pulse_power(self):
        title = "Pulse Power over Time"
        x_data = self.pulse_df["pulse_start_time"]
        x_axis = "Time (us)"
        y_data = [self.pulse_df["relative_power"]]
        y_axis = "Power (dBm)"
        file = f"{self.params.output_file}_pdw_power"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def plot_pulse_phase(self):  
        title = "Pulse Phase over Time"
        x_data = self.pulse_df["pulse_start_time"]
        x_axis = "Time (us)"
        y_data = [self.pulse_df["phase"]]
        y_axis = "Phase (°)"
        file = f"{self.params.output_file}_pdw_phase"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def plot_pulse_frequency(self):
        title = "Pulse Frequency (Baseband) over Time"
        x_data = self.pulse_df["pulse_start_time"]
        x_axis = "Time (us)"
        y_data = [self.pulse_df["freq_offset"]]
        y_axis = "Frequency (Hz)"
        file = f"{self.params.output_file}_pdw_frequency"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)
