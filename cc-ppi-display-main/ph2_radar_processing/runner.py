import logging
import argparse
import datetime

from ph2_tools.complex_radar_MF import perform_matched_filter_radar_processing
from ph2_tools.support_methods import import_json


logging.getLogger().setLevel(logging.DEBUG)

def setup_logger(config):
    logging.getLogger().setLevel(logging.getLevelName(config["log_level"]))
    
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()

    fileHandler = logging.FileHandler("{0}/{1}.log".format(config["files"]["output_folder"], "ph2_log"))
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

def execute_ph2(file):
    config = import_json(file)
    setup_logger(config)

    logging.info("Phase 2 Processing file: {}".format(file))
    logging.info("----------------------------------------")
    
    ph2_settings = config["ph2_settings"]

    if ph2_settings["process"] == "MatchedFilter":
        logging.info("Matched Filter Radar Processing Start: {}".format(datetime.datetime.now()))
        perform_matched_filter_radar_processing(config)
        logging.info("Matched Filter Radar Processing End: {}".format(datetime.datetime.now()))
        logging.info("----------------------------------------")

    logging.info("Phase 2 Processing complete")


if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="Define the JSON config file location.", default="config.json"
    )
    args = parser.parse_args()

    execute_ph2(args.config)