"""
Module description
"""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

from .iqimporter import IqImporter


class HDF5Importer(IqImporter):
    """
    Class description
    """

    def __init__(self):
        """
        Initialize the super class
        """
        super().__init__()
        self._importertype = "HDF5"
        self._fileextension = ".hdf"
        self._xmlinputfile = None
        self._iqinputfile = None

    @IqImporter.inputfile.setter
    def inputfile(self, file):
        """
        Setter method for inputfile property
        """
        if self.is_valid(file) and self.is_valid(file.replace(".hdf", ".xhdf")):
            self._inputfile = file.replace(".hdf", ".xhdf")
            self._xmlinputfile = file.replace(".hdf", ".xhdf")
            self._iqinputfile = file
        elif self.is_valid(file) and not self.is_valid(
            file.replace(".hdf", ".xhdf")
        ):
            raise ReferenceError
        else:
            raise ImportError

    def _read_header(self):
        """
        Helper method to parse XML file for important fields.
        Sets object fields from parsed values.
        """
        ghzoffset = 1000000000.0

        # open xml and pull dt, gain, and iq file name
        doc = ET.parse(self._xmlinputfile)
        root = doc.getroot()
        captures = root.find("captures")
        capture = captures[0]
        data_files = root.find("data_files")
        data = data_files[0]
        self._samplerate = np.float64(capture.get("sample_rate"))
        self._deltatime = 1.0 / self._samplerate
        self._scalefactor = np.float64(capture.get("acq_scale_factor"))
        self._centerghz = np.float64(capture.get("center_frequency")) / ghzoffset
        self._datatype = str(data.get("data_encoding"))
        self._numberofsamples = np.float64(data.get("samples"))
        self._referencelevel = 20*np.log10(self._scalefactor**2)
        start_time = 0
        time_diff = self._numberofsamples / self._samplerate

        return start_time, time_diff, (1/self._samplerate)

    def _read_iq(self, *args, **kwargs):
        """
        Helper method to read in IQ data from the iq file.
        Sets the IQ dataframe once imported.
        """
        #If the user desires, they can bound the start and end index of the data frame 
        self._iqdf = pd.read_hdf(self._iqinputfile, "df")
