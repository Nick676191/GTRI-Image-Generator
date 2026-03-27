"""
Use this module to handle and store all configuration data
for the application. This module should handle all JSON
importing and exporting for settings data as well as
handle reconfiguring the GUI.
"""

from dataclasses import dataclass, field
from enum import Enum


class PlotCenter(Enum):
    """
    Enum for centering frequency plots
    """
    BASEBAND = 0
    DUC = 1

class PlotOutput(Enum):
    """
    Enum defining plot output type to use
    """
    STATIC = 0
    HTML = 1

class FrequencyPlots(Enum):
    """
    Enum defining all frequency plots
    """
    SPECTOGRAM = 0
    SPECTRUM_GIF = 1

class TimePlots(Enum):
    """
    Enum defining all time plots
    """
    OSCILLOGRAM = 0
    IQPOWER = 1
    IQVOLTS = 2
    IQPHASE = 3
    OSCOPE = 4

class PDWPlots(Enum):
    """
    Enum defining all pdw plots
    """
    PW = 0
    PRI = 1
    POWER = 2
    PHASE = 3
    FREQUENCY = 4

class SampleLimit(Enum):
    """
    Enum defining the sample limit type used
    """
    MEGABYTES = 0
    MEGASAMPLES = 1


@dataclass
class GeneralSettings():
    """
    General settings used for IQ analysis
    """
    input_file: str = ""
    output_file: str = ""
    output_dir: str = ""
    sample_limit: float = 0
    sample_limit_type: SampleLimit = SampleLimit.MEGABYTES
    sample_offset: int = 0
    triggered: bool = False
    trigger_delay_sec: float = 0.0001
    trigger_level_dbm: float = -30
    analysis_dur_sec: float = 1
    analysis_del_sec: float = 0
    pwr_max_dbm: float = 0
    pwr_min_dbm: float = -100

    def deserialize(self, obj):
        """
        Deserializes provided dictionary into this object
        """
        self.input_file = add_optional_field(obj, "input_file", self.input_file)
        self.output_file = add_optional_field(obj, "filename", self.output_file)
        self.output_dir = add_optional_field(obj, "output_dir", self.output_dir)
        self.sample_limit = add_optional_field(obj, "sample_limit", self.sample_limit)
        if get_optional_value(obj, "sample_limit_type") is not None:
            self.sample_limit_type = SampleLimit[get_optional_value(obj, "sample_limit_type")]
        self.sample_offset = add_optional_field(obj, "sample_offset", self.sample_offset)
        self.triggered = True if get_optional_value(obj, "trigger_type") == "Triggered" else False
        self.trigger_delay_sec = add_optional_field(obj, "trigger_delay_sec", self.trigger_delay_sec)
        self.trigger_level_dbm = add_optional_field(obj, "trigger_level_dBm", self.trigger_level_dbm)
        self.pwr_max_dbm = add_optional_field(obj, "pwr_max_dbm", self.pwr_max_dbm)
        self.pwr_min_dbm = add_optional_field(obj, "pwr_min_dbm", self.pwr_min_dbm)
        self.analysis_dur_sec = add_optional_field(obj, "analysis_duration_sec", self.analysis_dur_sec)
        self.analysis_del_sec = add_optional_field(obj, "analysis_delay_sec", self.analysis_del_sec)

        plot_option = get_optional_value(obj, "plot_option")
        if plot_option == "Static Window":
            self.plot_output = PlotOutput.STATIC
        elif plot_option == "Interactive HTML":
            self.plot_output = PlotOutput.HTML

    def serialize(self):
        """
        Serializes this object and returns it as a dictionary
        """
        obj = {}
        obj["input_file"] = self.input_file
        obj["filename"] = self.output_file
        obj["output_dir"] = self.output_dir
        obj["sample_limit"] = self.sample_limit
        obj["sample_limit_type"] = self.sample_limit_type.name
        obj["sample_offset"] = self.sample_offset
        obj["trigger_type"] = "Triggered" if self.triggered else "Free Run"
        obj["trigger_delay_sec"] = self.trigger_delay_sec
        obj["trigger_level_dBm"] = self.trigger_level_dbm
        obj["pwr_max_dbm"] = self.pwr_max_dbm
        obj["pwr_min_dbm"] = self.pwr_min_dbm
        obj["analysis_duration_sec"] = self.analysis_dur_sec
        obj["analysis_delay_sec"] = self.analysis_del_sec
        if self.plot_output == PlotOutput.STATIC:
            obj["plot_option"] = "Static Window"
        elif self.plot_output == PlotOutput.HTML:
            obj["plot_option"] = "Interactive HTML"
        return obj


