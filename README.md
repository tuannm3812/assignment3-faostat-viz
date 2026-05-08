# FAOSTAT Food Price Shock Visualisation

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Pipeline-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?logo=plotly&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-F37626?logo=jupyter&logoColor=white)
![FAOSTAT](https://img.shields.io/badge/Data-FAOSTAT-2E7D32)

![FAO field work in South Sudan](https://www.fao.org/images/faofooterlibraries/default-album/south-sudan.jpg?sfvrsn=3f04ca76_11)

Interactive Streamlit dashboard for exploring FAOSTAT producer prices for Australia and New Zealand, enriched with FAO Food Price Index, Global Hunger Index, and World Bank food import dependency data.

Live app: https://assignment3-faostat-viz.streamlit.app/

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

## Data Scope and Enrichment Logic

The primary FAOSTAT dataset is intentionally focused on **Australia and New Zealand producer prices**. These countries are used as the supply-side case study because they are major food-producing and exporting economies in the Asia-Pacific region. The dashboard asks: when producer prices rise in this supplier context, which countries are most exposed to food-price stress?

The enrichment datasets add the demand-side and global-risk context:

- **FAO Food Price Index (FFPI)** is joined by `year` to show whether AUS/NZ producer price movements align with global food price shocks such as 2007-2008, 2010-2011, and 2022.
- **Global Hunger Index (GHI)** is used as a global vulnerability layer. AUS and NZL are high-income countries and do not have meaningful GHI scores in this dataset, so GHI is not expected to enrich AUS/NZ rows directly. Instead, it powers the global hunger map and vulnerability matrix.
- **World Bank food import dependency** measures how exposed countries are to international food-price changes. Combined with GHI, it identifies countries that may be less able to absorb price shocks.

This means the project links supply-side price shocks from AUS/NZ with global exposure indicators from GHI and World Bank data. A future extension could expand the FAOSTAT producer-price pull to more exporting countries, but the current scope keeps the narrative focused and easier to interpret.

## Repository Structure

```text
assignment3-faostat-viz/
|-- app/
|   `-- main.py                         # Streamlit dashboard
|-- data/
|   |-- raw/                            # Original downloads only
|   `-- processed/                      # Cleaned CSVs used by the app
|-- notebooks/
|   |-- 01_data_preparation/
|   |   `-- 01_data_cleaning_pipeline.ipynb
|   `-- 02_exploratory_analysis/
|       `-- 02_exploratory_analysis.ipynb
|-- src/
|   `-- data_pipeline/
|       |-- faostat_client.py           # FAOSTAT API helper
|       `-- make_dataset.py             # Data cleaning entry point placeholder
|-- requirements.txt
`-- README.md
```

## Local Data Files

Raw source files used to rerun the cleaning notebook live in `data/raw/`:

- `faostat_producer_prices_aus_nzl.csv`
- `fao_food_price_index.xlsx`
- `global_hunger_index.xlsx`
- `worldbank_food_import_raw.csv`

Place these cleaned files in `data/processed/`:

- `master_producer_prices_usd.csv`
- `master_producer_price_index.csv`
- `master_producer_prices_lcu.csv`
- `ffpi_monthly.csv`
- `ffpi_annual.csv`
- `ghi_cleaned.csv`
- `worldbank_food_import_pct.csv`

The dashboard reads the cleaned tables in `data/processed/`. The raw files are only needed when rerunning the cleaning notebook from scratch.

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
python -c "from src.data_pipeline.faostat_client import get_groups_and_domains; print(get_groups_and_domains().head())"
```

Example data retrieval matching the FAOSTAT guide:

```bash
python -m src.data_pipeline.faostat_client ^
  --domain QCL ^
  --param area=106 ^
  --param item=15 ^
  --param element=2510 ^
  --param year=2022 ^
  --output data/raw/faostat_qcl_italy_wheat_2022.csv
```

For Producer Prices, use the `PP` domain code and the relevant FAOSTAT query parameters:

```bash
python -m src.data_pipeline.faostat_client ^
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

Both notebooks resolve the repository root automatically, so they can be run from Jupyter after cloning without copying files into the notebook folders.

- `notebooks/01_data_preparation/01_data_cleaning_pipeline.ipynb` reads from `data/raw/` and writes to `data/processed/`.
- `notebooks/02_exploratory_analysis/02_exploratory_analysis.ipynb` reads from `data/processed/`.
- `app/main.py` also reads from `data/processed/`.

## Dashboard Views

- `Overview`: coverage, commodity count, producer price rows, latest FFPI, and top vulnerability scores.
- `Price Trends`: selectable commodity time series for Australia/New Zealand with FFPI overlay and crisis-year bands.
- `Volatility`: highest coefficient-of-variation commodities by country.
- `Global Context`: FFPI annual and monthly shock timelines plus GHI choropleth.
- `Vulnerability`: GHI x food import dependency scatter and what-if shock scenario.
- `Live FAOSTAT`: realtime Producer Prices API preview using your local `FAOSTAT_ACCESS_TOKEN`.
- `Data Explorer`: inspect the local CSV tables.

## Next API Step

Use the `Live FAOSTAT` page to confirm API filters, then move the confirmed query into the data pipeline under `src/data_pipeline/`. The pipeline should write cleaned outputs to `data/processed/`, and the main dashboard should keep reading the same table names. That keeps the dashboard stable while the data source changes from static local files to refreshed API data.
