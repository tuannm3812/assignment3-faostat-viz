"""
Script for fetching and cleaning FAOSTAT data.
"""

import pandas as pd
from typing import Optional


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
    # Example usage
    raw_path = "../../data/raw/faostat_raw.csv"
    processed_path = "../../data/processed/faostat_processed.csv"
    clean_faostat_data(raw_path, processed_path)