@dataclass
class TimeSettings(GeneralSettings):
    """
    Settings used for time domain analysis
    """
    sweep_window_sec: float = 0.002
    plot_selection: set = field(default_factory=set)

    def deserialize(self, obj):
        """
        Deserializes provided dictionary into this object
        """
        super().deserialize(obj)
        self.sweep_window_sec = add_optional_field(obj, "sweep_window_sec", self.sweep_window_sec)
        self.plot_selection = add_optional_field(obj, "plots", self.plot_selection)

    def serialize(self):
        """
        Serializes this object and returns it as a dictionary
        """
        obj = super().serialize()
        obj["sweep_window_sec"] = self.sweep_window_sec
        obj["plots"] = [plot.name for plot in self.plot_selection]
        return obj


@dataclass
class FrequencySettings(GeneralSettings):
    """
    Settings used for frequency domain analysis
    """
    rbw_hz: float = 3000
    span_hz: float = 1e4
    center_freq_hz: float = 1e9
    plot_center: PlotCenter = PlotCenter.BASEBAND
    plot_selection: set = field(default_factory=set)
    real_time_gif: bool = True

    def deserialize(self, obj):
        """
        Deserializes provided dictionary into this object
        """
        super().deserialize(obj)
        self.rbw_hz = add_optional_field(obj, "rbw_hz", self.rbw_hz)
        self.span_hz = add_optional_field(obj, "span_hz", self.span_hz)
        self.center_freq_hz = add_optional_field(obj, "f_c_iq_hz", self.center_freq_hz)
        bb_duc_choice = get_optional_value(obj, "bb_duc_choice")
        self.plot_center = PlotCenter[bb_duc_choice] if bb_duc_choice is not None else self.plot_center
        self.real_time_gif = add_optional_field(obj, "real_time_gif", self.real_time_gif)
        self.plot_selection = add_optional_field(obj, "plots", self.plot_selection)

    def serialize(self):
        """
        Serializes this object and returns it as a dictionary
        """
        obj = super().serialize()
        obj["rbw_hz"] = self.rbw_hz
        obj["span_hz"] = self.span_hz
        obj["f_c_iq_hz"] = self.center_freq_hz
        obj["bb_duc_choice"] = self.plot_center.name
        obj["real_time_gif"] = self.real_time_gif
        obj["plots"] = [plot.name for plot in self.plot_selection]
        return obj

@dataclass
class PDWSettings(GeneralSettings):
    """
    Settings used for pdw analysis
    """
    hysteresis_enabled: bool = False
    hysteresis_count: int = 5
    plot_selection: set = field(default_factory=set)

    def deserialize(self, obj):
        """
        Deserializes provided dictionary into this object
        """
        super().deserialize(obj)
        self.hysteresis_enabled = add_optional_field(obj, "hyst_bool", self.hysteresis_enabled)
        self.hysteresis_count = add_optional_field(obj, "hyst_level", self.hysteresis_count)
        self.plot_selection = add_optional_field(obj, "plots", self.plot_selection)

    def serialize(self):
        """
        Serializes this object and returns it as a dictionary
        """
        obj = super().serialize()
        obj["hyst_bool"] = self.hysteresis_enabled
        obj["hyst_level"] = self.hysteresis_count
        obj["plots"] = [plot.name for plot in self.plot_selection]
        return obj

def add_optional_field(obj, name, variable):
    """
    Helper function for filling in instance variables with optional fields from an object
    """
    try:
        return obj[name]
    except KeyError as err:
        # print("Key not found: ", err)
        return variable

def get_optional_value(obj, name):
    try:
        return obj[name]
    except KeyError as err:
        # print("Key not found: ", err)
        return None

def get_optional_field(obj, name, value):
    """
    Helper function for retrieving instance variables that may be optional for the object
    """
    if value is None:
        return
    if isinstance(value, list):
        if value == 0:
            return
    if isinstance(value, set):
        if value == 0:
            return
    obj[name] = value


class ConfigurationHandler():
    """
    Use this class to store common data across tabs
    """

    def __init__(self):
        """
        Add function comment
        """
        super().__init__()
        self.globaldict = GeneralSettings()
        self.freqdict = FrequencySettings()
        self.timedict = TimeSettings()
        self.pdwdict = PDWSettings()
