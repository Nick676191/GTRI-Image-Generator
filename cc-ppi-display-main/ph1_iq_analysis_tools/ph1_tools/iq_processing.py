import logging
import numpy as np
import pandas as pd
from scipy import signal

from iqtools.datastructures.iqdata import IQData
from ph1_tools import support_methods

from iqtools.frequencymanager import FrequencyManager
from iqtools.timemanager import TimeManager
from iqtools.datastructures.configsettings import FrequencyPlots, TimePlots


def bandpass(iqdata: IQData, config):
    intermediate_freq = config["frequency"]
    bandwidth = config["bandwidth"]
    freq_shift = intermediate_freq - iqdata.centerghz*1e9
    iqdf = iqdata.iqdf

    filter_order = 9
    lowcut = freq_shift - bandwidth/2
    highcut = freq_shift + bandwidth/2
    bpf_b, bpf_a = signal.butter(filter_order, [lowcut, highcut], fs=iqdata.samplefreq, btype="band")
    
    iqdf["I"] = signal.lfilter(bpf_b, bpf_a, iqdf["I"])
    iqdf["Q"] = signal.lfilter(bpf_b, bpf_a, iqdf["Q"])

    iqdata.iqdf = iqdf

    return iqdata

def bandpassSOS(iqdata: IQData, config):
    intermediate_freq = config["frequency"]
    bandwidth = config["bandwidth"]
    freq_shift = abs(intermediate_freq - iqdata.centerghz*1e9) #assumes bpf generates pos and neg coef's
    iqdf = iqdata.iqdf

    filter_order = 9
    for i in range(1,2): #default to one filter; sometimes adding additional harmonics filters improve result
        lowcut = freq_shift - bandwidth/2
        highcut = freq_shift + bandwidth/2
        if (lowcut < 0): #use lowpass instead
            sos = signal.butter(filter_order, [highcut], fs=iqdata.samplefreq, analog = False, btype="lowpass", output = "sos")
        else: # continue with bandpass
            sos = signal.butter(filter_order, [lowcut, highcut], fs=iqdata.samplefreq, analog = False, btype="bandpass", output = "sos")
        
        iqdf["I"] = signal.sosfiltfilt(sos, iqdf["I"])
        iqdf["Q"] = signal.sosfiltfilt(sos, iqdf["Q"])

    iqdata.iqdf = iqdf

    return iqdata
    
def windowFilter(iqdata: IQData, config):
    filter_type = config["type"] #MovingAverage or BlackmanHarris
    window_length = config["length"]
    iqdf = iqdata.iqdf

    try: 
        iqdf_length = len(iqdf)

        if filter_type == "MovingAverage":
            window = np.ones(window_length)
            window_sum = window_length
        else: #BlackmanHarris
            window = signal.windows.blackmanharris(window_length, sym=True)
            window_sum = sum(window)
        front_loc = int(np.floor((window_length-1)/2))
        '''
        THIS ASSUMES EACH BLOCK HAS DIFFERENT DATA FRAME w/ INDEX STARTING AT ZERO
        '''
        iqdf["I"][front_loc:iqdf_length-front_loc-1] = signal.convolve(iqdf["I"], window, 'valid')/window_sum
        iqdf["Q"][front_loc:iqdf_length-front_loc-1] = signal.convolve(iqdf["Q"], window, 'valid')/window_sum

        iqdata.iqdf = iqdf
    except: 
        iqdata.iqdf = iqdf

    return iqdata

def downconvert(iqdata: IQData, config):
    intermediate_freq = config["frequency"]
    bandwidth = config["bandwidth"]
    freq_shift = intermediate_freq - iqdata.centerghz*1e9
    iqdf = iqdata.iqdf

    logging.info("Shifting by: {}".format(freq_shift))

    iqdf["I"] = iqdf["I"] * np.cos(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift)
    iqdf["Q"] = iqdf["Q"] * (-np.sin(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift))

    lowpass_order = 51
    cutoff_3db = bandwidth
    lowpass = signal.firwin(lowpass_order, cutoff_3db/(iqdata.samplefreq/2))

    iqdf["I"] = signal.lfilter(lowpass, 1, iqdf["I"])
    iqdf["Q"] = signal.lfilter(lowpass, 1, iqdf["Q"])

    iqdata.iqdf = iqdf

    return iqdata

def upconvert(iqdata: IQData, config: dict):
    intermediate_freq = config["frequency"]
    freq_shift = intermediate_freq - iqdata.centerghz*1e9
    iqdf = iqdata.iqdf

    logging.info("Shifting by: {}".format(freq_shift))

    iqdf["I"] = iqdf["I"] * np.cos(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift)
    iqdf["Q"] = iqdf["Q"] * (-np.sin(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift))

    iqdata.iqdf = iqdf

    return iqdata

def downconvertSOS(iqdata: IQData, config):
    intermediate_freq = config["frequency"]
    bandwidth = config["bandwidth"]
    freq_shift = intermediate_freq - iqdata.centerghz*1e9
    iqdf = iqdata.iqdf

    logging.info("Shifting by: {}".format(freq_shift))

    iqdf["I"] = iqdf["I"] * np.cos(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift)
    iqdf["Q"] = iqdf["Q"] * (-np.sin(2*np.pi*(iqdf.index.values/iqdata.samplefreq)*freq_shift))

    lowpass_order = 51
    cutoff_3db = bandwidth
    #lowpass = signal.firwin(lowpass_order, cutoff_3db/(iqdata.samplefreq/2))
    lowpass = signal.butter(lowpass_order, cutoff_3db/(iqdata.samplefreq/2), analog = False, btype = "lowpass", output="sos")
    
    iqdf["I"] = signal.sosfiltfilt(lowpass, iqdf["I"])
    iqdf["Q"] = signal.sosfiltfilt(lowpass, iqdf["Q"])

    iqdata.iqdf = iqdf

    return iqdata

