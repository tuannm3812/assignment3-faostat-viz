# Food Price Shock Early Warning Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Pipeline-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Analytical%20Charts-3F4F75?logo=plotly&logoColor=white)

![FAO field work in South Sudan](https://www.fao.org/images/faofooterlibraries/default-album/south-sudan.jpg?sfvrsn=3f04ca76_11)

Interactive Streamlit dashboard for exploring food-price shock signals and identifying countries that may be structurally exposed to global food-price pressure.

Live dashboard: https://assignment3-faostat-viz.streamlit.app/

Walkthrough video: https://www.youtube.com/watch?v=5pSiKvORCVw

## 1. Run The Demo

### Streamlit Cloud

Open the hosted dashboard:

https://assignment3-faostat-viz.streamlit.app/

### Local Demo

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```

The local dashboard usually opens at `http://localhost:8501`.

## 2. Dashboard Scope

The app combines:

1. FAOSTAT producer prices for Australia and New Zealand.
2. FAO Food Price Index global shock context.
3. Global Hunger Index vulnerability data.
4. World Bank food import dependency data.

Producer-price coverage in the processed files is:

1. USD producer prices: 1991-2024.
2. Local-currency producer prices: 1991-2024.
3. Producer-price index: 1991-2025.

The dashboard uses cleaned CSV files from `data/processed/`.

## 3. Repository Structure

```text
assignment3-faostat-viz/
|-- app/
|   |-- main.py                         # Streamlit entry point
|   |-- config.py                       # paths, palette, assumptions
|   |-- data.py                         # cached local data loading
|   |-- analysis.py                     # exposure, scenario, sensitivity logic
|   |-- controls.py                     # sidebar controls
|   |-- tabs/                           # one renderer per dashboard tab
|   `-- style.py                        # shared chart and callout styling
|-- data/
|   |-- raw/                            # original source downloads
|   `-- processed/                      # cleaned CSVs used by the app
|-- docs/
|   |-- part3_final_portfolio.md        # final portfolio documentation
|   `-- archive/                        # supporting preparation files
|-- notebooks/
|   |-- 01_data_preparation/
|   `-- 02_exploratory_analysis/
|-- requirements.txt
`-- README.md
```

## 4. Key Files

1. `app/main.py`: Streamlit page setup, data loading, sidebar controls, and tab rendering.
2. `app/data.py`: cached loading and type handling for processed CSV files.
3. `app/analysis.py`: exposure index, what-if scenario logic, FFPI correlation, and sensitivity analysis.
4. `app/controls.py`: global sidebar filters and model inputs.
5. `app/tabs/`: dashboard tab renderers.
6. `docs/part3_final_portfolio.md`: methodology, data dictionary, limitations, credits, and technical documentation.

## 5. Data Pipeline

The dashboard reads these cleaned files from `data/processed/`:

1. `master_producer_prices_usd.csv`
2. `master_producer_price_index.csv`
3. `master_producer_prices_lcu.csv`
4. `ffpi_monthly.csv`
5. `ffpi_annual.csv`
6. `ghi_cleaned.csv`
7. `worldbank_food_import_pct.csv`

The main cleaning workflow is documented in `notebooks/01_data_preparation/01_data_cleaning_pipeline.ipynb`.

## 6. Documentation

Final portfolio documentation:

[docs/part3_final_portfolio.md](docs/part3_final_portfolio.md)
