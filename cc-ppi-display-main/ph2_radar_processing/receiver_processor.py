import os
import sys
import pandas as pd
import numpy as np

from pdw_to_iq_importer import PdwToIq

import pyqtgraph as pg
import matplotlib.pyplot as plt
import scipy
import math
import time


settings = {
    "pdw_file": "test-data\\test_pdws.csv",
    "ch1_xcom_file": "example-data\\s1_pulsed_with_fm.xdat",
    "ch2_xcom_file": "example-data\\s1_pulsed_with_fm.xdat",
}

radar_settings = {
    "angular_rate_rpm" : 10.0,
    "range_m" : 100000.0
}


SPEED_OF_LIGHT = 299792458.0

class PulseProcessor(object):
    def __init__(self, settings):
        
        self.REMChannel = PdwToIq(settings["ch1_xcom_file"], data=None)
        self.ECMChannel = PdwToIq(settings["ch2_xcom_file"], data=None)

        self.radar_angular_rate_hz = (1.0 / (float(radar_settings["angular_rate_rpm"])*60.0))
        
        self.sample_rate_hz = 0.0
        self.pulse_width_sec = 0.0

    def set_sample_rate(self, rate):
        self.sample_rate_hz = rate

    def set_pulse_width(self, width):
        self.pulse_width_sec = width

    def get_sample_rate(self):
        return self.REMChannel.iq_sample_rate_hz
        
    def sample_idx_to_range(self, index):
        return index * 1/self.sample_rate_hz * SPEED_OF_LIGHT/2

    def GetIqREM(self, start, end):
        return self.REMChannel.get_pulse_iq(start, end)
    
    def GetIqECM(self, start, end):
        return self.ECMChannel.get_pulse_iq(start, end) 
        
    def convolve(self, filter, input_signal):
        #pulse_len = self.pulse_width_sec * self.sample_rate_hz
        pulse_len = filter.shape[0]
        pulse_t = np.arange(pulse_len)/self.REMChannel.iq_sample_rate_hz

        '''
        print("pulse length", pulse_len)
        print("pulse time", pulse_len/self.REMChannel.iq_sample_rate_hz)
        print("sample rate", self.REMChannel.iq_sample_rate_hz)
        '''

        complex_filter = filter.I + 1j*filter.Q
        complex_input = input_signal.I + 1j*input_signal.Q
        
        # TO DO: matched filter input needs to come from args 
        '''
        complex_input = scipy.signal.chirp(pulse_t, 0, pulse_len/self.REMChannel.iq_sample_rate_hz, 1e6, 'linear') + \
            1j*scipy.signal.chirp(pulse_t, 0, pulse_len/self.REMChannel.iq_sample_rate_hz, 1e6, 'linear', 90)
        #pg.plot(abs(complex_input), title = "test")
        complex_filter = scipy.signal.chirp(pulse_t, 0, pulse_len/self.REMChannel.iq_sample_rate_hz, 1e6, 'linear') + \
            1j*scipy.signal.chirp(pulse_t, 0, pulse_len/self.REMChannel.iq_sample_rate_hz, 1e6, 'linear', 90)
        '''
        
        
        matched_filter = np.flip(complex_filter) *  1/len(complex_filter) 

        #avalable modes are full or valid.  Valid only gives you the matched cells, full gives everything
        result = np.convolve(complex_input, matched_filter, mode="full")
        
        return result
    
    def fft(self, input_signal):
            
            iq =  input_signal.I+1j*input_signal.Q
            iq = input_signal.I
            totalSampleCount = len(input_signal)

            Ts = self.get_sample_rate()
            
            Fs = 1/Ts # sampling rate
            
            timeaxis = np.linspace(0,totalSampleCount*Ts,totalSampleCount) # time vector
            
            k = np.arange(totalSampleCount)
            
            T = (totalSampleCount/Fs)
                  
            #frq = k/(T) # two sides frequency range
            #frq = frq[range(totalSampleCount//2)] # one side frequency range 
            self.frqCPU = np.fft.fftfreq(totalSampleCount // 2, Ts)
            self.frqCPU = np.fft.fftshift(self.frqCPU) 

            #Y = np.fft.fft(self.rawBuffer[:totalSampleCount // 2])/(totalSampleCount // 2) # fft computing and normalization
            Y = np.fft.fft(iq)/(totalSampleCount // 2) # fft computing and normalization
            return np.fft.fftshift(Y)




class PDWParser(object):
    def __init__(self, settings):

        self.pdws = pd.read_csv (settings["pdw_file"])
        self.numPdws = self.pdws.shape[0]
        self.currentIndex = 0 
        self.currentPDW = None
    
    def get_next_pdw(self):
        if self.currentIndex < self.numPdws:
            self.currentPDW  = self.pdws.loc[self.currentIndex]
            self.currentIndex += 1
            return self.currentPDW
        
        
if __name__ == '__main__':
    args = sys.argv[1:]

    if not args:
        
        PDWs = PDWParser(settings)
        Processor = PulseProcessor(settings)

        for pdw in range(0, 1):
            PDW = (PDWs.get_next_pdw())
            iq_rem = Processor.GetIqREM(PDW['pulse_start_index'], PDW['pulse_end_sample_index'])
            iq_ecm = Processor.GetIqECM(PDW['pulse_start_index'], PDW['pulse_end_sample_index'])

            matched_filter = Processor.convolve(iq_rem, iq_ecm) 

        #iq_t = np.arange(len(iq_rem.I))/iq_rem.get_sample_rate()
        pg.plot(iq_rem.I, title = "REM I")
        pg.plot(iq_rem.Q, title = "REM Q")
        pg.plot(iq_ecm.I, title = "ECM I")
        pg.plot(iq_ecm.Q, title = "ECM Q")

        iq = iq_rem.I+1j*iq_rem.Q
        iq_power = 20*np.log10( np.sqrt(iq_rem.I**2 +  iq_rem.Q**2) ) 
        pg.plot(abs(Processor.fft(iq_rem)), title = "FFT")
        
        pg.plot(abs(iq), title = "REM I/Q voltage")
        pg.plot((iq_power), title = "REM I/Q power")
        
        iq = iq_ecm.I+1j*iq_ecm.Q
        iq_power = 20*np.log10( np.sqrt(iq_ecm.I**2 +  iq_ecm.Q**2) ) 
        pg.plot(abs(iq), title = "ECM I/Q voltage")
        pg.plot((iq_power), title = "ECM I/Q power")
        
        

        pg.plot((20*np.log10(np.abs(matched_filter))), title = "matched filter")  ## setting pen=None disables line drawing
        input("Press Enter to continue...")
        #print(PDW['pulse_start_sample_index'])
        

    else:
        input_file = args[0]
        PdwToIq(input_file, data=None)