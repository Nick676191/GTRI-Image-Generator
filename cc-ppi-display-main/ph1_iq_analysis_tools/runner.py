import logging

import argparse
from pathlib import Path
from ph1_tools import ph1_main
from ph1_tools.support_methods import import_json

logging.getLogger().setLevel(logging.DEBUG)

def setup_logger(config):
    Path(config["files"]["output_folder"] + "/" + "support").mkdir(parents=True, exist_ok=True)
    logging.getLogger().setLevel(logging.getLevelName(config["log_level"]))
    
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()

    fileHandler = logging.FileHandler("{0}/{1}.log".format(config["files"]["output_folder"], "ph1_log"))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)


def execute_ph1(file):
    config = import_json(file)
    setup_logger(config)

    logging.info(f"Phase 1 Processing file: {file}")
    logging.info("----------------------------------------")

    blocks, block_offset = ph1_main.calculate_blocks(config)
    logging.info(f"Splitting processing into {blocks} blocks.")
    for block in range(block_offset, blocks): 
        block = block + 1
        logging.info("============================================")
        logging.info(f"BEGINNING SECTION {block} of {blocks}")
        logging.info("============================================")
        radar_iq, jam_iq = ph1_main.import_iq(config, block)
        radar_iq, jam_iq = ph1_main.bpf(config, radar_iq, jam_iq)
        radar_iq_f, jam_iq_f = ph1_main.windowf(config, radar_iq, jam_iq)
        radar_iq_f, jam_iq_f = ph1_main.apply_power_calibration(config, radar_iq_f, jam_iq_f)
        ph1_main.plot_radar_iq(config, radar_iq_f, block)
        pulse_df = ph1_main.pulse_detection(config, radar_iq_f)
        radar_iq_f, jam_iq_f = ph1_main.range_effects(config, radar_iq_f, jam_iq_f)
        pulse_df = ph1_main.dwell_split_calc(config, pulse_df, radar_iq_f.samplefreq, block)
        if config["ph1_settings"]["actions"]["windowfilter"]: #undo window filter effects
            radar_iq, jam_iq = ph1_main.apply_power_calibration(config, radar_iq, jam_iq)
            radar_iq, jam_iq = ph1_main.range_effects(config, radar_iq, jam_iq)
        else: 
            radar_iq, jam_iq = radar_iq_f, jam_iq_f
        pulse_df = ph1_main.pointing_angle_calc(config, pulse_df)
        radar_iq, jam_iq = ph1_main.apply_antenna(config, pulse_df, radar_iq, jam_iq)
        return_iq = ph1_main.add_skin(config, radar_iq, jam_iq)
        ph1_main.plot_return_iq(config, return_iq, block)
        ph1_main.export_dwell_schedule(config, pulse_df, block)
        ph1_main.export_iq_dwells(config, pulse_df, return_iq, block)
        logging.info("============================================")
        logging.info(f"COMPLETED SECTION {block} of {blocks}")
        logging.info("============================================")

    ph1_main.create_reference_hdf5_files(config, blocks, block_offset)
    logging.info("Phase 1 Processing complete")

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="Define the JSON config file location.", default="preprocess_config.json"
    )
    args = parser.parse_args()

    execute_ph1(args.config)