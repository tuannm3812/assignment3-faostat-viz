# FAOSTAT Food Price Shock Visualisation

Interactive Streamlit dashboard for exploring FAOSTAT producer prices for Australia and New Zealand, enriched with FAO Food Price Index, Global Hunger Index, and World Bank food import dependency data.

The current app runs from local CSV files. A realtime FAOSTAT/API ingestion layer can be added later without changing the dashboard structure.

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
├── app/
│   └── main.py                         # Streamlit dashboard
├── data/
│   ├── raw/                            # Original downloads only
│   └── processed/                      # Cleaned CSVs used by the app
├── notebooks/
│   ├── 01_data_api/
│   │   └── FPP_data_cleaning_pipeline.ipynb
│   └── 02_analysis/
│       └── FPP_EDA.ipynb
├── src/
│   └── data/
│       └── make_dataset.py             # Data cleaning entry point placeholder
├── requirements.txt
└── README.md
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
  --param area=36 ^
  --param area=554 ^
  --output data/raw/faostat_producer_prices.csv
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
- `Data Explorer`: inspect the local CSV tables.

## Next API Step

When the FAOSTAT API guideline is ready, add ingestion code under `src/data/`, write cleaned outputs to `data/processed/`, and keep `app/main.py` reading the same table names. That keeps the dashboard stable while the data source changes from local files to realtime refreshes.
