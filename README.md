# FAOSTAT Food Price Shock Visualisation

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Pipeline-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-F37626?logo=jupyter&logoColor=white)
![FAOSTAT](https://img.shields.io/badge/Data-FAOSTAT-2E7D32)

![FAO field work in South Sudan](https://www.fao.org/images/faofooterlibraries/default-album/south-sudan.jpg?sfvrsn=3f04ca76_11)

Interactive Streamlit dashboard for exploring FAOSTAT producer prices for Australia and New Zealand, enriched with FAO Food Price Index, Global Hunger Index, and World Bank food import dependency data.

The main analytical dashboard runs from local cleaned CSV files. A `Live FAOSTAT` page is included for testing realtime API pulls before those data are transformed into the dashboard-ready `data/processed` tables.

## Project Story

The dashboard follows the group's Sparkline narrative:

> When Australia and New Zealand commodity prices spike alongside global food prices, import-dependent and hunger-vulnerable countries face the highest food security risk.

The main analytical layers are:

- Producer price trends for AUS/NZ commodities in USD per tonne.
- Commodity volatility using coefficient of variation.
- Global FAO Food Price Index shock context.
- Global Hunger Index context.
- Vulnerability matrix combining hunger severity and food import dependency.
- What-if scenario slider for producer price shocks.

## Repository Structure

```text
assignment3-faostat-viz/
|-- app/
|   `-- main.py                         # Streamlit dashboard
|-- data/
|   |-- raw/                            # Original downloads only
|   `-- processed/                      # Cleaned CSVs used by the app
|-- notebooks/
|   |-- 01_data_api/
|   |   `-- FPP_data_cleaning_pipeline.ipynb
|   `-- 02_analysis/
|       `-- FPP_EDA.ipynb
|-- src/
|   `-- data/
|       |-- faostat_client.py           # FAOSTAT API helper
|       `-- make_dataset.py             # Data cleaning entry point placeholder
|-- requirements.txt
`-- README.md
```

## Local Data Files

Place these cleaned files in `data/processed/`:

- `master_producer_prices_usd.csv`
- `master_producer_price_index.csv`
- `master_producer_prices_lcu.csv`
- `ffpi_monthly.csv`
- `ffpi_annual.csv`
- `ghi_cleaned.csv`
- `worldbank_food_import_pct.csv`

The app also checks `data/raw/` as a fallback for older local layouts, but the preferred structure is `data/processed/`.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with:

```bash
source venv/bin/activate
```

## Run the Dashboard

```bash
streamlit run app/main.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## FAOSTAT API Access

The API client reads your token from `.env` or the active shell environment. Do not commit real tokens.

Create a local `.env` file from the example:

```bash
copy .env.example .env
```

Then edit `.env`:

```text
FAOSTAT_ACCESS_TOKEN=your_current_access_token
```

FAOSTAT access tokens are short-lived, so refresh this value when it expires.

Example API discovery call from Python:

```bash
python -c "from src.data.faostat_client import get_groups_and_domains; print(get_groups_and_domains().head())"
```

Example data retrieval matching the FAOSTAT guide:

```bash
python -m src.data.faostat_client ^
  --domain QCL ^
  --param area=106 ^
  --param item=15 ^
  --param element=2510 ^
  --param year=2022 ^
  --output data/raw/faostat_qcl_italy_wheat_2022.csv
```

For Producer Prices, use the `PP` domain code and the relevant FAOSTAT query parameters:

```bash
python -m src.data.faostat_client ^
  --domain PP ^
  --param area=5501^> ^
  --param element=5530,5532,5539 ^
  --param item=809 ^
  --param year=2025,2024,2023 ^
  --param month=7021 ^
  --output data/raw/faostat_producer_prices.csv
```

This matches the API Query Builder pattern:

```text
https://faostatservices.fao.org/api/v1/en/data/PP?area=5501%3E&element=5530%2C5532%2C5539&item=809&year=2025%2C2024%2C2023&month=7021&output_type=csv
```

## Notebook Path Notes

The notebooks currently contain relative paths that assume the notebook is run from a folder containing the source or cleaned files directly. For the repo structure above, use these conventions when updating notebook cells:

- Raw downloads: `../../data/raw/<filename>`
- Cleaned outputs: `../../data/processed/<filename>`
- Dashboard reads: `data/processed/<filename>` from the repo root

Recommended output path in the cleaning notebook:

```python
from pathlib import Path

ROOT_DIR = Path.cwd().parents[1]
OUT_DIR = ROOT_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
```

## Dashboard Views

- `Overview`: coverage, commodity count, producer price rows, latest FFPI, and top vulnerability scores.
- `Price Trends`: selectable commodity time series for Australia/New Zealand with FFPI overlay and crisis-year bands.
- `Volatility`: highest coefficient-of-variation commodities by country.
- `Global Context`: FFPI annual and monthly shock timelines plus GHI choropleth.
- `Vulnerability`: GHI x food import dependency scatter and what-if shock scenario.
- `Live FAOSTAT`: realtime Producer Prices API preview using your local `FAOSTAT_ACCESS_TOKEN`.
- `Data Explorer`: inspect the local CSV tables.

## Next API Step

Use the `Live FAOSTAT` page to confirm API filters, then move the confirmed query into the data pipeline under `src/data/`. The pipeline should write cleaned outputs to `data/processed/`, and the main dashboard should keep reading the same table names. That keeps the dashboard stable while the data source changes from static local files to refreshed API data.
