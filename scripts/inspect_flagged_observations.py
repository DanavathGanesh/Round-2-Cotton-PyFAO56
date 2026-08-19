import pandas as pd
from pathlib import Path
# Project directories
PROJECT_ROOT = Path("/content/Round-2-Cotton-PyFAO56")

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
# Mesonet input files
HINT_FILE = RAW_DIR / "Field_A_HINT_mesonet_data.csv"
FTCB_FILE = RAW_DIR / "Field_B_FTCB_mesonet_data.csv"
