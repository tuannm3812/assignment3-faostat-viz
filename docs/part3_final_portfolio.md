# Final Portfolio Technical Documentation

## Live Dashboard

Streamlit app: https://assignment3-faostat-viz.streamlit.app/

Walkthrough video: https://www.youtube.com/watch?v=5pSiKvORCVw

The dashboard is built for a UN food-systems panel or regional food-security policy board. It turns producer-price, global food-price, hunger, and import-dependency data into an early-warning view for food-security prioritisation.

## Decision Context

Food-price shocks do not affect all countries equally. A price rise may be manageable in one country and destabilising in another, depending on existing hunger severity, import dependency, and institutional capacity to absorb the pressure.

This dashboard supports one policy question:

> When producer-price and global food-price signals intensify, which countries should be prioritised for monitoring, preparedness, and policy support?

Australia and New Zealand are used as a focused supply-side case study because they are major food-producing economies in the Asia-Pacific region. The exposure analysis does not claim that vulnerable countries directly import from Australia or New Zealand. Instead, it links a producer-price signal with global food-price context and structural vulnerability indicators.

## Narrative Structure

The project uses a Sparkline narrative: it moves from observed pressure to policy-relevant action.

1. **What is happening:** global food-price index history and Australia/New Zealand producer-price movements show periods of price stress.
2. **Why it matters:** hunger severity and food import dependency show where equal price pressure may have unequal human consequences.
3. **What should happen next:** scenario controls and sensitivity analysis identify countries that should remain on a monitoring and preparedness watchlist.

## Portfolio Summary

The project delivers:

- A hosted Streamlit dashboard with a consistent design system.
- A modular Python implementation with cached local data loading.
- A documented data dictionary, methodology, limitations, and source credits.
- A 3-minute technical walkthrough focused on code organisation and advanced dashboard features.

## Dashboard Architecture

The main canvas uses a guided tab structure:

- `Executive Brief`
- `1. Shock Context`
- `2. Producer Signal`
- `3. Vulnerability`
- `4. What-If Action`
- `5. Evidence Base`

The sidebar is reserved for global filters and model assumptions. This keeps user interaction predictable while allowing charts, rankings, metrics, and narrative text to update dynamically.

## Data Scope

The dashboard combines four data layers:

| Dataset | Role in Dashboard | Key Fields |
|---|---|---|
| FAOSTAT Producer Prices | Supply-side commodity price signal for Australia and New Zealand | `country`, `iso3`, `item`, `year`, `value`, `unit` |
| FAO Food Price Index | Global food-price shock context | `year`, `ffpi_food`, `ffpi_cereals`, `ffpi_meat`, `ffpi_dairy`, `ffpi_oils`, `ffpi_sugar` |
| Global Hunger Index | Hunger and food-access vulnerability layer | `country`, `iso3`, `ghi_2025` |
| World Bank food import dependency | Exposure to international food-price changes | `country`, `iso3`, `food_import_pct` |

Producer-price coverage in the processed dashboard files is:

- USD producer prices: 1991-2024.
- Local-currency producer prices: 1991-2024.
- Producer-price index: 1991-2025.

The app runs from cleaned CSV files in `data/processed/`.

## Advanced Features

### Context-Aware Filtering

Implemented through global sidebar controls for year range, FFPI series, commodity, producer country, exposure weights, scenario assumptions, evidence dataset, and volatility country. Controls update the tabs where they are analytically relevant.

### Visual Tooltips

Implemented through Plotly hover tooltips across line charts, scatter plots, and bar charts. Tooltips expose country, year, commodity, data quality flags, GHI, food import dependency, exposure index, and scenario pressure.

### What-If Parameterisation

Implemented through sliders for:

- producer price shock,
- relevant import basket share,
- transmission coefficient,
- producer-to-import pass-through,
- food-access/import-dependency weighting,
- scenario priority ranking.

### Sensitivity Analysis

The What-If Action tab includes a robustness table and chart showing which countries remain in the top priority group when the food-access stress weight changes from 0.40 to 0.80.

## Data Dictionary

