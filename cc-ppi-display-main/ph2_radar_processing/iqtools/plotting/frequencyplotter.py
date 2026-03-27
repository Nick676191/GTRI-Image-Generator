import numpy as np
import pandas as pd
from .generalrunner import *

from scipy.fftpack import fft, fftfreq, fftshift

from iqtools.datastructures.configsettings import FrequencySettings, PlotCenter, FrequencyPlots

pd.options.mode.chained_assignment = None  # default='warn'

parameters = {}

class FrequencyPlotter(GeneralRunner):

    def __init__(self, params, data):
        super().__init__(params, data)
        self.iqdata = data
        self.sig_data = self.iqdata.iqdf
        self.params: FrequencySettings = params
        self.plot_df = None
        self.plot_type = None
        self.plot_center = None

    def create_plot(self):

        #choose plotter, trim IQ data, add output file name, add time index to dataframe
        self.prepare_plot_data()

        #create complex bb signal
        iq_dataFrame = self.create_complex_bb_sig(self.plot_df)

        #find fft window size
        nfft_window_size = self.find_fft_sample_window_size()

        #slice data into fft window size
        fft_slices, trigger_starts = self.slice_iq_ff_into_fft_windows(iq_dataFrame, nfft_window_size)
        
        #process the ffts
        ffts, freqs = self.process_ffts(fft_slices, nfft_window_size)

        # Default to baseband or shift freqs up to IQ center frequency
        if (self.params.plot_center == PlotCenter.DUC):
            freqs += self.params.center_freq_hz

        # make sure rwb is high enough
        samp = len(iq_dataFrame.index)
        fft_iter = int(np.floor(samp / nfft_window_size))
        fpw = nfft_window_size * (1.0 / self.iqdata.samplefreq) * 30
        numslice = int(np.floor(1.0 / fpw))

        if fft_iter > 2 and numslice > 0:

            data = self.format_data_frame_to_plot(trigger_starts,freqs,ffts)
            realTimeData = self.format_real_time_data_frame_to_plot(trigger_starts,freqs,ffts)

            for plot in self.params.plot_selection:
                if plot == FrequencyPlots.SPECTOGRAM:
                    self._spectrum_plot(data)
                elif plot == FrequencyPlots.SPECTRUM_GIF:
                    if self.params.real_time_gif:
                        self._spectrum_animation(realTimeData)
                    else:
                        self._spectrum_animation(data)
 
    def create_complex_bb_sig(self, iq_df):
        """Takes both I and Q columns in the imported DataFrame
        and return a DataFrame that contains a new column that is the
        rectangular complex representation of both columns.

        :param iq_df: Data structure that holds the imported IQ data
        :type iq_df: pandas DataFrame
        """

        # Create the complex baseband signal from I and Q paths
        iq_df.loc[:, "complex_bb"] = iq_df.loc[:, "I"].values + (
            1j * iq_df.loc[:, "Q"].values
        )

        return iq_df

    def find_fft_sample_window_size(self):
        """Finds how many samples are needed at a specific sampling
        frequency to obtain a specific resolution bandwidth.

        :param f_s_hz: Sampling frequency in Hz
        :type f_s_hz: float
        :param rbw_hz: Resolution Bandwidth in Hz
        :type rbw_hz: float
        """

        # Finding minimum number of samples required for FFT
        # window needed to reach the required RBW
        nfft_wind = np.ceil(np.divide(self.iqdata.samplefreq, self.params.rbw_hz))

        # Catch the edge case where total analysis duration
        # may be less than the nfft_wind
        analysis_duration_secamples = self.params.analysis_dur_sec / self.iqdata.deltatime

        if nfft_wind > analysis_duration_secamples:
            nfft_wind = analysis_duration_secamples

        return int(nfft_wind)

    def slice_iq_ff_into_fft_windows(self, iq_df, nfft_wind):

        # Find number of samples and number of splits to perform
        n_samples = len(iq_df.index)
        num_fft_iters = int(np.floor(n_samples / nfft_wind))

        # Store the FFT values in a list
        fft_slices = []
        t_starts = []

        # Get the column number of the complex_BB signal
        complex_bb_col_ind = iq_df.columns.get_loc("complex_bb")

        # Loop through to split sample into fft windows
        for i in range(0, num_fft_iters - 1):

            # Grab the batch
            batch_start = int(i * nfft_wind)
            batch_end = int((i + 1) * nfft_wind)
            complex_bb_batch = iq_df.iloc[batch_start:batch_end, complex_bb_col_ind].values

            # Scale the input such that the output of the FFT is not warped
            complex_bb_batch = complex_bb_batch / nfft_wind

            fft_slices.append(complex_bb_batch)
            t_starts.append(self.params.analysis_del_sec + batch_start * self.iqdata.deltatime)

        return fft_slices, t_starts

    def process_ffts(self, fft_slices, nfft_wind):

        ffts = []

        # Loop through to make FFTs for BB signal
        for batch in fft_slices:
            # Compute the FFT
            temp_fft = fft(batch)
            temp_fft = fftshift(temp_fft)
            # Convert the ouput of the FFT to dBm
            temp_fft = np.abs(temp_fft)
            temp_fft = 10 * np.log10((temp_fft ** 2 / 100) * 1000)
            ffts.append(temp_fft)

        # Grab the frequencies given the batch size
        freqs = fftfreq(nfft_wind, self.iqdata.deltatime)
        freqs = fftshift(freqs)

        freq_low = self.params.center_freq_hz - (self.params.span_hz/2)
        freq_high = self.params.center_freq_hz + (self.params.span_hz/2)
        freq_ind = [ ((freqs > freq_low) & (freqs < freq_high)) ]

        np_ffts = np.array(ffts)
        trunc_ffts = []
        for rows in range(np_ffts.shape[0]):
            trunc_ffts.append(np_ffts[rows][tuple(freq_ind)])

        # Return the FFT and the associated frequencies
        return trunc_ffts, freq_ind[0]

    def format_data_frame_to_plot(self,t_starts,freqs,ffts):

        freq_low = self.params.center_freq_hz - (self.params.span_hz/2)
        freq_high = self.params.center_freq_hz + (self.params.span_hz/2)
        freqs = np.linspace(freq_low,freq_high,len(ffts[0]))

        data = pd.DataFrame(ffts).transpose()
        data.columns = t_starts

        data = data.assign(frequencies = freqs)
        data = data.set_index('frequencies')

        return data

    def format_real_time_data_frame_to_plot(self,t_starts,freqs,ffts):
        fps = 30.0
        frameLength = 1.0/fps
        frameStartTime = frameLength
        i = 1
        while i < (len(ffts)-1):
            if t_starts[i+1] > frameStartTime:
                i+=1
                frameStartTime += frameLength
            else: 
                ffts.pop(i)
                t_starts.pop(i)
        data = self.format_data_frame_to_plot(t_starts,freqs,ffts)
        return data

    def _spectrum_animation(self,data):

        file = f"{self.params.output_file}_iq_spectrum"
        title = self.params.input_file
        x_axis = "Frequency"
        y_axis = "Amplitude"
        pow_min = self.params.pwr_min_dbm
        pow_max = self.params.pwr_max_dbm

        self.plotter.animation(title, data, x_axis, y_axis, file, pow_min, pow_max)

    def _spectrum_plot(self,data):
        
        file = f"{self.params.output_file}_iq_spectogram"
        title = self.params.input_file
        x_axis = "Frequency"
        y_axis = "Time"
        z_axis = "Amplitude"
        pow_min = self.params.pwr_min_dbm
        pow_max = self.params.pwr_max_dbm
        
        self.plotter.intensity_plot(title, data, x_axis, y_axis, z_axis, file, pow_min, pow_max)
