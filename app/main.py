"""
Streamlit dashboard for analyzing global food price shocks and Global Hunger Index.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os


def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Load processed data from a CSV file.

    Args:
        filepath (str): Path to the processed data CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame with processed data.
    """
    if os.path.exists(filepath):
        data_df = pd.read_csv(filepath)
        return data_df
    else:
        st.error(f"File {filepath} not found.")
        return pd.DataFrame()


def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(layout="wide")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Overview", "Data Analysis", "Visualizations"])

    if page == "Overview":
        st.title("Global Food Price Shocks and Hunger Index Analysis")
        st.write("Welcome to the dashboard. Use the sidebar to navigate.")

    elif page == "Data Analysis":
        st.title("Data Analysis")
        # Placeholder for data loading
        faostat_df = load_processed_data("../data/processed/faostat_processed.csv")
        hunger_df = load_processed_data("../data/processed/hunger_index_processed.csv")

        if not faostat_df.empty:
            st.write("FAOSTAT Data Preview:")
            st.dataframe(faostat_df.head())

        if not hunger_df.empty:
            st.write("Hunger Index Data Preview:")
            st.dataframe(hunger_df.head())

    elif page == "Visualizations":
        st.title("Visualizations")
        # Placeholder for visualizations
        st.write("Visualizations will be added here.")


if __name__ == "__main__":
    main()