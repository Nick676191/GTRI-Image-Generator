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
import logging
import numpy as np
import pandas as pd
from math import inf

from iqtools.datastructures.configsettings import GeneralSettings


def detect_pulse(iq_df: pd.DataFrame, dt, settings: GeneralSettings):
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
    trig = settings.trigger_level_dbm
    total_samples = len(iq_df)

    pwr_df = pd.DataFrame()

    pwr_df["pwr_lin"] = iq_df["I"].values ** 2 + iq_df["Q"].values ** 2
    pwr_df["pwr_lin"] = pwr_df["pwr_lin"].clip(1e-10)
    pwr_df["pwr_db"] = 10 * np.log10(pwr_df["pwr_lin"])

    first_low_power_index = pwr_df[pwr_df["pwr_db"] < trig].index[0]
    pwr_df = pwr_df.iloc[first_low_power_index:, :].reset_index()

    pwr_df = pwr_df[pwr_df["pwr_db"] > trig].reset_index(drop=True)

    pwr_df["is_start_sample"] = (pwr_df["index"] - pwr_df["index"].shift(1)) > 1 # compare to index one behind
    pwr_df["is_end_sample"] = (pwr_df["index"].shift(-1) - pwr_df["index"]) > 1 # compare to index one ahead
    if len(pwr_df):
        pwr_df.loc[pwr_df.index[0], "is_start_sample"] = True
        pwr_df.loc[pwr_df.index[-1], "is_end_sample"] = True
    pwr_df = pwr_df[pwr_df["is_start_sample"] != pwr_df["is_end_sample"]]

    start_sample_series = pwr_df[pwr_df["is_start_sample"]]["index"].values
    end_sample_series = pwr_df[pwr_df["is_end_sample"]]["index"].values
    pulse_width_series = (end_sample_series - start_sample_series) * dt * 1e6

    data = {
        "pulse_start_time(us)": start_sample_series * dt * 1e6,
        "pulse_end_time(us)": end_sample_series * dt * 1e6,
        "pulse_width(us)": pulse_width_series,
        "pulse_start_index": start_sample_series,
        "pulse_end_index": end_sample_series,
        # "pri(us)": pris,
        # "pri_end_index" : pri_end_indices,
    }

    df_out = pd.DataFrame(data=data)
    df_out["pri_end_index"] = df_out["pulse_start_index"].shift(-1) - 1
    df_out = df_out.fillna(total_samples - 1)
    df_out = df_out.astype({"pri_end_index": int})
    df_out["pri(us)"] = df_out["pulse_start_time(us)"].shift(-1) - df_out["pulse_start_time(us)"]
    if len(df_out):
        df_out = df_out.fillna((df_out["pri_end_index"].values[-1] - df_out["pulse_start_index"].values[-1]) * dt * 1e6)
    else:
        logging.error("No pulses detected. Check trigger level.")

    return df_out