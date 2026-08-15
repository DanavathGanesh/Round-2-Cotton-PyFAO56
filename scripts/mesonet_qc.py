import pandas as pd
from pathlib import Path


# ============================================================
# Mesonet Data Quality Control
# Fields:
#   Field A = HINT (Hinton)
#   Field B = FTCB (Fort Cobb)
#
# The routine:
# 1. Checks missing values
# 2. Checks duplicate dates
# 3. Checks date continuity
# 4. Checks physical ranges
# 5. Checks internal physical consistency
# 6. Produces row-level QC flags
# 7. Produces a QC summary
#
# Raw data are NOT modified.
# ============================================================


# ------------------------------------------------------------
# File locations
# ------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "Field_A_HINT": REPO_ROOT / "data" / "raw" / "Field_A_HINT_mesonet_data.csv",
    "Field_B_FTCB": REPO_ROOT / "data" / "raw" / "Field_B_FTCB_mesonet_data.csv",
}

OUTPUT_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Expected variables
# ------------------------------------------------------------

EXPECTED_COLUMNS = [
    "YEAR", "MONTH", "DAY", "STID",
    "RAIN",
    "TMAX", "TMIN", "HAVG",
    "2AVG", "ATOT", "TAVG",
    "HMAX", "HMIN", "2MAX",
    "DAVG", "DMAX", "DMIN",
    "AMAX", "TR60", "S60AV"
]


# ------------------------------------------------------------
# Physical limits
# ------------------------------------------------------------

# These are broad screening limits.
# They are intended to identify impossible observations,
# not to remove physically unusual but possible weather events.

LIMITS = {
    "RAIN": (0, None),       # inches/day
    "TMAX": (-40, 140),      # deg F
    "TMIN": (-40, 140),      # deg F
    "TAVG": (-40, 140),      # deg F
    "HAVG": (0, 100),        # %
    "HMAX": (0, 100),        # %
    "HMIN": (0, 100),        # %
    "2AVG": (0, None),       # mph
    "2MAX": (0, None),       # mph
    "ATOT": (0, None),       # MJ/m2/day
    "AMAX": (0, None),       # W/m2
    "S60AV": (-40, 140),     # deg F
}


def load_data(path):
    """Read a Mesonet CSV and create a date column."""

    df = pd.read_csv(path)

    # Remove accidental whitespace from column names
    df.columns = df.columns.str.strip()

    missing_columns = [
        c for c in EXPECTED_COLUMNS
        if c not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{path.name}: Missing expected columns: "
            f"{missing_columns}"
        )

    df["DATE"] = pd.to_datetime(
        dict(
            year=df["YEAR"],
            month=df["MONTH"],
            day=df["DAY"]
        ),
        errors="coerce"
    )

    return df


