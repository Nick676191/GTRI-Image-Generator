import logging
import datetime
from pathlib import Path

import pandas as pd

from iqtools.datastructures.iqdata import IQData
from ph1_tools import pdw_processing
from ph1_tools import iq_processing
from ph1_tools import file_handler


def calculate_blocks(config):
    blocks_to_read = config["files"]["blocks_to_read"]
    samples_to_read = config["files"]["block_size_samples"]
    block_delay = config["files"]["block_delay"]
    blocks_to_read += block_delay
    if blocks_to_read <= 0:
        file_size_bytes = Path(config["files"]["radar_iq"]).stat().st_size
        blocks_to_read = int(file_size_bytes / samples_to_read / 4) - block_delay
    return blocks_to_read, block_delay

def import_iq(config, block: int = 0):
    phase = "Import IQ"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    files = config["files"]
    samples_to_read = files["block_size_samples"]
    read_offset = (block - 1) * samples_to_read
    try: block_offset = files["block_offset"]
    except: block_offset=0
    read_offset = read_offset + block_offset
    
    radar_iq = IQData()
    radar_iq.set_importer(Path(files["radar_iq"]).suffix)
    radar_iq.set_importer_settings(samples_to_read, read_offset)
    radar_iq.importer.inputfile = files["radar_iq"]
    radar_iq.import_iq()

    jam_iq = IQData()
    jam_iq.set_importer(Path(files["jammer_iq"]).suffix)
    radar_iq.set_importer_settings(samples_to_read, read_offset)
    jam_iq.importer.inputfile = files["jammer_iq"]
    jam_iq.import_iq()  

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return radar_iq, jam_iq


def bpf(config: dict, radar_iq: IQData, jam_iq: IQData):
    if not config["ph1_settings"]["actions"]["bandpassfilter"]:
        return radar_iq, jam_iq
    
    phase = "Bandpass Filtering"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))
    
    filter = config["ph1_settings"]["bandpassfilter"]

    #sosfiltfilt bandpass is the most robust filter after reviewing sources and performing tests
    #TODO:  still has issues when setting bw for values on edge of recording bw; overrides this issue with lowpass
    radar_iq = iq_processing.bandpassSOS(radar_iq, filter)
    jam_iq = iq_processing.bandpassSOS(jam_iq, filter)

    # downconversion = config["ph1_settings"]["bandpassfilter"]
    # logging.info("Downconverting...")
    # radar_iq = iq_processing.downconvert(radar_iq, downconversion)
    # jam_iq = iq_processing.downconvert(jam_iq, downconversion)
    # logging.info("Upconverting...")
    # radar_iq = iq_processing.upconvert(radar_iq, downconversion)
    # jam_iq = iq_processing.upconvert(jam_iq, downconversion)
    
    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return radar_iq, jam_iq
    
def windowf(config: dict, radar_iq: IQData, jam_iq: IQData):
    if not config["ph1_settings"]["actions"]["windowfilter"]:
        return radar_iq, jam_iq
    
    phase = "Other Filtering"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))
    
    filter = config["ph1_settings"]["windowfilter"]

    radar_iq = iq_processing.windowFilter(radar_iq, filter)
    jam_iq = iq_processing.windowFilter(jam_iq, filter)
    
    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return radar_iq, jam_iq

def apply_power_calibration(config: dict, radar_iq: IQData, jammer_iq: IQData):
    phase = "Power Calibration"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    scenario = config["ph1_settings"]["scenario"]
    radar_iq, jammer_iq = iq_processing.apply_power_calibration(scenario, radar_iq, jammer_iq)
    
    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return radar_iq, jammer_iq

def pulse_detection(config: dict, radar_iq: IQData):
    phase = "Pulse Detection"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    pulse_df = pdw_processing.generate_pulse_start_times(config, radar_iq)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return pulse_df

def range_effects(config: dict, radar_iq: IQData, jam_iq: IQData):
    if (not config["ph1_settings"]["actions"]["range_loss"] and 
        not config["ph1_settings"]["actions"]["range_delay"]):
        return radar_iq, jam_iq
    
    phase = "Range Effects"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    scenario = config["ph1_settings"]["scenario"]
    if config["ph1_settings"]["actions"]["range_loss"]:
        radar_iq, jam_iq = iq_processing.apply_range_loss_effects(scenario, radar_iq, jam_iq)
    if config["ph1_settings"]["actions"]["range_delay"]:
        radar_iq, jam_iq = iq_processing.apply_range_delay_effects(scenario, radar_iq, jam_iq)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return radar_iq, jam_iq

def dwell_split_calc(config: dict, pulse_df: pd.DataFrame, samplerate: float, block: int):
    phase = "Dwell Split Calcuations"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    pulse_df = pdw_processing.restructure_to_dwells(config, pulse_df, samplerate, block)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")
    
    return pulse_df

def pointing_angle_calc(config: dict, pulse_df: pd.DataFrame):
    phase = "Pointing Angle Calcuations"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    ph1_settings = config["ph1_settings"]
    pulse_df = pdw_processing.add_azimuth_location(ph1_settings, pulse_df)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")
    
    return pulse_df

def apply_antenna(config: dict, pulse_df: pd.DataFrame, radar_iq: IQData, jam_iq: IQData):
    if not config["ph1_settings"]["actions"]["antenna_effects"]:
        return radar_iq, jam_iq
    
    phase = "Apply Antenna"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    radar_iq, jam_iq = iq_processing.apply_antenna(config, pulse_df, radar_iq, jam_iq)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")
    
    return radar_iq, jam_iq

def add_skin(config: dict, radar_iq: IQData, jam_iq: IQData):
    if not config["ph1_settings"]["actions"]["skin_return"]:
        return jam_iq

    phase = "Add Skin Return"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    scenario = config["ph1_settings"]["scenario"]
    return_iq = iq_processing.add_skin_return(scenario, radar_iq, jam_iq)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

    return return_iq

def plot_radar_iq(config: dict, radar_iq: IQData, block: int):
    if not config["ph1_settings"]["actions"]["signal_plotting"]:
        return

    phase = "Radar IQ Plotting"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    iq_processing.generate_output_plots(config, radar_iq, f"Radar_{block}")

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")


def plot_return_iq(config: dict, return_iq: IQData, block: int):
    if not config["ph1_settings"]["actions"]["signal_plotting"]:
        return

    phase = "Return IQ Plotting"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    iq_processing.generate_output_plots(config, return_iq, f"Return_{block}")

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

def export_dwell_schedule(config: dict, pulse_df: pd.DataFrame, block: int):
    phase = "Exporting Dwell Schedule"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    file_handler.export_dwell_schedule(config, pulse_df, block)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")


def export_iq_dwells(config: dict, pulse_df: pd.DataFrame, return_iq: IQData, block: int):
    phase = "Exporting to HDF5"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    file_handler.produce_transmit_pulse_hdf5(config, pulse_df, block)
    file_handler.produce_receive_pulse_hdf5(config, pulse_df, return_iq, block)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")

def create_reference_hdf5_files(config: dict, blocks: int, block_offset: int):
    phase = "Creating reference HDF5"
    logging.info("{} Start: {}".format(phase, datetime.datetime.now()))

    file_handler.create_reference_hdf5(config, blocks, block_offset)

    logging.info("{} End: {}".format(phase, datetime.datetime.now()))
    logging.info("----------------------------------------")
