# Compass Call Radar Processor

This tool was developed by GTRI to support Compass Call jammer testing. For more details please contact Josh Deremer (Joshua.Deremer@gtri.gatech.edu) or Rich Cohen (Rich.Cohen@gtri.gatech.edu).

## Summary

The Compass Call Radar Processor is a data processing tool capable of processing signal data produced in a test environment against a common radar processor. The tool performs environment emulation effects, radar processing, and visualization through a Plan Position Indicator (PPI) display. The PPI display visualizes signal return power as seen by the radar after performing radar processing in a top down
azimuth view.

The tool is split into three main components allowing for batching processing as desired and visualizing post-processed data without the need to reprocess. These phases are defined as follows:

- Phase 1
-- Performs environment emulation, radar schedule detection, and data manipulation to process recorded IQ signal data into a format expected by a radar receiver and signal processor. The output of this data is fed directly to phase 2.
- Phase 2
-- Performs radar processing and matched filtering of the received signal data to produce azimuth aligned range bins required for the PPI display and track detection.
- Phase 3
-- Visualizes the processed radar data on a PPI GUI that allows moving forwards or backwards in scenario time to see PPI returns as the scenario progresses.

These phases can be executed independently but are typically executed in order to process the data received from a single scenario.

## Getting Started

The tool is python based and contains a *requirements.txt* file that defines the python package dependencies that need to be installed to run the tool. If using **pip** as a package manager, the following command can be executed to install all required packages.

```
pip install -r requirements.txt
```

## Execution

The tool has a single point entry through the **run.py** file found at the base level of the repo. The file takes one positional argument that defines which phase is to be executed, chose from the following:

- ph1
- ph2
- ph3

Execution of phase 1:

```
python run.py ph1
```

Execution of phase 2:

```
python run.py ph2
```

Execution of phase 3:

```
python run.py ph3
```

A second optional positional argument can be provided to give a unique configuration file. The default configuration file is *config.json*, however, this can be overriden with the following:

```
python run.py ph1 --config myconfigfile.json
```

In this case, the selected file *myconfig.json* is used in place of the default config file *config.json*.

Each phase can be executed independently from other phases, however, phase 2 and phase 3 in order to complete execution succesfully require that previous phase(s) have been completed and the output files from the previous phase(s) are available. 

For example, Phase 1 needs to be run at least once to produce the input data required for Phase 2, however, Phase 2 can be run any number of times after this with different configuration settings using the same data output from Phase 1. The same can be said for Phase 3, which requires output data from Phase 2. However, once that data exists at least once, Phase 3 can be run fully independently.

## File Dependencies and Management

### External Data as Inputs

The tool requires input data from the test scenario run in order to begin processing. This data is the following:

- Radar IQ -- recorded IQ signal data from the threat radar stimulus that was used in the scenario. (The IQ file format must be one of the ones in the accepted IQ format list below.)
- Jammer IQ -- recorded IQ signal data from the SUT jammer response that was used in the scenario. (The IQ file format must be one of the ones in the accepted IQ format list below.)
- Antenna Pattern -- the antenna pattern for the radar being processed as a csv file in the format (azimuth, gain) for each row. Example antenna

The accepted IQ formats currently supported by the tool are:

- Signal Hound IQ
- XCOM IQ
- Midas Blue
- HDF5
- NI PXI IQ

Additional development is required to add supported IQ formats.

### User Configurable Data as Inputs

The tool requires a configuration file as an input that defines key parameters used during data processing. As mentioned in the Execution section above, the default configuration file is *config.json*, however, this can be overridden using the optional argument "--config" to define a custom configuration file path.

- config.json

The configuration file uses the common JSON format and can be edited to specify settings that affect the processing performed in all three phases of execution. Specific details about each field in the configuration file can be found below.

### Data Artifacts

The tool produces a number of artifacts during data processing that are used by subsequent phases of execution but can also be viewed and analyzed for additional scenario details or debugging purposes. These data artifacts will appear in the output folder defined by the configuration file.

The following artifacts are produced by **Phase 1** in the base output folder:

- ph1_log.log -- a log of the standard output produced during executino of Phase 1
- tx_reference.hdf5 -- a cumulation of all block processing and dwells generated during the Phase 1 processing, specifically for the detected threat radar pulse data that will be used for matched filter processing
- rx_reference.hdf5 -- a cumulation of all block processing and dwells generated during the Phase 1 processing, specifically of the return data - including both jam signals and skin returns - that will be processed by the radar processing for detections

