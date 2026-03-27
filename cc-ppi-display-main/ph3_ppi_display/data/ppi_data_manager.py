import numpy as np
import pandas as pd

class PPIData():
    def __init__(self):
        self.file = ""
        self.range_bin_size = None
        self.range_array = None
        self.max_range = None
        self.azimuth_step_size = None
        self.min_power = None
        self.azimuth_array = np.array([])
        self.timestamp_array = np.array([])
        self.power_level_dataframe = pd.DataFrame()

    def import_data(self):
        data = pd.read_csv(self.file, header=None)
        self.range_bin_size = float(data.iat[1, 1])
        self.azimuth_array = np.array(data.iloc[1:, 2], float)
        self.timestamp_array = np.array(data.iloc[1:, 0], float)
        self.power_level_dataframe = data.iloc[1:,4:].reset_index(drop=True)
        self.power_level_dataframe.columns = range(0, len(self.power_level_dataframe.columns))

        self.max_range = (len(self.power_level_dataframe.columns)-1) * self.range_bin_size
        self.range_array = np.linspace(0, self.max_range, num=len(self.power_level_dataframe.columns))
        self.azimuth_step_size = self.azimuth_array[1] - self.azimuth_array[0]
        self.min_power = self.power_level_dataframe.min().min()
        self.power_level_dataframe = self.power_level_dataframe.fillna(self.min_power)

        self.azimuth_array = np.arange(0,360 + self.azimuth_step_size,self.azimuth_step_size) * np.pi / 180

    def get_beam_data(self, timestamp, az_scan_rate):
        beam_angle = 360 / az_scan_rate * timestamp * np.pi / 180
        beam_data = [[beam_angle, beam_angle],
                     [0, self.max_range]]
        return beam_data

    def generate_data(self, timestamp, az_rate):
        closest_index = min(int(timestamp * 360 / az_rate / self.azimuth_step_size), len(self.power_level_dataframe))
        # closest_index = (np.abs(self.timestamp_array - timestamp)).argmin()
        total_angles = len(self.azimuth_array)
        total_range_bins = len(self.range_array)
        if closest_index < total_angles:
            radar_data = self.power_level_dataframe.iloc[:closest_index, :].copy()
            empty_data = pd.DataFrame(np.ones([total_angles - closest_index, total_range_bins])) * self.min_power
            plot_data = pd.concat([radar_data, empty_data]).reset_index(drop=True)
        else:
            angle_break = int(closest_index / (total_angles)) * (total_angles - 1)
            print(angle_break)
            data_block_a = self.power_level_dataframe.iloc[angle_break:closest_index, :].copy()
            data_block_b = self.power_level_dataframe.iloc[closest_index-total_angles:angle_break, :].copy()
            plot_data = pd.concat([data_block_a, data_block_b]).reset_index(drop=True)
        return plot_data.T