| Field | Type | Source | Description |
|---|---|---|---|
| `country` | string | FAOSTAT/GHI/World Bank | Country name. |
| `iso3` | string | Derived/source | ISO 3166-1 alpha-3 country code. |
| `item` | string | FAOSTAT | Commodity name. |
| `year` | integer | FAOSTAT/FFPI/World Bank | Observation year. |
| `value` | float | FAOSTAT | Producer price or producer price index value depending on file. |
| `unit` | string | FAOSTAT | Unit such as USD/tonne, LCU/tonne, or index. |
| `is_imputed` | boolean | Derived | True for FAOSTAT estimated or internationally sourced records. |
| `is_outlier` | boolean | Derived | IQR-based outlier flag within country-commodity group. |
| `ffpi_food` | float | FAO FFPI | Global food price index, base 2014-2016 = 100. |
| `ffpi_cereals` | float | FAO FFPI | Global cereals price index, base 2014-2016 = 100. |
| `ffpi_meat` | float | FAO FFPI | Global meat price index, base 2014-2016 = 100. |
| `ffpi_dairy` | float | FAO FFPI | Global dairy price index, base 2014-2016 = 100. |
| `ffpi_oils` | float | FAO FFPI | Global vegetable oils price index, base 2014-2016 = 100. |
| `ffpi_sugar` | float | FAO FFPI | Global sugar price index, base 2014-2016 = 100. |
| `ghi_2025` | float | Global Hunger Index | Hunger severity score in 2025. |
| `food_import_pct` | float | World Bank | Food imports as percentage of merchandise imports. |
| `ghi_norm` | float | Derived | Min-max scaled GHI score used in exposure index. |
| `import_dependency_norm` | float | Derived | Min-max scaled food import dependency used in exposure index. |
| `exposure_index` | float | Derived | Weighted hunger-import exposure index, 0-100 scale. |
| `implied_import_cost_pressure_pct` | float | Derived | Illustrative scenario pressure based on shock and pass-through. |
| `scenario_pressure_score` | float | Derived | Exposure-weighted scenario ranking metric. |

## Methodology

### Exposure Index

```text
ghi_norm = min-max scaled GHI 2025 score
import_norm = min-max scaled latest food imports as % of merchandise imports

exposure_index = (0.60 x ghi_norm + 0.40 x import_norm) x 100
```

Hunger receives the higher default weight because it is the direct human-centred risk. Food import dependency is treated as an exposure pathway. Scaling prevents either metric from dominating only because of its numeric range.

### What-If Scenario

```text
global_price_pressure = producer_price_shock x basket_share x transmission_coeff x pass_through_rate
implied_import_cost_pressure = food_import_pct x global_price_pressure / 100
scenario_pressure_score = exposure_index x implied_import_cost_pressure / 100
```

The scenario is illustrative. It helps rank monitoring priorities under alternative assumptions; it does not estimate exact import bills or forecast national food-security outcomes.

## Design System

- Streamlit theme: `.streamlit/config.toml`.
- Shared palette and assumptions: `app/config.py`.
- Chart and callout helpers: `app/style.py`.
- Visual approach: high-contrast charts, restrained colour use, consistent margins, clear hover tooltips, and compact policy-facing copy.

## Code Organisation

- `app/main.py`: Streamlit entry point.
- `app/data.py`: cached loading and type handling for processed CSVs.
- `app/analysis.py`: exposure index, scenario model, correlation logic, and sensitivity analysis.
- `app/controls.py`: sidebar controls and shared app state.
- `app/tabs/`: one renderer per dashboard tab.
- `app/style.py`: reusable Plotly and Streamlit presentation helpers.
- `notebooks/`: data preparation and exploratory analysis.

## Limitations

- No bilateral trade-flow data is included, so direct import dependence on Australia or New Zealand is not claimed.
- Producer prices are not import prices.
- Exchange rates, freight costs, tariffs, subsidies, margins, and substitution are not modelled.
- GHI is a slower-moving hunger measure and may not capture sudden crisis changes.
- Food import dependency may include non-staple or higher-value food categories.

## Credits

Data sources:

- FAOSTAT Producer Prices.
- FAO Food Price Index.
- Global Hunger Index.
- World Bank food import dependency indicator.

Implementation:

- Streamlit for the interactive application.
- Plotly for interactive visualisation.
- Pandas for data transformation and analysis.
- GitHub for version control and portfolio delivery.