The following artifacts are produced by **Phase 1** in the support output folder:

- dwell_schedule_X.csv -- a csv output of the calculated dwell schedules for Block X of the data processing
- transmit_iq_active_pulses_X.hdf5 -- the IQ split by dwells for Block X of the data processing, specifically for the threat radar pulse data
- received_iq_by_dwell_X.hdf5 -- the IQ split by dwells for Block X of the data processing, specifically for the return data
- Radar_X_iq_spectogram.png -- a frequency domain spectogram plot for Block X of the threat radar recorded signal
- Radar_X_iq_power.png -- a time domain power plot for Block X of the threat radar recorded signal
- Return_X_iq_spectogram.png -- a frequency domain spectogram plot for Block X of the return processed signal
- Return_X_iq_power.png -- a time domain power plot for Block X of the return processed signal

The following artifacts are produced by **Phase 2** in the base output folder:

- returns.csv -- a csv of the azimuths and range bin powers calculated during radar processing that is used by the PPI GUI display. (Note: This file's name is defined by the configuration file and so may not be named returns.csv each time.)

## Configuration File Details

The configuration file greatly determines the processing performed by the tool. The file is user editable and stored as the common JSON format, with key and value pairs for the fields defined.

The base level fields are defined as follows:

- classification -- the classification level for the data processing being performed
- scenario_name -- an identifier for the scenario that this config file supports
- log_level -- defines the level of detail recorded to the log file and printed to the screen. Acceptable values are "DEBUG", "INFO", "WARNING", and "ERROR".
- files -- a dictionary of fields to support file management and manipulation
- ph1_settings -- a dictionary of fields to support Phase 1 processing
- ph2_settings -- a dictionary of fields to support Phase 2 processing

### File Settings

The *files* section defines settings related to the input and output files to be used by the tool. They are the following:

- radar_iq -- string -- the relative or absolute path to the recorded threat radar IQ file
- jammer_iq -- string -- the relative or absolute path to the recorded jammer IQ file
- block_size_samples -- int -- the number of samples for a block size that are used when splitting the IQ file into chunks for phase 1 processing. Units are samples.
- blocks_to_read -- int -- the number of blocks to read from a file when performing phase 1 processing. Units are blocks.
- block_delay -- int -- the number of blocks to skip over before beginning to read from a file when performing phase 1 processing. Units are blocks.
- block_offset -- int -- the number of samples you'd like to skip before starting with the first block
- antenna_file -- string -- the relative or absolute path to the antenna file to be used.
- output_folder -- string -- the relative or absolute path to the output folder where artifacts will be stored.
- output_returns -- string -- the filename of the range bin returns produced by phase 2 that will be used in phase 3 visualizations.

### Phase 1 Settings

The *ph1_settings* section defines configurable settings that are used during phase 1 processing.

The *actions* group of settings allow the user to enable or disable certain processes. They are the following:

- bandpassfilter -- boolean -- determines whether bandpassfiltering is performed on the signals. Note this is performed on the radar signal as well and therefore can affect pulse detections.
- windowfilter -- boolean -- determines whether bandpass filtering is performed
- range_loss -- boolean -- determines whether propogation power loss for range is applied to the return signal
- range_delay -- boolean -- determines whether propogation time delay for range is applied to the return signal
- antenna_effects -- boolean -- determines whether antenna affects from the antenna pattern provided are applied to the return signal
- skin_return -- boolean -- determines whether a simulated skin return is added to the return signal
- signal_plotting -- boolean -- determines whether time and frequency domain plots for the radar and return signals are produced. Note this does significantly increase processing time.

The *pulse_detection* group of settings configures the pulse detection settings used when initiating dwell schedule detection. They are the following:

- trigger_level_dBm -- float -- the minimum detection level for detecting a pulse from the noise floor in dBm

The *radar* group of settings defines characteristics of the radar schedule that are used when reverse engineering the dwell schedule. They are the following:

- antenna_azimuth_calibration_offset -- float -- allows for azimuth calibration that provides a static offset for the azimuth pointing angle of the radar relative to time. Units are degrees and it must be between 0 and 360.
- antenna_az_block_size_deg -- float -- defines the step size for the azimuth pointing angle of the radar between scan blocks. The radar will step this amount of degrees for each stare. Units are degrees and must be positive.
-- Examples:
--- Mechanically Scanned: antenna_az_block_size_deg can be set to the step size based on the desired azimuth resolution for dwell grouping
--- Electronically Scanned: antenna_az_block_size_deg should be set to the actual emitter beam width used for dwell scan
- az_stare_time_us -- float -- defines the amount of time the antenna will stare at each azimuth block. This also allows multiple dwells to be grouped into the same azimuth stare grouping. Units are microseconds and must be positive.
-- Examples:
--- Mechanically Scanned: az_stare_time_us should be calcuated as (antenna_az_block_size_deg(deg) * Scan Period(s)) / 360, this will provide the total time the energy is "dwelling" at that beam width
--- Electronically Scanned: az_stare_time_us should be set based on the actual emitter's beam dwell time
- min_dwell_length_us -- float -- defines the minimum size of a radar dwell, allowing for grouping of pulses into a single CPI if the grouping is closer together than this value. Units are microseconds and must be positive and less than max_dwell_length_us.
-- This should be based on either the PRI range of the emitter or the required time to caputure pulse bursts for a CPI of multiple pulses
- max_dwell_length_us -- float -- defines the maximum size of a radar dwell, ensuring if no pulses are detected for long periods of time, dwell sizes are capped to a certain size. Units are microseconds and must be positive and greater than min_dwell_length_us
- min_pw_us -- float -- (Optional) this is an optional filter, requiring both min and max values input for pulse dwell processing.  Not accurate for modulation where coherent pw should be used.  
- max_pw_us -- float -- (Optional) this is an optional filter.  When used with min can remove pulses from the dwell schedule.
- offset_pw_us -- float -- (Optional) this is an optional filter, requiring both offset (first pulse width plus time to next pulse) and main pw values input for pulse dwell processing.  This can be used to filter out pre-pulses in a doublet.  Increasing max dwell to include doublet is not usually required.
- main_pw_us -- float -- (Optional) this is an optional filter, requiring both offset and main pw values to handle pre pulse filtering for doublets.

The *scenario* group of settings define characteristics of the test scenario that are run allowing calculation based on scenario entity locations. They are the following:

- jammer_calibration_power_offset -- float -- defines a static power offset that can be used to scale the jammer component of the return. Units are dBm.
- jammer_range -- float -- defines the slant range the jammer aircraft is from the radar system. Units are meters.
- jammer_azimuth_deg -- float -- defines the azimuth angle the jammer aircraft is relative to the entity facing direction of the radar system. Units are degrees and must be between 0 and 360.
- skin_calibration_power_offset -- float -- defines a static power offset that can be used to scale the skin component of the return. Units are dBm.
- skin_rcs -- float -- defines the range cross section size of the simulated skin return. Units are dBm.
- skin_range -- float -- defines the slant range the SUT or protected entity aircraft is from the radar system. Units are meters.
- skin_azimuth_deg -- float -- defines the azimuth angle the SUT or proteceted entity aircraft is relative to the entity facing direction of the radar system. Units are degrees and must be betweeen 0 and 360.

The *bandpassfilter* group of settings define characteristics of the bandpass filter that would be applied to the radar and jammer IQ data at the beginning of processing. They are the following:

- frequency -- float -- the absolute center frequency for the bandpass filter. Units are in hertz.
- bandwidth -- float -- the bandpass bandwidth for the bandpass filter. Units are in hertz.

The *windowfilter* group of settings define characteristics of the window filter that would be applied to the radar and jammer IQ data.

- type -- string -- default is "MovingAverage". Any other value uses the Blackman Harris filter.
- length -- int -- the sample length of the window.

The following settings are also used by phase 1 for procesing:

- radar_iq
- jammer_iq
- block_size_samples
- blocks_to_read
- block_delay
- antenna_file
- output_folder

### Phase 2 Settings

The *ph2_settings* section defines configurable settings that are used during phase 2 processing. They are the following:

- process -- string -- defines what processing algorithm is used by the radar processor. Accepted values are "MatchedFilter".
- num_range_bins -- int -- defines the number of ranged bins the radar processor will decimate to when producing the output rangebin data.
- scan_azimuth_offset -- float -- allows for offsetting the base azimuth values for the radar antenna. Units are degrees and must be between 0 and 360.

The following settings are also used by phase 2 for procesing:

- output_folder
- output_returns
- antenna_az_block_size_deg

### Phase 3 Settings

Phase 3 does not have any independent settings. However, the following configuration settings are used by phase 3 from other phases:

- antenna_az_block_size_deg
- az_stare_time_us


# Phase 1 Processing Details

TODO

# Phase 2 Processing Details

TODO

# Phase 3 User Interface

TODO
