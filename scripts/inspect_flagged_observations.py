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

# Create DATE for flagged HINT observations
flagged_hint["DATE"] = pd.to_datetime(
    {
        "year": flagged_hint["YEAR"],
        "month": flagged_hint["MONTH"],
        "day": flagged_hint["DAY"]
    },
    errors="coerce"
)

print("\nFlagged HINT dates:")
print(flagged_hint["DATE"].to_string(index=False))
print("\nFlagged HINT observations:")
print(flagged_hint[["YEAR", "MONTH", "DAY", "STID", "QC_REASONS"]].to_string(index=False))

print(f"\nNumber of flagged HINT observations: {len(flagged_hint)}")

# Inspect the 3-day neighbourhood around the first flagged date
first_flagged_date = flagged_hint.iloc[0]["DATE"]

start_date = first_flagged_date - pd.Timedelta(days=3)
end_date = first_flagged_date + pd.Timedelta(days=3)

hint_neighbourhood = hint_df[
    hint_df["DATE"].between(start_date, end_date)
].copy()

print("\n" + "=" * 70)
print("HINT — FIRST FLAGGED OBSERVATION")
print("=" * 70)

print(f"Flagged date : {first_flagged_date.date()}")
print(f"Inspection period : {start_date.date()} to {end_date.date()}")

print("\nSurrounding observations:")

columns_to_show = [
    "DATE",
    "STID",
    "RAIN",
    "ATOT",
    "AMAX",
    "TMAX",
    "TMIN"
]

available_columns = [
    col for col in columns_to_show
    if col in hint_neighbourhood.columns
]

print(
    hint_neighbourhood[available_columns]
    .sort_values("DATE")
    .to_string(index=False)
)
