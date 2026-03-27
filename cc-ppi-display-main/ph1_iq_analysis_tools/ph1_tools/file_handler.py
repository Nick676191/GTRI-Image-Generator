import logging
from pathlib import Path
import h5py
import pandas as pd

from iqtools.datastructures.iqdata import IQData


def produce_transmit_pulse_hdf5(config, pulse_df, block: int = 0):
    files = config["files"]
    output_hdf5 = Path(files["output_folder"] + "/" + f"support/transmit_iq_active_pulses_{block}.hdf5")
    logging.info("Extracting active pulse I/Q to output file: {}".format(output_hdf5))

    samples_to_read = files["block_size_samples"]
    sample_offset = (block - 1) * samples_to_read
    try: block_offset = files["block_offset"]
    except: block_offset=0
    sample_offset = sample_offset + block_offset

    radar_iq = IQData()
    radar_iq.set_importer(Path(files["radar_iq"]).suffix)
    radar_iq.set_importer_settings(samples_to_read, sample_offset)
    radar_iq.importer.inputfile = files["radar_iq"]
    radar_iq.import_iq()

    output = h5py.File(output_hdf5, "w")
    for index, row in pulse_df.iterrows():
        if index == len(pulse_df)-1:
            continue
        start_sample = int(row["pulse_start_index"])
        end_sample = int(row["pulse_end_index"])
        active_pulse = radar_iq.iqdf.iloc[start_sample:end_sample, :]
        output.attrs["classification"] = config["classification"]
        output.attrs["center_freq(hz)"] = float(radar_iq.centerghz*1e9)
        output.attrs["sample_frequency(hz)"] = float(radar_iq.samplefreq)
        output.attrs["max coherent pw(us)"] = float(max(pulse_df["coherent pulse width(us)"])) 

        output['Dwell '+str(index)] = active_pulse.to_records(index=False)  
        output['Dwell '+str(index)].attrs["description"] = str("Each dataset in this file corresponds to a single radar TX pulse.  " +
                                                            "The dataset contains only active pulse I/Q to be used later as a " +
                                                            "reference for the receiver's matched filter.")
        output['Dwell '+str(index)].attrs["center_freq(hz)"] = float(radar_iq.centerghz*1e9)
        output['Dwell '+str(index)].attrs["sample_frequency(hz)"] = float(radar_iq.samplefreq) 
        output['Dwell '+str(index)].attrs["pulse_number"] = int(index)
        output['Dwell '+str(index)].attrs["pulse_width(us)"] = float(row["pulse_width(us)"])
        output['Dwell '+str(index)].attrs["pulse_start_time(us)"] = float(row["pulse_start_time(us)"]) 

    output.close()
    logging.info(f"File \'{output_hdf5}\' created!")


def produce_receive_pulse_hdf5(config: dict, pulse_df: pd.DataFrame, return_iq: IQData, block: int = 0):
    files = config["files"]
    output_hdf5 = Path(files["output_folder"] + "/" + f"support/received_iq_by_dwell_{block}.hdf5")
    logging.info("Splitting dwells by PRI and storing to output file: {}".format(output_hdf5))

    output = h5py.File(output_hdf5, "w")
    for index, row in pulse_df.iterrows():
        if index == len(pulse_df)-1:
            continue
        start_sample = int(row["pulse_start_index"])
        end_sample = start_sample + int(return_iq.samplefreq * row["pri(us)"] / 1e6)
        active_pulse = return_iq.iqdf.iloc[start_sample:end_sample, :]
        output.attrs["classification"] = config["classification"]
        output.attrs["center_freq(hz)"] = float(return_iq.centerghz * 1e9)
        output.attrs["sample_frequency(hz)"] = float(return_iq.samplefreq)
        output.attrs["max pri(us)"] = float(max(pulse_df["pri(us)"]))

        output['Dwell ' + str(index)] = active_pulse.to_records(index=False)  
        output['Dwell ' + str(index)].attrs["classification"] = config["classification"]
        output['Dwell ' + str(index)].attrs["description"] = str("Each dataset in this file corresponds to a single radar PRI's worth of return information, "+
                                                            "grouped by dwell ID.  For each radar dwell, the dataset contains a PRI's worth of "+
                                                            "RCS + Jammer return data (including path effects).")
        output['Dwell ' + str(index)].attrs["pulse_number"] = int(index)
        output['Dwell ' + str(index)].attrs["pri(us)"] = float(row["pri(us)"])
        output['Dwell ' + str(index)].attrs["pulse_start_time(us)"] = float(row["pulse_start_time(us)"]) 
        output['Dwell ' + str(index)].attrs["beam_azimuth(deg)"] = float(row["beam_azimuth"]) 
    
    output.close()
    logging.info(f"File \'{output_hdf5}\' created!")

def create_reference_hdf5(config: dict, blocks: int, block_offset: int):
    files = config["files"]
    tx_ref_file = Path(files["output_folder"] + "/" + f"tx_reference.hdf5")
    rx_ref_file = Path(files["output_folder"] + "/" + f"rx_reference.hdf5")
    tx_ref = h5py.File(tx_ref_file,'w')
    rx_ref = h5py.File(rx_ref_file,'w')

    for block in range(block_offset, blocks):
        block = block + 1

        temp_tx_ref_file = f"support/transmit_iq_active_pulses_{block}.hdf5"
        tx_ref[f'Section{block}'] = h5py.ExternalLink(temp_tx_ref_file, "/")

        temp_rx_ref_file = f"support/received_iq_by_dwell_{block}.hdf5"
        rx_ref[f'Section{block}'] = h5py.ExternalLink(temp_rx_ref_file, "/")


def export_dwell_schedule(config: dict, pulse_df: pd.DataFrame, block: int = 0):
    files = config["files"]
    output_csv = Path(files["output_folder"] + "/" + f"support/dwell_schedule_{block}.csv")
    logging.info("Exporting dwell schedule to output file: {}".format(output_csv))

    pulse_df.to_csv(output_csv)
    logging.info(f"File \'{output_csv}\' created!")