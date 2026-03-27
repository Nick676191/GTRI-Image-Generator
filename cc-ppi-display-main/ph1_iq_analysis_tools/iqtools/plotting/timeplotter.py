import pandas as pd

from .generalrunner import GeneralRunner
from iqtools.datastructures.configsettings import TimeSettings, TimePlots

pd.options.mode.chained_assignment = None  # default='warn'

class TimePlotter(GeneralRunner):

    def __init__(self, params, data):
        super().__init__(params, data)
        self.iqdata = data
        self.sig_data = self.iqdata.iqdf
        self.params: TimeSettings = params
        self.plot_type = None
        self.plot_center = None

    def create_plot(self):
        self.prepare_plot_data()
        for plot in self.params.plot_selection:
            if plot == TimePlots.IQPOWER:
                self.power_plot()
            elif plot == TimePlots.IQVOLTS:
                self.voltage_plot()
            elif plot == TimePlots.IQPHASE:
                self.phase_plot()
            elif plot == TimePlots.OSCILLOGRAM:
                self.oscillogram()
            elif plot == TimePlots.OSCOPE:
                self.playback_animation()

    def power_plot(self):
        title = "Signal Power over Time"
        x_data = self.time_index
        x_axis = "Time (s)"
        y_data = [self.plot_df["power"]]
        y_axis = "Power (dBm)"
        file = f"{self.params.output_file}_iq_power"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def voltage_plot(self):
        title = "Signal Voltage over Time"
        x_data = self.time_index
        x_axis = "Time (s)"
        y_data = [self.plot_df["voltage"]]
        y_axis = "Voltage (mV)"
        file = f"{self.params.output_file}_iq_voltage"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def phase_plot(self):
        self.calculate_phase()
        title = "Signal Phase over Time"
        x_data = self.time_index
        x_axis = "Time (s)"
        y_data = [self.plot_df["phase"]]
        y_axis = "Phase (°)"
        file = f"{self.params.output_file}_iq_phase"
        self.plotter.simple_plot(title, x_data, y_data, x_axis, y_axis, file)

    def oscillogram(self):
        data = self._prepare_osc_data()
        title = "Oscillogram"
        x_axis = "Short Time (ms)"
        y_axis = "Long Time (ms)"
        z_axis = "Power (dBm)"
        power_min = self.params.pwr_min_dbm
        power_max = self.params.pwr_max_dbm
        file = f"{self.params.output_file}_iq_oscillogram"
        self.plotter.intensity_plot(title, data, x_axis, y_axis, z_axis, file, power_min, power_max)

    def playback_animation(self):
        data = self._prepare_osc_data()
        title = "Time Domain Animation"
        x_axis = "Time (ms)"
        y_axis = "Power (dBm)"
        power_min = self.params.pwr_min_dbm
        power_max = self.params.pwr_max_dbm
        file = f"{self.params.output_file}_iq_oscope"
        self.plotter.animation(title, data, x_axis, y_axis, file, power_min, power_max)

    def _prepare_osc_data(self):
        data = None
        if not self.params.triggered:
            data = self._create_free_run_oscillogram()
        else:
            data = self._create_triggered_oscillogram()
        return data

    def _create_free_run_oscillogram(self):
        sweep_window = self._calculate_sweep_window()

        # Create 2 dimensional oscillogram power dataframe
        osc_power_df = pd.DataFrame()
        for sweep in range(0, len(self.plot_df.index), sweep_window):
            if sweep + sweep_window > len(self.plot_df.index):
                break
            column = str(sweep / self.iqdata.samplefreq * 1000)
            osc_power_df[column] = self.plot_df.loc[sweep:sweep + sweep_window - 1]["power"].tolist()
        osc_power_df = self.calculate_time(osc_power_df)
        return osc_power_df

    def _create_triggered_oscillogram(self):
        
        sweep_window = self._calculate_sweep_window()
        trigger_delay = self.calculate_trigger_delay()

        # Create 2 dimensional oscillogram power dataframe
        osc_power_df = pd.DataFrame()
        for sweep in range(0, len(self.plot_df.index), sweep_window):
            if sweep + sweep_window > len(self.plot_df.index):
                break
            trigger_index = self.get_trigger_index(self.plot_df.loc[sweep:sweep + sweep_window - 1].reset_index(drop=True), trigger_delay)
            start_index = sweep + trigger_index - trigger_delay
            stop_index = start_index + sweep_window - 1
            column = str(sweep / self.iqdata.samplefreq * 1000)
            if stop_index > len(self.plot_df.index):
                break
            osc_power_df[column] = self.plot_df.loc[start_index:stop_index]["power"].tolist()
        osc_power_df = self.calculate_time(osc_power_df)
        return osc_power_df

    def _calculate_sweep_window(self):
        return int(self.params.sweep_window_sec * self.iqdata.samplefreq)