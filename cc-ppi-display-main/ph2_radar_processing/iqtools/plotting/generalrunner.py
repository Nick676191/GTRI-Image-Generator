import numpy as np
import pandas as pd
from pathlib import Path
from iqtools.plotting.simple_plotter import MplPlotter, PlotlyPlotter

from iqtools.datastructures.configsettings import GeneralSettings, PlotOutput
from iqtools.datastructures.iqdata import IQData

pd.options.mode.chained_assignment = None  # default='warn'

PLOTTER_TYPES = {
    PlotOutput.HTML: PlotlyPlotter,
    PlotOutput.STATIC: MplPlotter
}


class GeneralRunner():
    
    def __init__(self, params, data):
        self.params: GeneralSettings = None
        self.iqdata: IQData = None
        self.sig_data: pd.DataFrame = None
        self.plot_df: pd.DataFrame = None
        self.time_index = None

    def prepare_plot_data(self):
        if not self.params.triggered:
            self.create_free_run_array()
        else:
            self.create_triggered_array()

        self.plotter = PLOTTER_TYPES[self.params.plot_output]()
        self.add_time_index()
        self.add_output_file_name()

    def add_time_index(self):
        self.time_index = self.plot_df.index / self.iqdata.samplefreq

    def add_output_file_name(self):
        self.params.output_file = Path(self.params.output_dir).joinpath(self.params.output_file)

    def get_analysis_delay(self):
        return int(self.params.analysis_del_sec * self.iqdata.samplefreq)

    def get_analysis_length(self):
        return int(self.params.analysis_dur_sec * self.iqdata.samplefreq)

    def calculate_trigger_delay(self):
        return int(self.params.trigger_delay_sec * self.iqdata.samplefreq)

    def calculate_time(self, data: pd.DataFrame):
        #convert to milliseconds
        data = data.assign(time = data.index / self.iqdata.samplefreq * 1000)
        data = data.set_index('time')
        return data

    def calculate_power(self):
        self.calculate_voltage()
        voltage = self.plot_df["voltage"]
        pwr = 10 * np.log10(voltage)
        self.plot_df = self.plot_df.assign(power = pwr)

    def calculate_voltage(self):
        voltage_array = np.array(self.plot_df["I"] ** 2 + self.plot_df["Q"] ** 2)
        self.plot_df = self.plot_df.assign(voltage = voltage_array)
        self.fill_in_noise_floor()

    def calculate_phase(self):
        i_data = self.plot_df["I"]
        q_data = self.plot_df["Q"]

        radian_phase = np.arctan2(q_data, i_data)

        phs = np.degrees(radian_phase)

        self.plot_df = self.plot_df.assign(phase = phs)

    def fill_in_noise_floor(self):
        # Provide a noise floor for data
        noise_floor = 1e-15
        self.plot_df["voltage"][self.plot_df["voltage"] < noise_floor] = noise_floor

    def create_free_run_array(self):
        # Trim down to just the data to be plotted
        analysis_delay = self.get_analysis_delay()
        analysis_length = self.get_analysis_length()
        start_index = analysis_delay
        stop_index = start_index + analysis_length

        self.plot_df = self.sig_data.loc[start_index:stop_index].reset_index(drop=True)

        self.calculate_power()

    def create_triggered_array(self):

        # Ignore data before the analysis delay
        analysis_delay = self.get_analysis_delay()
        analysis_length = self.get_analysis_length()
        trigger_delay = self.calculate_trigger_delay()
        start_index = analysis_delay
        self.plot_df = self.sig_data.loc[start_index:].reset_index(drop=True)

        self.calculate_power()

        # Trim down to the plot data after finding a trigger
        trigger_index = self.get_trigger_index(self.plot_df[trigger_delay:], trigger_delay)
        start_index = trigger_index - trigger_delay
        stop_index = start_index + analysis_length
        self.plot_df = self.plot_df.loc[start_index:stop_index].reset_index(drop=True)

    def get_trigger_index(self, data: pd.DataFrame, trigger_delay: float):

        # Find locations below the trigger level
        floor = data.index[  data["power"] < self.params.trigger_level_dbm].tolist()
        if len(floor) == 0:
            print("Data could not be triggered.")
            return trigger_delay

        # Find the first transition from low to high to trigger upon
        analysis_data = data.loc[floor[0]:]
        triggers = analysis_data.index[analysis_data["power"] > self.params.trigger_level_dbm].tolist()
        if len(triggers) == 0:
            print("Data could not be triggered.")
            return trigger_delay
        
        #Found trigger
        trigger_index = triggers[0]
        if trigger_index > trigger_delay:
            return trigger_index
        return trigger_delay