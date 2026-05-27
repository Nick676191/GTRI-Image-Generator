from pathlib import Path

import logging
import datetime
import numpy as np
import pandas as pd
import h5py

from ph2_tools import file_handling
from ph2_tools import calculations

plot = False

def perform_matched_filter_radar_processing(config):
    files = config["files"]
    tx_hdf5 = h5py.File(files["output_folder"] + "/" + "tx_reference.hdf5", "r")
    rx_hdf5 = h5py.File(files["output_folder"] + "/" + "rx_reference.hdf5", "r")
    outputfile = Path.joinpath(Path(files["output_folder"]), Path(files["output_returns"]))

    block_metadata = file_handling.get_blocks(tx_hdf5)
    
    max_pri_block_0 = rx_hdf5[block_metadata[0][0]].attrs["max pri(us)"] / 1e6
    sample_freq = file_handling.get_sample_freq(tx_hdf5)
    dwell_length = max_pri_block_0 * sample_freq
    num_range_bins = config["ph2_settings"]["num_range_bins"]

    decimation_factor, range_bin_size = calculations.calculate_decimation_factor(max_pri_block_0, sample_freq, num_range_bins)

    block_dfs = []
    for block in block_metadata:
        block_df = perform_matched_filter_on_block(block, tx_hdf5, rx_hdf5, config, decimation_factor)
        block_dfs.append(block_df)

    processed_df = pd.concat(block_dfs)
    processed_df["RangeBinSize"] = range_bin_size

    if not len(processed_df):
        logging.error("!!!!! No dwells found to be processed. Exiting. !!!!!")
        return
    
    processed_df = processed_df.sort_values('Timestamp').reset_index(drop=True)
    processed_df = group_block_split_azimuths(processed_df)
    processed_df = fill_skipped_range_bins(processed_df, config)
    processed_df = processed_df.iloc[:,:(num_range_bins+4)] #easy fix to ensure convert_to_db doesn't break; may be due to extra bad data types
    processed_df = convert_to_db(processed_df)
    processed_df.to_csv(outputfile, index=False)

def perform_matched_filter_on_block(block, tx_hdf5, rx_hdf5, config, decimation_factor):
    az_groups = file_handling.get_az_groups(block[0], rx_hdf5)
    azimuths, dwell_groups = calculations.get_dwell_groups_by_azimuth(az_groups)

    azimuth_dfs = []
    for index, (azimuth, dwells) in enumerate(zip(azimuths, dwell_groups)):
        azimuth_df = process_azimuth(block, azimuth, dwells, index, tx_hdf5, rx_hdf5, config, decimation_factor)
        azimuth_dfs.append(azimuth_df)
    
    if not azimuth_dfs:
        return pd.DataFrame(columns=["Timestamp", "RangeBinSize", "Azimuth", "Dwell"])
    
    block_df = pd.concat(azimuth_dfs)

    return block_df

def process_azimuth(block, azimuth, dwells, az_index, tx_hdf5, rx_hdf5, config, decimation_factor):
    num_range_bins = config["ph2_settings"]["num_range_bins"]
    sample_freq = file_handling.get_sample_freq(tx_hdf5)
    azimuth_offset = config["ph2_settings"]["scan_azimuth_offset"]
    azimuth = (azimuth + azimuth_offset) % 360

    max_pri = rx_hdf5[block[0]].attrs["max pri(us)"] / 1e6
    dwell_length = max_pri * sample_freq

    max_pw = tx_hdf5[block[0]].attrs["max coherent pw(us)"] / 1e6
    match_length = max_pw * sample_freq

    dwell_dfs = []
    for dwell_num in dwells:
        current_dwell = f"Dwell {dwell_num}"
    
        reference_iqdf = file_handling.import_dwell(tx_hdf5, block[0], current_dwell, match_length)
        receiver_iqdf = file_handling.import_dwell(rx_hdf5, block[0], current_dwell, dwell_length*(1+match_length/dwell_length))
        starttime = datetime.datetime.now()

        matched_filter = calculations.convolve(reference_iqdf, receiver_iqdf, plot)
        df = calculations.calculate_power(matched_filter)
        powers = calculations.decimate_for_range(df, decimation_factor)
        dwell_df = calculations.rearrange_power_in_dwells(powers)

        dwell_df.insert(loc=0, column="Az Index", value=[az_index])

        dwell_dfs.append(dwell_df)
        logging.info(f"Matched filter for Dwell {dwell_num + block[1]} from group {azimuth} deg, completed in {str(datetime.datetime.now()-starttime)} with total points: {str(len(matched_filter))}") 

    azimuth_df = pd.concat(dwell_dfs)
    azimuth_df = azimuth_df.groupby(["Az Index"]).sum()

    azimuth_df.insert(loc=0, column="Dwell", value=[f"{block[0]}: Dwell {dwells[0]}"])
    azimuth_df.insert(loc=0, column="Azimuth", value=[azimuth])
    azimuth_df.insert(loc=0, column="RangeBinSize", value=[0])
    azimuth_df.insert(loc=0, column="Timestamp", value=[file_handling.get_pulse_start_time(tx_hdf5, block[0], f"Dwell {dwells[0]}")]) 

    return azimuth_df

