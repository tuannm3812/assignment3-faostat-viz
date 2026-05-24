# Part 3 Final Portfolio Plan

## Required Deliverables

- Hosted Streamlit dashboard.
- GitHub repository with organised code, data, notebooks, and documentation.
- 3-minute video walkthrough.
- Technical documentation, data dictionary, methodology, limitations, and credits.

## Live Dashboard

URL: https://assignment3-faostat-viz.streamlit.app/

Design system:

- Streamlit theme defined in `.streamlit/config.toml`.
- Modern policy palette in `app/main.py`: ocean teal, clear blue, amber, rose, navy, and slate.
- Plotly charts use a shared `plotly_white` template and common chart styling helper.

Main views:

The main canvas uses tabs for the narrative flow. The sidebar is reserved for global filters and model assumptions.

- `Executive Brief`
- `1. Shock Context`
- `2. Producer Signal`
- `3. Vulnerability`
- `4. What-If Action`
- `5. Evidence Base`

## Advanced Features

### Context-Aware Filtering

Implemented through sidebar controls for year range, FFPI series, commodity, producer country, exposure weights, scenario assumptions, evidence dataset, and volatility country. Controls update the tabs where they are analytically relevant, preserving one coherent dashboard layout without implying unsupported relationships.

### Visual Tooltips

Implemented through Plotly hover tooltips across line charts, scatter plots, and bar charts. Tooltips expose data quality flags, GHI, food import dependency, exposure index, and scenario pressure.

### What-If Parameterization

Implemented through:

- producer price shock slider,
- relevant import basket share slider,
- transmission coefficient slider,
- producer-to-import pass-through slider,
- food-access/import-dependency weight slider,
- scenario pressure ranking.

### Sensitivity Analysis

Implemented through the `3. Vulnerability` tab. The sensitivity table and bar chart show which countries remain in the top-10 exposure group when the food-access stress weight changes from 0.40 to 0.80.

### Narrative Flow

The tabs follow the project story:

1. What is the policy decision and priority watchlist?
2. What global food-price shocks provide the context?
3. What producer-price signal is visible in Australia and New Zealand?
4. Which countries are structurally exposed through hunger and import dependency?
5. What happens under alternative shock and pass-through assumptions?

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
global_price_pressure = producer_price_shock x basket_share x transmission_coeff x pass_through_rate
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

Detailed transcript: [Part 3 Video Walkthrough Transcript](part3_video_transcript.md)

1. Open the app and explain the stakeholder and question.
2. Show `Executive Brief` and the policy watchlist.
3. Show `1. Shock Context`, including FFPI crisis markers.
4. Show `2. Producer Signal`, including AUS/NZ producer-price alignment with FFPI.
5. Show `3. Vulnerability` and `4. What-If Action`, explaining the exposure formula, sensitivity analysis, and scenario sliders.
6. Open `5. Evidence Base` or the code briefly to show data organisation.
7. Close with limitations and call to action.

## Part 3 Compliance Checklist

- **Hosted dashboard:** Streamlit Cloud URL included above.
- **Consistent design system:** `.streamlit/config.toml` plus shared colour constants and chart styling in `app/main.py`.
- **Responsive load times:** Dashboard reads cleaned local CSV files from `data/processed/` and caches loading with `st.cache_data`.
- **Advanced features:** context-aware sidebar filters, Plotly hover tooltips, guided tab narrative, what-if parameterisation, adjustable exposure weighting, and sensitivity analysis.
- **Technical documentation:** data dictionary, methodology, limitations, and credits are documented in this file and the README.
- **Code organisation:** Streamlit implementation is in `app/main.py`; data preparation notebooks and API helper are separated under `notebooks/` and `src/data_pipeline/`.
