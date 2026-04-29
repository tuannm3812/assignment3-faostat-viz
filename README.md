# Global Food Price Shocks and Hunger Index Analysis

## Project Overview

This project analyzes global food price shocks using FAOSTAT data and correlates them with the Global Hunger Index. The goal is to provide insights into how price fluctuations impact food security worldwide.

The project includes:
- Data fetching and cleaning scripts
- Exploratory data analysis notebooks
- An interactive Streamlit dashboard for visualization

## Folder Structure

- `data/raw/`: Raw data files downloaded from FAOSTAT and other sources. This folder is gitignored except for .gitkeep.
- `data/processed/`: Cleaned and processed data ready for analysis. This folder is gitignored except for .gitkeep.
- `notebooks/`: Jupyter notebooks for exploratory data analysis and visualization.
  - `01_data_api/`: Notebooks for fetching data from FAOSTAT and other dataset APIs.
  - `02_analysis/`: Notebooks for exploratory data analysis and visualization.
- `src/data/`: Python scripts for data fetching, cleaning, and preprocessing.
- `app/`: Streamlit application for the interactive dashboard.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Git

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Notebooks
1. Activate the virtual environment (if not already activated).
2. Start Jupyter:
   ```
   jupyter notebook
   ```
3. Navigate to the `notebooks/` folder and open desired notebooks.

### Running the Streamlit App
1. Activate the virtual environment (if not already activated).
2. Run the app:
   ```
   streamlit run app/main.py
   ```
3. Open your browser to the provided URL (usually http://localhost:8501).

## Branching Policy

- `main`: Production-ready code. Only merge via pull requests after review.
- `develop`: Integration branch for features. Merge feature branches here.
- `feature/*`: Feature branches. Create from develop, merge back to develop.
- `hotfix/*`: Emergency fixes. Create from main, merge to both main and develop.

Always create pull requests for merging, and ensure CI/CD passes before merging.