def group_block_split_azimuths(processed_df: pd.DataFrame):
    logging.info("Fixing azimuth block breaks.")
    processed_df["keep"] = True
    for index, row in processed_df.iterrows():
        if row["Azimuth"] != processed_df["Azimuth"].iloc[index-1]:
            continue
        processed_df.iloc[index, 4:-1] = processed_df.iloc[index - 1: index+1, 4:-1].sum()
        processed_df["keep"].iloc[index - 1] = False
    processed_df = processed_df[processed_df["keep"] == True].reset_index(drop=True)
    processed_df = processed_df.drop("keep", axis=1)
    return processed_df

def fill_skipped_range_bins(processed_df: pd.DataFrame, config):
    logging.info("Filling in missing azimuths")
    az_block_size = config["ph1_settings"]["radar"]["antenna_az_block_size_deg"]
    current_azimuth = 0
    new_df_set = []
    empty_row = pd.DataFrame({"Timestamp": [0], "RangeBinSize": [processed_df["RangeBinSize"].iloc[0]], "Azimuth": [0]})
    for index, row in processed_df.iterrows():
        while (row["Azimuth"] - current_azimuth + 360) % 360 > az_block_size:
            empty_row["Azimuth"].iloc[0] = current_azimuth
            new_df_set.append(empty_row.copy())
            current_azimuth = (current_azimuth + az_block_size) % 360
        new_df_set.append(pd.DataFrame(row).T)
        current_azimuth = (current_azimuth + az_block_size) % 360
    new_df = pd.concat(new_df_set)
    
    # pd.set_option('mode.use_inf_as_na', True) #sets -inf to nan so it can be filled; may cause issues if there are other -inf values in the dataframe that should be preserved; may be better to just set -inf to floor in the loop below
    # pd.options.mode.use_inf_as_na = True
    '''
    #Use this if you want to set min values across one azimuth block dwell"
    try:
        len(processed_df.min())
        new_df = new_df.fillna(processed_df.min())
    except:
        new_df.iloc[:,4:] = new_df.fillna(1.0e-25) #fix -inf in plots showing white space; min not working when there is no data
    '''
    #Use this if you want to set homogenous floor
    new_df["Dwell"] = new_df["Dwell"].fillna("Section0: Dwell 0")
    #new_df.iloc[:,4:] = new_df.iloc[:,4:].fillna(1.0e-25) #sets both -inf and nan to floor; breaks convert_to_db if extra columns?
    for range_bin in range(0,len(processed_df.columns)-4):
        new_df[range_bin] = new_df[range_bin].fillna(1.0e-25)
        new_df[range_bin] = new_df[range_bin].replace(-np.inf, 1.0e-25)
    
    return new_df

def convert_to_db(processed_df: pd.DataFrame):
    # Convert power values to decibels safely, handling non-numeric entries
    cols = processed_df.columns[4:]
    # Ensure values are numeric (float) before applying log10
    processed_df[cols] = 10 * np.log10(processed_df[cols].astype(float))
    return processed_df
