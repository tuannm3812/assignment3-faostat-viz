# Part 3 Final Portfolio Plan

## Required Deliverables

- Hosted Streamlit dashboard.
- GitHub repository with organised code, data, notebooks, and documentation.
- 3-minute video walkthrough.
- Technical documentation, data dictionary, methodology, limitations, and credits.

## Live Dashboard

URL: https://assignment3-faostat-viz.streamlit.app/

Main views:

- `Overview`
- `Price Trends`
- `Volatility`
- `Global Context`
- `Exposure Matrix`
- `Live FAOSTAT`
- `Data Explorer`

## Advanced Features

### Context-Aware Filtering

Implemented through commodity and country controls in `Price Trends`, FFPI index selection in `Global Context`, and country selection in `Exposure Matrix`.

### Visual Tooltips

Implemented through Plotly hover tooltips across line charts, scatter plots, and bar charts. Tooltips expose data quality flags, GHI, food import dependency, exposure index, and scenario pressure.

### What-If Parameterization

Implemented through:

- producer price shock slider,
- producer-to-import pass-through slider,
- scenario pressure ranking.

### Narrative Flow

The sidebar pages follow the project story:

1. What is changing in producer prices?
2. How does this relate to global food price shocks?
3. Who is structurally exposed?
4. What happens under alternative shock assumptions?

## Data Dictionary

| Field | Type | Source | Description |
|---|---|---|---|
| `country` | string | FAOSTAT | Producer-price country, Australia or New Zealand. |
| `iso3` | string | Derived/source | ISO 3166-1 alpha-3 country code. |
| `item` | string | FAOSTAT | Commodity name. |
| `year` | integer | FAOSTAT/FFPI/World Bank | Observation year. |
| `value` | float | FAOSTAT | Producer price or producer price index value depending on file. |
| `unit` | string | FAOSTAT | Unit such as USD/tonne, LCU/tonne, or index. |
| `is_imputed` | boolean | Derived | True for FAOSTAT estimated or internationally sourced records. |
| `is_outlier` | boolean | Derived | IQR-based outlier flag within country-commodity group. |
| `ffpi_food` | float | FAO FFPI | Global food price index, base 2014-2016 = 100. |
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

Rationale:

- Hunger receives more weight because it is the direct human-centered risk.
- Food import dependency is an exposure pathway, not proof of food insecurity by itself.
- Scaling prevents one metric from dominating only because of its numeric range.

### What-If Scenario

```text
global_price_pressure = producer_price_shock x pass_through_rate
implied_import_cost_pressure = food_import_pct x global_price_pressure / 100
scenario_pressure_score = exposure_index x implied_import_cost_pressure / 100
```

The scenario is illustrative. It is not a causal forecast.

## Limitations

- No bilateral trade-flow data is included, so the dashboard does not prove direct import dependence on Australia or New Zealand.
- Producer prices are not import prices.
- Exchange rates, freight costs, tariffs, subsidies, margins, and substitution are not modelled.
- GHI is a slower-moving hunger measure and may not capture sudden short-term crisis changes.
- Food import dependency can include non-staple or higher-value food categories.

## Credits

Data sources:

- FAOSTAT Producer Prices.
- FAO Food Price Index.
- Global Hunger Index.
- World Bank food import dependency indicator.

Repository and implementation:

- Streamlit dashboard in `app/main.py`.
- Data preparation notebooks in `notebooks/`.
- API helper in `src/data_pipeline/faostat_client.py`.

## Video Walkthrough Script

1. Open the app and explain the stakeholder and question.
2. Show `Price Trends` and crisis bands.
3. Show `Global Context`, including FFPI correlations and crisis markers.
4. Show `Exposure Matrix`, explain the corrected formula and pass-through slider.
5. Open `Data Explorer` or the code briefly to show data organisation.
6. Close with limitations and call to action.
