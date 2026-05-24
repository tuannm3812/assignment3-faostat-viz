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

The main analytical dashboard runs from local cleaned CSV files. A FAOSTAT API helper is included for testing realtime pulls before those data are transformed into the dashboard-ready `data/processed` tables.

## Project Story

The dashboard follows the group's Sparkline narrative:

> When Australia and New Zealand commodity prices spike alongside global food prices, import-dependent and hunger-vulnerable countries face the highest food security risk.

The main analytical layers are:

- Producer price trends for AUS/NZ commodities in USD per tonne.
- Commodity volatility using coefficient of variation.
- Global FAO Food Price Index shock context.
- Global Hunger Index context.
- Hunger-import exposure matrix combining hunger severity and food import dependency.
- What-if scenario slider for producer price shocks.
- Sensitivity analysis showing which priority countries remain robust across exposure-weight assumptions.

## Design System

The dashboard uses a consistent Streamlit and Plotly design system:

- Streamlit theme settings live in `.streamlit/config.toml`.
- Shared chart colours are defined in `app/main.py`.
- Modern policy palette: ocean teal, clear blue, amber, rose, navy, and slate.
- Teal and blue identify the AUS/NZ producer-price signal.
- Amber identifies food-price shock context; rose/red is reserved for higher exposure.
- Charts use a common white Plotly template, consistent margins, and standard hover tooltips.

## Data Scope and Enrichment Logic

The primary FAOSTAT dataset is intentionally focused on **Australia and New Zealand producer prices**. These countries are used as the supply-side case study because they are major food-producing and exporting economies in the Asia-Pacific region. The dashboard asks: when producer prices rise in this supplier context, which countries are most exposed to food-price stress?

The enrichment datasets add the demand-side and global-risk context:

- **FAO Food Price Index (FFPI)** is joined by `year` to show whether AUS/NZ producer price movements align with global food price shocks such as 2007-2008, 2010-2011, and 2022.
- **Global Hunger Index (GHI)** is used as a global vulnerability layer. AUS and NZL are high-income countries and do not have meaningful GHI scores in this dataset, so GHI is not expected to enrich AUS/NZ rows directly. Instead, it powers the global hunger map and exposure matrix.
- **World Bank food import dependency** measures how exposed countries are to international food-price changes. Combined with GHI, it identifies countries that may be less able to absorb price shocks.

This means the project links supply-side price shocks from AUS/NZ with global exposure indicators from GHI and World Bank data. A future extension could expand the FAOSTAT producer-price pull to more exporting countries, but the current scope keeps the narrative focused and easier to interpret.

## Exposure Index Methodology

Earlier prototypes used a simple multiplication of `GHI score x food import %`. We replaced that with a normalized weighted index because the two variables are on different scales and should not be assumed to compound equally.

Current method:

```text
ghi_norm = min-max scaled GHI 2025 score
import_norm = min-max scaled latest food imports as % of merchandise imports

hunger_import_exposure_index = (0.60 x ghi_norm + 0.40 x import_norm) x 100
```

Rationale:

- GHI receives the higher weight because hunger severity is the direct human-centered risk.
- Food import dependency receives a lower weight because it is an exposure pathway, not proof of food insecurity by itself.
- Min-max scaling puts both inputs on the same 0-1 scale before combining them.

The what-if scenario is also treated as illustrative rather than causal:

```text
global_price_pressure = producer_price_shock x basket_share x transmission_coeff x pass_through_rate
implied_import_cost_pressure = food_import_pct x global_price_pressure / 100
scenario_pressure_score = exposure_index x implied_import_cost_pressure / 100
```

The basket share, transmission coefficient, and pass-through rate are controlled in the dashboard because producer prices do not translate directly into import prices. Shipping costs, exchange rates, trade margins, policy buffers, and supplier substitution can all absorb or amplify shocks.

Important caveats:

- The model does **not** use bilateral trade-flow data, so it does not prove that a specific country imports food from Australia or New Zealand.
- The model does **not** estimate exchange-rate effects, freight costs, tariffs, subsidies, or supply substitution.
- The exposure index identifies countries that are structurally vulnerable to global food-price stress, not countries directly dependent on AUS/NZ supply.
- Results should be interpreted as a prioritization and storytelling tool, not as a causal economic forecast.

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
|       |-- 04_part2_visual_story_analysis.ipynb
|       `-- archive/                    # Earlier exploratory notebooks
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

The dashboard supports two safe ways to use a FAOSTAT token. Do not commit real tokens.

### Option 1: Paste Token in Streamlit

Use the local `.env` option or a current FAOSTAT token when testing API pulls with the helper module.

Get a token from the [FAOSTAT Developer Portal](https://www.fao.org/faostat/en/#developer-portal). Tokens are short-lived, so refresh the token if the API request starts failing.

This is the easiest option for deployed demos because teammates do not need to create a local `.env` file.

### Option 2: Local `.env`

The API client also reads your token from `.env` or the active shell environment.

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
- `notebooks/02_exploratory_analysis/04_part2_visual_story_analysis.ipynb` reads from `data/processed/` and contains exploratory visual story analysis from the pitch phase.
- `app/main.py` also reads from `data/processed/`.

## Dashboard Views

The sidebar acts as the global control panel for filters and model assumptions. The main canvas uses tabs for the narrative flow.

- `Executive Brief`: stakeholder framing, priority watchlist, and recommended narrative route.
- `1. Shock Context`: global food-price shock periods and FFPI evidence.
- `2. Producer Signal`: Australia/New Zealand producer-price evidence and FFPI alignment.
- `3. Vulnerability`: hunger-import exposure matrix, policy watchlist, and sensitivity analysis.
- `4. What-If Action`: parameterized shock/pass-through scenario and priority-country ranking.
- `5. Evidence Base`: source tables and commodity volatility checks.

## Assessment Documents

- [Assignment 3 Part 3 Instructions Summary](docs/1_instructions.md)
- [Part 3 Final Portfolio Plan](docs/part3_final_portfolio.md)
- [Team To-Do List](docs/team_todo.md)
- Archived Part 2 materials live under `docs/archive/`.

## Next API Step

Use `src/data_pipeline/faostat_client.py` to confirm API filters, then move the confirmed query into the data pipeline under `src/data_pipeline/`. The pipeline should write cleaned outputs to `data/processed/`, and the main dashboard should keep reading the same table names. That keeps the dashboard stable while the data source changes from static local files to refreshed API data.
