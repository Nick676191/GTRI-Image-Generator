from iqtools.importers.sighoundimporter import SigHoundImporter
from iqtools.importers.pxiimporter import PxiImporter
from iqtools.importers.midasblueimporter import MidasBlueImporter
from iqtools.importers.xcomimporter import XcomImporter
from iqtools.importers.hdf5importer import HDF5Importer

from iqtools.datastructures.configsettings import ConfigurationHandler

import pandas as pd
import numpy as np


class IQData():
    """
    Class to store IQ data for use across
    tabs and to set and call the correct 
    importer.
    """

    def __init__(self):
        """
        Initialization of IQ data parameters
        """
        super().__init__()
        if len(self.__dict__) == 0:
            self.importerdict = {
                ".iq": SigHoundImporter,
                ".dat": PxiImporter,
                ".tmp": MidasBlueImporter,
                ".xdat": XcomImporter,
                ".hdf": HDF5Importer,
            }
            self.importer = None
            self._deltatime = None
            self._samplefreq = None
            self._iqdf = pd.DataFrame()
            self._inputfile = None
            self._centerghz = None
            self._fileextension = None
            self.imported = False

            self.cs = ConfigurationHandler()
            self.settings = {}

            # PDW Tab objects
            self._pulse_df = pd.DataFrame()
            self._signal_power = np.array([])

            # Freq. tab objects
            self._freqs = []

    def set_importer(self, ext):
        """
        Method to set the correct importer when the filetype 
        is changed.
        :param iqtype: filetype that is being imported
        :type iqtype: str
        """
        self.importer = self.importerdict[ext]()
        self._fileextension = self.importer.fileextension

    def import_iq(self):
        """
        Method to call importer and update
        IQ data
        """
        self.importer.import_iq()
        self._deltatime = self.importer.deltatime
        self._samplefreq = self.importer.samplefrequency
        self._iqdf = self.importer.iqdf
        self._inputfile = self.importer.inputfile
        self._centerghz = self.importer.centerghz
        self.imported = True

    @property
    def deltatime(self):
        """
        Getter method for deltatime property
        """
        return self._deltatime

    @property
    def samplefreq(self):
        """
        Getter method for samplefreq property
        """
        return self._samplefreq

    @property
    def iqdf(self):
        """
        Getter method for iqdf property
        """
        return self._iqdf

    @property
    def inputfile(self):
        """
        Getter method for inputfile property
        """
        return self._inputfile

    @inputfile.setter
    def inputfile(self, file):
        """
        Setter method for inputfile property
        """
        if file != "Please select an IQ data input file":
            if self.importer.is_valid(file):
                self._inputfile = file
                self.importer.inputfile = file
            else:
                raise ImportError

    @property
    def centerghz(self):
        """
        Getter method for centerghz property
        """
        return self._centerghz

    @property
    def fileextension(self):
        """
        Getter method for fileextension property
        """
        return self._fileextension

    @property
    def pulse_df(self):
        """Getter method for the pulse_df property"""
        return self._pulse_df

    @pulse_df.setter
    def pulse_df(self, df):
        """Setter method for the pulse_df property"""
        self._pulse_df = df

    @property
    def signal_power(self):
        """Getter method for the signal_power property"""
        return self._signal_power

    @signal_power.setter
    def signal_power(self, array):
        """Setter method for the signal_power property"""
        self._signal_power = array

    @property
    def freqs(self):
        """Getter method for the freqs property"""
        return self._freqs

    @freqs.setter
    def freqs(self, freqlist):
        """Setter method for the freqs property"""
        self._freqs = freqlist
