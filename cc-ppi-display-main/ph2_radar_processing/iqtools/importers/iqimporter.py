"""
Module description
Created with help from:
http://www.science.smith.edu/dftwiki/index.php/PyQt5_Tutorial:_A_Window_Application_with_File_IO
"""

from abc import abstractmethod
import pandas as pd


class IqSingleton:
    """
    Use Singleton design pattern to share data between
    all IQ Importer objects.
    """

    _shared_data = {}

    def __init__(self):
        self.__dict__ = self._shared_data


class IqImporter(IqSingleton):
    """
    Class to manage importers and 
    handle the importing of IQ data.
    """

    def __init__(self):
        """
        Initialization of import parameters
        """
        super().__init__()
        self._importertype = None
        self._deltatime = None
        self._samplerate = None
        self._iqdf = pd.DataFrame()
        self._iqraw = pd.DataFrame()
        self._inputfile = None
        self._centerghz = None
        self._scalefactor = None
        self._fileextension = None
        self._datatype = None
        self._referencelevel = None

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
        :param file: file to be imported
        :type file: str
        """
        if self.is_valid(file):
            self._inputfile = file
        else:
            raise ImportError

    @property
    def importertype(self):
        """
        Getter method for importertype property
        """
        return self._importertype

    @property
    def deltatime(self):
        """
        Getter method for deltatime property
        """
        return self._deltatime

    @property
    def samplefrequency(self):
        """
        Getter method for samplefrequency property
        """
        return self._samplerate

    @property
    def iqdf(self):
        """
        Getter method for iqdf property
        """
        return self._iqdf

    @property
    def fileextension(self):
        """
        Getter method for fileextension property
        """
        return self._fileextension

    @property
    def centerghz(self):
        """
        Getter method for centerghz property
        """
        return self._centerghz

    def is_valid(self, file):
        """
        Returns True if the file exists and can be
        opened. Returns False otherwise.
        :param file: file to be checked
        :type file: str
        """
        try:
            file = open(file, "r")
            file.close()
            return True
        except (FileNotFoundError, TypeError) as e:
            return False

    def _reset_class_variables(self):
        """
        Helper method resets class variables that are
        set when importing IQ.
        """
        self._deltatime = None
        self._samplerate = None
        self._iqdf = None
        self._centerghz = None
        self._scalefactor = None

    def import_iq(self):
        """
        Method to grab IQ data from PXI files
        """
        if not self.is_valid(self.inputfile):
            return ("Error", "Invalid data path")
        self._reset_class_variables()
        try:
            self._read_header()
            self._read_iq()
        except FileNotFoundError:
            return ("Error", "Invalid data path")

        if self.valid_import():
            return ("Success", "Import successfull")
        return ("Error", "Files are empty")

    def valid_import(self):
        """
        Verifies IQ import completed successfully
        """
        if self._deltatime and self._iqdf.size > 0:
            return True
        return False

    @abstractmethod
    def _read_header(self):
        pass

    @abstractmethod
    def _read_iq(self):
        pass
