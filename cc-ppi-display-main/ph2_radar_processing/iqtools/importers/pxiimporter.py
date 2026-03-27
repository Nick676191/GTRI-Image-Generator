"""
Module description
"""
import os
import pandas as pd
import numpy as np

from .iqimporter import IqImporter


class PxiImporter(IqImporter):
    """
    Class description
    """

    def __init__(self):
        """
        Initialize the super class
        """
        super().__init__()
        self._importertype = "NI PXI"
        self._fileextension = ".dat"
        self._offset = None

    def _reset_class_variables(self):
        """
        Helper method resets class variables that are
        set when importing IQ.
        """
        super()._reset_class_variables()
        self._offset = None

    def __scale_iq_data(self, iqval):
        iqval = iqval * self._scalefactor + self._offset * 1.0
        return iqval

    def _read_header(self):
        """
        Helper method to read in header data of PXI
        binary file.
        """
        dt_pxi_header = np.dtype(
            [("dt", ">f8"), ("offset", ">f8"), ("gain", ">f8")]
        )
        # Read in the header to grab gain, offset, and delta time
        data_pxi_header = np.fromfile(
            self._inputfile, dtype=dt_pxi_header, count=1
        )
        self._deltatime, self._offset, self._scalefactor = data_pxi_header[0]
        self._samplerate = 1.0 / self._deltatime

    def _read_iq(self):
        """
        Helper method to read in IQ data of PXI
        binary file.
        """
        opened_file = open(self._inputfile, "rb")
        opened_file.seek(24, os.SEEK_SET)

        dt_iq = np.dtype([("I", ">i2"), ("Q", ">i2")])

        data_iq = np.fromfile(opened_file, dtype=dt_iq)
        dataframe = pd.DataFrame(data_iq, columns=data_iq.dtype.names)

        self._iqraw = dataframe
        # scale data to fit standard IQ data
        dataframe = dataframe.apply(self.__scale_iq_data)
        self._iqdf = dataframe
