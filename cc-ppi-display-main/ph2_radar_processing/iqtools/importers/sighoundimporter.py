"""
Module description
"""
from math import sqrt
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

from .iqimporter import IqImporter


class SigHoundImporter(IqImporter):
    """
    Class description
    """

    def __init__(self):
        """
        Initialize the super class
        """
        super().__init__()
        self._importertype = "Signal Hound"
        self._fileextension = ".iq"
        self._xmlinputfile = None
        self._iqinputfile = None

    @IqImporter.inputfile.setter
    def inputfile(self, file):
        """
        Setter method for inputfile property
        """
        if self.is_valid(file) and self.is_valid(file.replace(".iq", ".xml")):
            self._inputfile = file.replace(".iq", ".xml")
            self._xmlinputfile = file.replace(".iq", ".xml")
            self._iqinputfile = file
        elif self.is_valid(file) and not self.is_valid(
            file.replace(".iq", ".xml")
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
        self._samplerate = np.float64(doc.find("SampleRate").text)
        self._deltatime = 1.0 / self._samplerate
        self._scalefactor = float(doc.find("ScaleFactor").text)
        self._centerghz = float(doc.find("CenterFrequency").text) / ghzoffset
        self._datatype = str(doc.find("DataType").text)
        self._numberofsamples = float(doc.find("SampleCount").text)
        self._referencelevel = float(doc.find("ReferenceLevel").text)
        start_time = 0
        time_diff = self._numberofsamples / self._samplerate

        return start_time, time_diff, (1/self._samplerate)

    def __scale_iq_data(self, iqval):
        """
        Helper method to scale IQ read into dataframe to
        a comparable factor to work with.
        Received IQ resolution of 15 bits and need a
        resolution of 16 bits.
        """
       
        if self._datatype == "Complex Short":
            iqval = ( iqval / 32768.0) #convert to float and scale 
            iqval *= self._scalefactor
    
        return iqval

    def _read_iq(self):
        """
        Helper method to read in IQ data from the iq file.
        Sets the IQ dataframe once imported.
        """
        iqf = open(self._iqinputfile, "rb")

        if self._datatype == "Complex Short":
            dt_iq = np.dtype([("I", "<i2"), ("Q", "<i2")])
        elif self._datatype == "Complex Float":
            dt_iq = np.dtype([("I", "<f4"), ("Q", "<f4")])

        data_iq = np.fromfile(iqf, dtype=dt_iq)
        dataframe = pd.DataFrame(data_iq, columns=data_iq.dtype.names)
        

        # scale data to fit standard IQ data
        if self._datatype == "Complex Short": # scale only when data is stored as complex short
            dataframe = dataframe.apply(self.__scale_iq_data)
        self._iqdf = dataframe
