# Technical Video Walkthrough Transcript

Target length: approximately 3 minutes.

## Transcript

### 0:00-0:20 - Opening

Hello, this is Group 16's technical walkthrough for the Food Price Shock Early Warning dashboard.

This walkthrough focuses on the technical delivery: how the Streamlit app is structured, how it loads and transforms data, and how the interactive features support the food-security decision workflow.

### 0:20-0:45 - App Layout and User Flow

The dashboard uses a sidebar for analysis controls and a tabbed main canvas for the narrative workflow.

The sidebar defines the analysis scope: year range, FAO Food Price Index series, producer commodity, producer countries, exposure weights, and scenario assumptions. The main view then organises the output into Executive Brief, Shock Context, Producer Signal, Vulnerability, What-If Action, and Evidence Base.

This layout gives users one consistent control panel while each tab presents a specific analytical step.

### 0:45-1:15 - Repository and Code Structure

The Streamlit entry point is `app/main.py`. It sets the page configuration, loads the prepared data, creates the sidebar controls, and renders the dashboard tabs.

The implementation is split into focused modules:

- `app/config.py` stores file paths, colour constants, chart palettes, crisis periods, and model defaults.
- `app/data.py` loads the cleaned CSV files and applies type conversion.
- `app/analysis.py` contains the exposure index, scenario calculations, FFPI correlation logic, and sensitivity analysis.
- `app/controls.py` contains the sidebar widgets.
- `app/tabs/` contains one Streamlit renderer per dashboard tab.
- `app/style.py` contains reusable chart styling and narrative callout helpers.

This modular structure keeps data loading, analysis, controls, visual rendering, and styling in separate responsibilities.

### 1:15-1:40 - Data Pipeline and Performance

The dashboard reads from `data/processed` during runtime. This keeps the app responsive and reproducible.

In `app/data.py`, `load_data()` loads the processed FAOSTAT, FFPI, GHI, and World Bank tables. It uses `st.cache_data`, so Streamlit only reloads the data when the source files or code change.

The raw data and preparation notebooks remain in the repository for traceability, while the live app uses cleaned tables for fast interaction.

### 1:40-2:10 - Advanced Feature 1: Context-Aware Filtering

The first advanced feature is context-aware filtering.

In `app/controls.py`, the sidebar inputs are collected into one `controls` dictionary. That dictionary is passed into each tab renderer in the `app/tabs/` package.

For example, the year range and FFPI series update the Shock Context tab; the commodity and producer-country controls update the Producer Signal tab; and the exposure weight updates the Vulnerability and What-If tabs. This keeps the app state consistent across the dashboard.

### 2:10-2:35 - Advanced Feature 2: Tooltips and Visual Design

The second advanced feature is visual detail on demand.

The dashboard uses Plotly charts throughout the tab renderers, with hover templates and hover data exposing details such as country, year, producer price, food import dependency, exposure index, and scenario pressure score.

The design system is also centralised. `.streamlit/config.toml` defines the Streamlit theme, while `app/config.py` defines the policy palette. `app/style.py` applies consistent Plotly margins, backgrounds, grid styling, and crisis bands.

### 2:35-3:05 - Advanced Feature 3: What-If and Sensitivity Analysis

The third advanced feature is what-if parameterisation.

In `app/analysis.py`, `build_scenario()` calculates effective global pressure from producer shock, basket share, transmission coefficient, and pass-through rate. The What-If tab uses those assumptions to update the scenario priority ranking.

The sensitivity analysis is implemented in `build_weight_sensitivity()`. It tests food-access stress weights from 0.40 to 0.80 and identifies countries that stay in the top priority group across assumptions. This helps show whether a priority country is robust or only appears under one weighting choice.

### 3:05-3:25 - Evidence and Close

The Evidence Base tab exposes the cleaned datasets and commodity volatility checks. This supports transparency, because viewers can inspect the tables behind the charts.

Overall, the dashboard combines a hosted Streamlit app, a consistent design system, cached processed data, modular code organisation, context-aware controls, Plotly tooltips, what-if modelling, sensitivity analysis, and documented methodology and limitations.

## Shorter Version If Needed

This is Group 16's technical walkthrough for the Food Price Shock Early Warning dashboard. I will focus on how the app is built and how the technical features support the decision workflow.

The Streamlit entry point is `app/main.py`. It sets the page config, loads data, builds sidebar controls, and renders the tabbed dashboard. The rest of the app is split into modules: `config.py` for constants and colours, `data.py` for loading processed CSVs, `analysis.py` for exposure and scenario calculations, `controls.py` for sidebar widgets, `style.py` for reusable Plotly and Streamlit presentation helpers, and `app/tabs/` for one renderer per dashboard tab.

The app reads cleaned data from `data/processed` and uses `st.cache_data` for responsive load times. The sidebar controls are collected into a shared dictionary, which gives us context-aware filtering across the relevant tabs. Plotly hover tooltips reveal deeper data without cluttering the charts. The what-if model is implemented in `build_scenario()`, and the sensitivity analysis tests whether priority countries remain stable across different exposure-weight assumptions.

The design system is defined in `.streamlit/config.toml` and shared colour constants in `app/config.py`. The Evidence Base tab exposes cleaned source tables and volatility checks, making the dashboard transparent and auditable.
