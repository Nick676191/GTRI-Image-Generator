import numpy as np
import pandas as pd


def get_blocks(h5data):
    """
    All blocks start with dwell 0. In order to stack them together, we will
    offset the indexing of each subsequent block's dwells by the number of 
    dwells that came before it.
    """
    dwell_offsets = []
    current_offset = 0
    for key in h5data.keys():
        dwells_in_block = len(h5data[key].keys())
        dwell_offsets.append(current_offset)
        current_offset += dwells_in_block
    return list(zip(h5data.keys(), dwell_offsets))

def get_sample_freq(h5data):
    sf = h5data[list(h5data.keys())[0]].attrs["sample_frequency(hz)"]
    return float(sf)

def get_az_groups(block, h5data):
    azimuths = []
    num_dwells = len(h5data[block].keys())
    dwell_block = h5data[block]
    for dwell in range(0, num_dwells):
        azimuths.append(float(dwell_block["Dwell "+str(dwell)].attrs["beam_azimuth(deg)"]))
    return azimuths

def import_dwell(hdf5data, block, dwell, dwell_len = None):
    noise_floor = 1.0e-25  # ~  -250 dBm
    if dwell_len != None:
        arr = np.full((int(dwell_len), ), noise_floor, dtype=np.dtype([('I', '<f8'), ('Q', '<f8')]))
        try:
            arr[:hdf5data[block][dwell].shape[0]] = np.array(hdf5data[block][dwell])
            df = pd.DataFrame(np.array(arr))
        except:
            df = pd.DataFrame(np.array(hdf5data[block][dwell]))
            print("WARNING:  IMPORT DWELL SHAPE ISSUE BYPASSED SKIPPING DATA; CHECK BLOCK SIZE")
    else:
        df = pd.DataFrame(np.array(hdf5data[block][dwell]))
    return df

def get_pulse_start_time(hdf5data, block, dwell):
    return hdf5data[block][dwell].attrs["pulse_start_time(us)"] / 10**6