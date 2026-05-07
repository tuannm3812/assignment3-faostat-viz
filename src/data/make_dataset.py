"""Data cleaning helpers for FAOSTAT producer price files."""

import pandas as pd
from typing import Optional
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def clean_faostat_data(raw_filepath: str, processed_filepath: str) -> Optional[pd.DataFrame]:
    """
    Clean raw FAOSTAT data and save to processed filepath.

    Args:
        raw_filepath (str): Path to the raw data file.
        processed_filepath (str): Path to save the processed data.

    Returns:
        Optional[pd.DataFrame]: Cleaned DataFrame if successful, None otherwise.
    """
    try:
        # Placeholder for data cleaning logic
        raw_df = pd.read_csv(raw_filepath)
        # Add cleaning steps here
        cleaned_df = raw_df  # Placeholder
        cleaned_df.to_csv(processed_filepath, index=False)
        return cleaned_df
    except Exception as e:
        print(f"Error cleaning data: {e}")
        return None


if __name__ == "__main__":
    raw_path = RAW_DIR / "faostat_raw.csv"
    processed_path = PROCESSED_DIR / "faostat_processed.csv"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean_faostat_data(str(raw_path), str(processed_path))
