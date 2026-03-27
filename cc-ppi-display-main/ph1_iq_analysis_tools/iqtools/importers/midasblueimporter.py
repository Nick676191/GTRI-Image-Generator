"""
Module description
"""
import os
import pandas as pd
import numpy as np

from .iqimporter import IqImporter
from . import midas_parser as mp


class MidasBlueImporter(IqImporter):
    """
    Class description
    """

    def __init__(self):
        """
        Initialize the super class
        """
        super().__init__()
        self._importertype = "Midas Blue"
        self._fileextension = ".tmp"

    def _read_header(self):
        """
        Helper method to read in header data of PXI
        binary file.
        """

    def _read_iq(self):
        """
        Helper method to read in IQ data of PXI
        binary file.
        """
        headers, df = mp.midas_parser(self.inputfile)

        df = df.reset_index(drop=True)
        dt = headers["var"]["x_delta"]
        fs = 1 / dt

        self._iqdf = df
        self._deltatime = dt
        self._samplerate = fs
