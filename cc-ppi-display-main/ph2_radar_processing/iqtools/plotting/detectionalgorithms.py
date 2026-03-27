# -*- coding: utf-8 -*-
"""
This script houses helper functions used by PDW_Tab
to detect pulses, generate PDWs, and graph pulse information
as well as a few functions for development purposes.

This script needs matplotlib, pathlib, numpy, pandas, and math
to function properly.

Date updated: 1/28/2020

@author: Woods Burton
"""

import numpy as np
import pandas as pd
from math import inf

from iqtools.datastructures.configsettings import GeneralSettings


def detect_pulse(iq_df, dt, settings: GeneralSettings):
    """Scans through IQ data to determine pulse information.
    Compares samples to a user-specified trigger level to 
    determine if there is a pulse. Pulse information is returned
    in a pandas DataFrame. For information on hysteresis triggering
    see page 12 of the document below
    https://www.spdevices.com/documents/application-notes/73-pulse-detection-application-note/file


    :param iq_df: IQ data
    :type iq_df: pandas DataFrame
    :param dt: time per sample, 1/fs
    :type dt: float
    :param trig: trigger level in dBm
    :type trig: float
    :param dur: the duration of the pulse detection window
    :type dur: float
    :param start: start time for pulse detection window
    :type start: float
    :param hyst_bool: boolean value for hysteresis
    :type hyst_bool: bool
    :param hyst: hysteresis level in dbm
    :type hyst: float
    """
    # grab settings
    trig = settings.trigger_level_dbm
    dur = settings.analysis_dur_sec
    start = settings.analysis_del_sec

    startind = int(start / dt)
    endind = int(startind + (dur / dt))

    if startind > iq_df.index.max():
        startind = 0
        endind = iq_df.index.max()
    elif endind > iq_df.index.max():
        endind = iq_df.index.max()

    dbm_array = np.array(iq_df["I"].values ** 2 + iq_df["Q"].values ** 2)
    dbm_array[dbm_array == 0] = 1e-10 #floor of -100 dBm
    dbm_array = 10 * np.log10(dbm_array)

    #find first power outside of a pulse so we don't start in the middle of a pulse
    firstlowpower = next(x for x, val in enumerate(dbm_array)
                                  if val < trig)
    dbm_array = dbm_array[firstlowpower:] #throw away until we arent in a pulse to start

    dic = {
        "dbm": dbm_array
    }
    df = pd.DataFrame(data=dic)
    df.index.name = "sample_num"
    df.reset_index(inplace=True)

    mask = df["dbm"].values > trig
    
    # mask to get samples that are part of pulses
    df = df[mask]
    df.reset_index(inplace=True, drop=True)

    # get first pulse start and last pulse end time samples
    first_pulse_start_sample = df["sample_num"][0]

    # mask to get the samples at starts of pulses
    start_mask = df["sample_num"].diff() > 5
    start_df = df[start_mask]
    start_df.reset_index(inplace=True, drop=True)
    start_sample_numbers = np.insert(np.array(start_df["sample_num"]), 0, first_pulse_start_sample)
    pulse_start_times = start_sample_numbers * dt * 1000000

    # mask to get the samples at ends of pulses
    end_mask = start_mask.shift(-1, fill_value=True)
    end_df = df[end_mask]
    end_df.reset_index(inplace=True, drop=True)
    end_sample_numbers = np.array(end_df["sample_num"])
    pulse_end_times = end_sample_numbers * dt * 1000000
    
    # get pulse widths
    pulse_widths = pulse_end_times - pulse_start_times

    # get pris
    pris = []
    for index in range(len(pulse_start_times)):
        if index == len(pulse_start_times) - 1:
            continue
        pri = pulse_start_times[index + 1] - pulse_start_times[index]
        pris.append(pri)
    pris.append(0)

    # initialize components
    d = {
        "pulse_start_time(us)": pulse_start_times,
        "pulse_end_time(us)": pulse_end_times,
        "pulse_width(us)": pulse_widths,
        "pulse_start_sample_index": start_sample_numbers,
        "pulse_end_sample_index": end_sample_numbers,
        "pri": pris,
    }

    df_out = pd.DataFrame(data=d)

    return df_out