def run_qc(df, field_name):

    df = df.copy()

    # --------------------------------------------------------
    # Create QC flag columns
    # --------------------------------------------------------

    df["QC_FLAG"] = False
    df["QC_REASONS"] = ""

    def add_flag(mask, reason):
        mask = mask.fillna(False)

        df.loc[mask, "QC_FLAG"] = True

        existing = df.loc[mask, "QC_REASONS"]

        df.loc[mask, "QC_REASONS"] = existing.where(
            existing.eq(""),
            existing + "; "
        ) + reason

    # --------------------------------------------------------
    # 1. Invalid dates
    # --------------------------------------------------------

    add_flag(
        df["DATE"].isna(),
        "Invalid date"
    )

    # --------------------------------------------------------
    # 2. Missing values
    # --------------------------------------------------------

    for col in EXPECTED_COLUMNS:

        if col in ["YEAR", "MONTH", "DAY", "STID"]:
            continue

        add_flag(
            df[col].isna(),
            f"Missing {col}"
        )

    # --------------------------------------------------------
    # 3. Duplicate dates
    # --------------------------------------------------------

    duplicate_date = df["DATE"].duplicated(
        keep=False
    )

    add_flag(
        duplicate_date,
        "Duplicate date"
    )

    # --------------------------------------------------------
    # 4. Physical range checks
    # --------------------------------------------------------

    for col, (lower, upper) in LIMITS.items():

        if col not in df.columns:
            continue

        if lower is not None:
            add_flag(
                df[col] < lower,
                f"{col} below physical minimum"
            )

        if upper is not None:
            add_flag(
                df[col] > upper,
                f"{col} above physical maximum"
            )

    # --------------------------------------------------------
    # 5. Temperature consistency
    # --------------------------------------------------------

    # Tmin cannot exceed Tmax
    add_flag(
        df["TMIN"] > df["TMAX"],
        "TMIN greater than TMAX"
    )

    # TAVG should lie between Tmin and Tmax
    add_flag(
        (df["TAVG"] < df["TMIN"]) |
        (df["TAVG"] > df["TMAX"]),
        "TAVG outside Tmin-Tmax range"
    )

    # --------------------------------------------------------
    # 6. Relative-humidity consistency
    # --------------------------------------------------------

    # HAVG should lie between HMIN and HMAX
    add_flag(
        (df["HAVG"] < df["HMIN"]) |
        (df["HAVG"] > df["HMAX"]),
        "HAVG outside HMIN-HMAX range"
    )

    # HMIN cannot exceed HMAX
    add_flag(
        df["HMIN"] > df["HMAX"],
        "HMIN greater than HMAX"
    )

    # --------------------------------------------------------
    # 7. Wind-speed consistency
    # --------------------------------------------------------

    add_flag(
        df["2AVG"] > df["2MAX"],
        "Average wind speed greater than maximum wind speed"
    )

    # --------------------------------------------------------
    # 8. Dew-point consistency
    # --------------------------------------------------------

    # Maximum dew point should not exceed maximum air temperature
    add_flag(
        df["DMAX"] > df["TMAX"],
        "DMAX greater than TMAX"
    )

    # Minimum dew point should not exceed maximum dew point
    add_flag(
        df["DMIN"] > df["DMAX"],
        "DMIN greater than DMAX"
    )

    # --------------------------------------------------------
    # 9. Solar-radiation consistency
    # --------------------------------------------------------

    # Daily total radiation and maximum radiation must be nonnegative
    add_flag(
        df["ATOT"] < 0,
        "Negative total solar radiation"
    )

    add_flag(
        df["AMAX"] < 0,
        "Negative maximum solar radiation"
    )

    # --------------------------------------------------------
    # 10. Date continuity
    # --------------------------------------------------------

    sorted_dates = df["DATE"].dropna().sort_values()

    if len(sorted_dates) > 1:

        date_diff = sorted_dates.diff().dt.days

        missing_day_mask = date_diff > 1

        missing_intervals = int(
            missing_day_mask.sum()
        )

    else:
        missing_intervals = 0

    # --------------------------------------------------------
    # Summary statistics
    # --------------------------------------------------------

    total_rows = len(df)

    flagged_rows = int(
        df["QC_FLAG"].sum()
    )

    summary = {
        "Field": field_name,
        "Rows": total_rows,
        "Flagged_rows": flagged_rows,
        "Flagged_percent": (
            100 * flagged_rows / total_rows
            if total_rows > 0 else 0
        ),
        "Missing_date": int(
            df["DATE"].isna().sum()
        ),
        "Duplicate_dates": int(
            duplicate_date.sum()
        ),
        "Missing_date_intervals": missing_intervals,
    }

    # --------------------------------------------------------
    # Count individual QC problems
    # --------------------------------------------------------

    reason_counts = {}

    for reason in df.loc[
        df["QC_FLAG"],
        "QC_REASONS"
    ]:

        for item in reason.split("; "):

            reason_counts[item] = (
                reason_counts.get(item, 0) + 1
            )

    for reason, count in reason_counts.items():

        summary[
            reason.replace(" ", "_")
                  .replace("-", "_")
        ] = count

    return df, pd.DataFrame([summary])


def main():

    all_summaries = []

    for field_name, file_path in FILES.items():

        print("\n" + "=" * 70)
        print(f"Processing: {field_name}")
        print("=" * 70)

        if not file_path.exists():

            print(
                f"WARNING: File not found:\n{file_path}"
            )

            continue

        df = load_data(file_path)

        qc_df, summary_df = run_qc(
            df,
            field_name
        )

        # ----------------------------------------------------
        # Save row-level QC results
        # ----------------------------------------------------

        output_file = (
            OUTPUT_DIR /
            f"{field_name}_QC_results.csv"
        )

        qc_df.to_csv(
            output_file,
            index=False
        )

        # ----------------------------------------------------
        # Save summary
        # ----------------------------------------------------

        summary_file = (
            OUTPUT_DIR /
            f"{field_name}_QC_summary.csv"
        )

        summary_df.to_csv(
            summary_file,
            index=False
        )

        all_summaries.append(summary_df)

        print(
            f"Total rows: {len(df)}"
        )

        print(
            f"Flagged rows: "
            f"{int(qc_df['QC_FLAG'].sum())}"
        )

        print(
            f"QC results saved to:\n"
            f"{output_file}"
        )

    # --------------------------------------------------------
    # Combined summary
    # --------------------------------------------------------

    if all_summaries:

        combined_summary = pd.concat(
            all_summaries,
            ignore_index=True
        )

        combined_file = (
            OUTPUT_DIR /
            "Mesonet_QC_combined_summary.csv"
        )

        combined_summary.to_csv(
            combined_file,
            index=False
        )

        print("\n" + "=" * 70)
        print("COMBINED QC SUMMARY")
        print("=" * 70)

        print(
            combined_summary.to_string(
                index=False
            )
        )

        print(
            f"\nCombined summary saved to:\n"
            f"{combined_file}"
        )


if __name__ == "__main__":
    main()
