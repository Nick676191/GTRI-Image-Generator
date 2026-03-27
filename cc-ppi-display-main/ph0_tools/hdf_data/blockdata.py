import numpy as np
import pandas as pd

import h5py


class BlockData():
    def __init__(self):
        self.file = ""
        self.hdf5_handle = None
        self.dwells = []
        self.iq = None
        self.powers = None
        self.sample_rate = None
        self.timestamps = None

    def import_data(self):
        self.hdf5_handle = h5py.File(self.file, "r")
        self.dwells = list(self.hdf5_handle.keys())
        self.sample_rate = self.hdf5_handle.attrs["sample_frequency(hz)"]

    def get_dwell_iq(self, dwell: str):
        data_type = np.dtype([('I', '<f8'), ('Q', '<f8')])
        np_iq = np.array(self.hdf5_handle[dwell], dtype=data_type)
        self.iq = pd.DataFrame(np_iq, columns=["I", "Q"])
        lin_powers = self.iq.I**2 + self.iq.Q**2
        self.powers = 10*np.log(lin_powers.values)
        total_time = len(self.powers) / self.sample_rate
        self.timestamps = np.arange(0, total_time, 1 / self.sample_rate)