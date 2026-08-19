import pandas as pd
from pathlib import Path
# Project directories
PROJECT_ROOT = Path("/content/Round-2-Cotton-PyFAO56")

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
# Mesonet input files
HINT_FILE = RAW_DIR / "Field_A_HINT_mesonet_data.csv"
FTCB_FILE = RAW_DIR / "Field_B_FTCB_mesonet_data.csv"
# Load Field A (HINT) data
hint_df = pd.read_csv(HINT_FILE)

print("Field_A_HINT data loaded")
print(f"Total rows: {len(hint_df)}")
print(f"Columns: {list(hint_df.columns)}")

# Create a DATE column from YEAR, MONTH, and DAY
hint_df["DATE"] = pd.to_datetime(
    {
        "year": hint_df["YEAR"],
        "month": hint_df["MONTH"],
        "day": hint_df["DAY"]
    },
    errors="coerce"
)

print("\nHINT date range:")
print(hint_df["DATE"].min(), "to", hint_df["DATE"].max())
# Load Field A (HINT) QC results
hint_qc_file = PROCESSED_DIR / "Field_A_HINT_QC_results.csv"

hint_qc = pd.read_csv(hint_qc_file)

print("\nHINT QC results loaded")
print(f"QC rows: {len(hint_qc)}")
print(f"QC columns: {list(hint_qc.columns)}")
# Identify flagged HINT observations
flagged_hint = hint_qc[
    hint_qc["QC_REASONS"].notna()
    & (hint_qc["QC_REASONS"].astype(str).str.strip() != "")
].copy()

print("\nFlagged HINT observations:")
print(flagged_hint[["YEAR", "MONTH", "DAY", "STID", "QC_REASONS"]].to_string(index=False))

print(f"\nNumber of flagged HINT observations: {len(flagged_hint)}")
