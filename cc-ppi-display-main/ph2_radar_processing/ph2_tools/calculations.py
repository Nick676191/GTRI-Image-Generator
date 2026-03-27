import numpy as np
import pandas as pd
from scipy import constants, signal

import pyqtgraph as pg


def get_dwell_groups_by_azimuth(az_list):
    previous_az = -1
    stare_groups = [[]]
    azimuths = []
    current_stare = 0
    for index, azimuth in enumerate(az_list):
        if azimuth == previous_az:
            stare_groups[current_stare].append(index)
        else:
            stare_groups.append([index])
            azimuths.append(azimuth)
            previous_az = azimuth
            current_stare += 1
    del stare_groups[0]
    return azimuths, stare_groups


def convolve(filter, input_signal, plot): 
    matched_filter = filter.I + 1j*filter.Q
    complex_input = input_signal.I + 1j*input_signal.Q 
    # matched_filter=np.conjugate(complex_filter)
    result = signal.correlate(complex_input, matched_filter, mode="valid")

    if plot:
        plot_matched_filter_response(filter, input_signal, matched_filter, result)
    
    mf_df = pd.DataFrame({'I': np.real(result), 'Q': np.imag(result)})
    
    return mf_df

def plot_matched_filter_response(filter, input_signal, matched_filter, result):
        pg_layout = pg.GraphicsLayoutWidget()

        # Add subplots
        pg_layout.addPlot(x = np.arange(len(filter.I)), y=filter.I, row=0, col=0, title = "REM I")
        pg_layout.addPlot(x = np.arange(len(filter.Q)), y=filter.Q, row=0, col=1, title = "REM Q")
        pg_layout.addPlot(x = np.arange(len(input_signal.I)), y=input_signal.I, row=1, col=0, title = "Received I")
        pg_layout.addPlot(x = np.arange(len(input_signal.Q)), y=input_signal.Q, row=1, col=1, title = "Received Q")
        pg_layout.addPlot(x = np.arange(len(matched_filter)), y=np.real(matched_filter), row=2, col=0, title = "Received I")
        pg_layout.addPlot(x = np.arange(len(matched_filter)), y=np.real(matched_filter), row=2, col=1, title = "Received Q")

        mf_power = 20*np.log10( np.sqrt(np.real(result)**2 +  np.imag(result)**2) )  
        pg_layout.addPlot(x = np.arange(len(mf_power)), y=mf_power, row=3, col=0, title="Matched Filter")

        # Show our layout holding multiple subplots
        pg_layout.show()
        input("Press Enter to continue...")

def calculate_decimation_factor(max_pri, sample_rate, num_range_bins):
    new_sample_rate = num_range_bins/max_pri
    decimation_factor = int(sample_rate/new_sample_rate)
    if decimation_factor == 0:
        decimation_factor = 1
    range_bin_size = constants.c / new_sample_rate / 2.0
    return decimation_factor, range_bin_size

def decimate_for_range(df, decimation_factor):
    powers = df["power"].values
    powers_trimmed = powers[:int(len(powers)/decimation_factor)*decimation_factor]
    decimated_powers = powers_trimmed.reshape(-1, decimation_factor).sum(1)
    return decimated_powers

def calculate_power(df):
    df["power"] = df["I"]**2 + df["Q"]**2  
    return df

def rearrange_power_in_dwells(power):
    return pd.DataFrame(power).T