def apply_power_calibration(config: dict, radar_iq: IQData, jam_iq: IQData):
    jam_cal_db = config["jammer_calibration_power_offset"]
    skin_cal_db = config["skin_calibration_power_offset"]
    jam_cal_linear = support_methods.get_power_from_db(jam_cal_db)
    skin_cal_linear = support_methods.get_power_from_db(skin_cal_db)

    jam_iq.iqdf = support_methods.apply_power_offset(jam_iq.iqdf, jam_cal_linear)
    radar_iq.iqdf = support_methods.apply_power_offset(radar_iq.iqdf, skin_cal_linear)

    return radar_iq, jam_iq

def apply_range_loss_effects(config: dict, radar_iq: IQData, jam_iq: IQData):
    range_loss = support_methods.get_range_loss(config["jammer_range"])
    logging.info("Range loss for jammer: {}".format(10*np.log10(range_loss)))
    jam_iq.iqdf = support_methods.apply_power_offset(jam_iq.iqdf, range_loss)
    range_loss = support_methods.get_range_loss(config["skin_range"])
    logging.info("Range loss for skin: {}".format(10*np.log10(range_loss)))
    radar_iq.iqdf = support_methods.apply_power_offset(radar_iq.iqdf, range_loss)
    return radar_iq, jam_iq

def apply_range_delay_effects(config: dict, radar_iq: IQData, jam_iq: IQData):
    sample_rate = jam_iq.samplefreq
    range_delay_samples = support_methods.calculate_sample_delay(sample_rate, config["jammer_range"])
    logging.info("Range delay in samples for jammer: {}".format(range_delay_samples))
    jam_iq.iqdf = support_methods.front_fill_samples(jam_iq.iqdf, range_delay_samples)
    range_delay_samples = support_methods.calculate_sample_delay(sample_rate, config["skin_range"])
    logging.info("Range delay in samples for skin: {}".format(range_delay_samples))
    radar_iq.iqdf = support_methods.front_fill_samples(radar_iq.iqdf, range_delay_samples)
    return radar_iq, jam_iq

def apply_antenna(config: dict, pulse_df: pd.DataFrame, radar_iq: IQData, jam_iq:IQData):
    antenna_file = config["files"]["antenna_file"]
    antenna_pattern = import_antenna_file(antenna_file) 

    for index, row in pulse_df.iterrows():
        radar_az = float(row["skin_az"])
        radar_closest_pattern_gain_dBm = antenna_pattern.iloc[(antenna_pattern['angle']-radar_az).abs().argsort()[:1]]["dB"].values[0]
        radar_closest_pattern_gain_linear = 10**(radar_closest_pattern_gain_dBm/10)

        jammer_az = float(row["jam_az"])
        jammer_closest_pattern_gain_dBm = antenna_pattern.iloc[(antenna_pattern['angle']-jammer_az).abs().argsort()[:1]]["dB"].values[0]
        jammer_closest_pattern_gain_linear = 10**(jammer_closest_pattern_gain_dBm/10)
        
        start_sample = int(row["pulse_start_index"])
        end_sample = int(radar_iq.samplefreq * row["pri(us)"] / 1e6) +start_sample
        radar_iq.iqdf.iloc[start_sample:end_sample] = support_methods.apply_power_offset(radar_iq.iqdf.iloc[start_sample:end_sample], radar_closest_pattern_gain_linear)
        jam_iq.iqdf.iloc[start_sample:end_sample] = support_methods.apply_power_offset(jam_iq.iqdf.iloc[start_sample:end_sample], jammer_closest_pattern_gain_linear)


    return radar_iq, jam_iq

def import_antenna_file(file):
    ant_df = pd.read_csv(file, names=["angle", "dB"]) 
    return ant_df


def add_skin_return(config: dict, radar_iq: IQData, jam_iq: IQData):
    rcs = config["skin_rcs"]
    rcs_linear = 10**(rcs/10)
    radar_iq.iqdf = support_methods.apply_power_offset(radar_iq.iqdf, rcs_linear)

    return_iq = radar_iq
    return_iq.iqdf = support_methods.add_iq_df(radar_iq.iqdf, jam_iq.iqdf)

    return return_iq

def generate_input_plots(config):
    radar_file = config["files"]["radar_iq"]
    jam_file = config["files"]["jammer_iq"]
    output_folder = config["files"]["output_folder"] + "/support"

    plot_file(radar_file, output_folder, "radar")
    plot_file(jam_file, output_folder, "jam")


def generate_output_plots(config, return_iq, name):
    output_folder = config["files"]["output_folder"] + "/support"
    settings = {
        "filename": name,
        "output_dir": output_folder
    }

    logging.info("Generating spectogram for: {}".format("Receiver IQ"))
    manager = FrequencyManager()
    manager.update_settings(settings)
    manager.data = return_iq
    manager.execute(FrequencyPlots.SPECTOGRAM)

    logging.info("Generating IQ power plot for: {}".format("Receiver IQ"))
    manager = TimeManager()
    manager.update_settings(settings)
    manager.data = return_iq
    manager.execute(TimePlots.IQPOWER)


def plot_file(file, output_folder, name):
    settings = {
        "input_file": file, 
        "filename": name,
        "output_dir": output_folder
    }

    logging.info("Generating spectogram for: {}".format(file))
    manager = FrequencyManager()
    manager.update_settings(settings)
    manager.execute(FrequencyPlots.SPECTOGRAM)

    logging.info("Generating IQ power plot for: {}".format(file))
    manager = TimeManager()
    manager.update_settings(settings)
    manager.execute(TimePlots.IQPOWER)