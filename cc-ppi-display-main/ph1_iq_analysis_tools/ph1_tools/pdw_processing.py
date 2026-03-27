import numpy as np
import pandas as pd

from iqtools.datastructures.iqdata import IQData
from iqtools.pdwmanager import PdwManager


def generate_pulse_start_times(config: dict, iqdata: IQData):
    manage = PdwManager()
    settings = config["ph1_settings"]["pulse_detection"]
    settings["input_file"] = config["files"]["radar_iq"]
    # settings["filename"] = config["files"]["output_schedule"][:-4] # drop the ".csv"
    settings["output_dir"] = config["files"]["output_folder"]
    manage.update_settings(settings)

    manage.data = iqdata
    manage.generate_pdws()
    
    return manage.plotter.pulse_df

def update_for_block_offset(pulse_df: pd.DataFrame, time_offset: float):
    pulse_df["pulse_start_time(us)"] = pulse_df["pulse_start_time(us)"] + time_offset
    pulse_df["pulse_end_time(us)"] = pulse_df["pulse_end_time(us)"] + time_offset
    return pulse_df

def restructure_to_dwells(config: dict, pulse_df: pd.DataFrame, samplerate: float, block: int):
    #files = config["files"]
    minimum_dwell = config["ph1_settings"]["radar"]["min_dwell_length_us"]
    maximum_dwell = config["ph1_settings"]["radar"]["max_dwell_length_us"]
    maximum_pri_samples = maximum_dwell * samplerate / 1e6
    sample_offset = (block - 1) * config["files"]["block_size_samples"]
    #try: block_offset = files["block_offset"]
    #except: block_offset=0
    #sample_offset = sample_offset + block_offset
    time_offset = sample_offset / samplerate * 1e6
    pulse_df = update_for_block_offset(pulse_df, time_offset)
    try:
        offset_pw = config["ph1_settings"]["radar"]["offset_pw_us"]
        main_pw = config["ph1_settings"]["radar"]["main_pw_us"]
        tol = 1 #us
        use_pp = True
    except:
        use_pp = False
    try:
        minimum_pw = config["ph1_settings"]["radar"]["min_pw_us"]
        maximum_pw = config["ph1_settings"]["radar"]["max_pw_us"]
        use_pw = True
    except:
        use_pw = False

    current_dwell_start = -minimum_dwell
    current_dwell_index = 0
    dwell_pulse_count = 1
    dt = 1 / samplerate
    pulse_df["keep"] = False

    if use_pw:
        pulse_df=pulse_df[(minimum_pw<pulse_df["pulse_width(us)"]) & (maximum_pw>pulse_df["pulse_width(us)"])] #DO NOT REINDEX
    prev_index=0

    for index, row in pulse_df.iterrows():
        if row["pulse_start_time(us)"] - current_dwell_start < minimum_dwell:
            dwell_pulse_count += 1
            pulse_df["keep"].loc[index] = False
            prev_index=index
            continue
        if dwell_pulse_count == 1:
            current_dwell_start = row["pulse_start_time(us)"]
            current_dwell_index = prev_index = index
            pulse_df.loc[index, "keep"] = True
            continue
        pulse_df["pulse_end_time(us)"].loc[current_dwell_index] = pulse_df["pulse_end_time(us)"].loc[prev_index]
        pulse_df["pulse_end_index"].loc[current_dwell_index] = pulse_df["pulse_end_index"].loc[prev_index]
        pulse_df["pri_end_index"].loc[current_dwell_index] = pulse_df["pri_end_index"].loc[prev_index]
        current_dwell_start = row["pulse_start_time(us)"]
        current_dwell_index = prev_index = index
        dwell_pulse_count = 1
        pulse_df["keep"].loc[index] = True

    pulse_df["pri_end_index"] = (pulse_df["pulse_start_index"] + maximum_pri_samples).where(pulse_df["pri_end_index"] - pulse_df["pulse_start_index"] > maximum_pri_samples, pulse_df["pri_end_index"])
    pulse_df = pulse_df[pulse_df["keep"] == True].reset_index()
    pulse_df = pulse_df.drop("keep", axis=1)
    pulse_df["coherent pulse width(us)"] = (pulse_df["pulse_end_index"] - pulse_df["pulse_start_index"]) * dt * 1e6
    pulse_df["pri(us)"] = (pulse_df["pri_end_index"] - pulse_df["pulse_start_index"]) * dt * 1e6

    if use_pp: #special case for doublets
        num_offset_samples = int(offset_pw * samplerate / 1e6)
        test = main_pw + offset_pw
        for index, row in pulse_df.iterrows():
            if (row["coherent pulse width(us)"] > (test - tol)) and (row["coherent pulse width(us)"] < (test + tol)):
                pulse_df["coherent pulse width(us)"].loc[index] = row["coherent pulse width(us)"] - offset_pw
                pulse_df["pulse_start_index"].loc[index] = row["pulse_start_index"] + num_offset_samples #assumes main pw already included in pulse_end
                pulse_df["pulse_start_time(us)"].loc[index] = row["pulse_start_time(us)"] + offset_pw
                try: #use try in case of offset pri_end_index exceeding values in current block
                    pulse_df["pri_end_index"].loc[index] = row["pri_end_index"] + num_offset_samples 
                    #note PRI for doublet should be the same so no PRI correction needed
                except:
                    pulse_df["pri_end_index"].loc[index] = row["pri_end_index"]

    return pulse_df

def add_azimuth_location(config: dict, pulse_df: pd.DataFrame):
    az_block_size = config["radar"]["antenna_az_block_size_deg"]
    az_stare_time_us = config["radar"]["az_stare_time_us"]
    az_calibration = config["radar"]["antenna_azimuth_calibration_offset"]
    jam_az = config["scenario"]["jammer_azimuth_deg"]
    skin_az = config["scenario"]["skin_azimuth_deg"]

    pulse_df["beam_azimuth"] = (np.floor_divide(pulse_df["pulse_start_time(us)"], az_stare_time_us) * az_block_size + az_calibration) % 360
    pulse_df["jam_az"] = (jam_az - pulse_df["beam_azimuth"] + 360) % 360
    pulse_df["skin_az"] = (skin_az - pulse_df["beam_azimuth"] + 360) % 360

    return pulse_df

