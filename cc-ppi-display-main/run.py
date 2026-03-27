"""
PPI Tool Run Support

This module is the entry point for running each of the tasks in the PPI Tool
"""

import argparse
import sys, os
from pathlib import Path
import PyQt5
import pyqtgraph
import h5py
import matplotlib

sys.path.append(str(Path.joinpath(Path(os.getcwd()), Path("ph0_tools"))))
sys.path.append(str(Path.joinpath(Path(os.getcwd()), Path("ph1_iq_analysis_tools"))))
sys.path.append(str(Path.joinpath(Path(os.getcwd()), Path("ph2_radar_processing"))))
sys.path.append(str(Path.joinpath(Path(os.getcwd()), Path("ph3_ppi_display"))))

from ph0_tools.runner import execute_ph0
from ph1_iq_analysis_tools.runner import execute_ph1
from ph2_radar_processing.runner import execute_ph2
from ph3_ppi_display.runner import execute_ph3

# ============================
# STATIC VARIABLES
# ============================


SUPPORTED_TOOLS = {
    "ph0": execute_ph0,
    "ph1": execute_ph1,
    "ph2": execute_ph2,
    "ph3": execute_ph3,
}

parser = argparse.ArgumentParser()
parser.add_argument("tool", help="Request the tool to run.", choices=SUPPORTED_TOOLS.keys())
parser.add_argument(
    "--config", help="Define the JSON config file location.", default="config.json"
)
args = parser.parse_args()

SUPPORTED_TOOLS[args.tool](args.config)
