
from abc import abstractmethod
from pathlib import Path
from PyQt5.QtWidgets import QApplication
import sys

from iqtools.datastructures.configsettings import GeneralSettings

# Create app window for matplotlib plots
app = QApplication(list(sys.argv[0]))


class AnalysisManager():
    """
    Class to manage analysis of iqdata
    providing interface bridge to each
    analysis capability
    """

    def __init__(self, settings = None, data = None):
        """
        Initialization of parameters
        """
        self.settings: GeneralSettings = None
        self.analysis_type = None
        self.data = data
        self.initialize_settings(settings)
    
    def initialize_settings(self, settings):
        pass

    def update_settings(self, settings):
        if settings == None:
            print("no settings")
            return
        self.settings.deserialize(settings)

    def request_settings(self):
        return self.settings.serialize()

    @abstractmethod
    def execute(self, param):
        pass

    def importiq(self):
        self.data.settings = self.settings.serialize()
        self.data.set_importer(Path(self.settings.input_file).suffix)
        self.data.importer.inputfile = self.settings.input_file
        self.data.import_iq()
        return self.data.iqdf.head()

    def check_output_directory(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)