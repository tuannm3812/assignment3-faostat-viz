# Part 3 Video Walkthrough Transcript

Target length: approximately 3 minutes.

Presenter goal: show the live Streamlit dashboard, briefly explain the code/data organisation, and explicitly highlight at least three advanced features.

## Before Recording

- Open the live dashboard or local Streamlit app.
- Open the repository in a second tab or IDE window, ready to show `app/main.py`, `data/processed/`, `.streamlit/config.toml`, and `README.md`.
- Keep the browser zoom around 90-100% so the sidebar and charts fit on screen.
- Start on the `Executive Brief` tab.

## Transcript

### 0:00-0:20 - Opening and Stakeholder

Hello, this is our Part 3 final portfolio walkthrough for the FAOSTAT Food Price Shock Visualisation project.

Our stakeholder is a UN Food Systems Summit Panel or a regional food-security policy board. The decision problem is: when global food prices and Australia or New Zealand producer prices rise, which countries should be prioritised for food-security monitoring and preparedness?

This is not designed as a general status dashboard. It is a guided data narrative that moves from price shocks, to producer signals, to human vulnerability, and finally to policy action.

### 0:20-0:45 - Executive Brief

The dashboard now uses a professional layout: the sidebar is the control panel, and the main canvas uses tabs for the story. On the `Executive Brief` tab, we summarise the dashboard in decision-maker language. The top metrics show the producer-price coverage, number of commodities, latest FAO Food Price Index value, and the highest exposure country in the current model.

The policy watchlist translates the analysis into action categories such as preparedness package, import-buffer monitoring, or watchlist. This first page is intentionally concise so a policy audience can understand the main recommendation before exploring the detailed evidence.

### 0:45-1:10 - Data and Design System

The dashboard is built in Streamlit using `app/main.py`. It reads cleaned CSV files from `data/processed`, including FAOSTAT producer prices, FAO Food Price Index data, Global Hunger Index data, and World Bank food import dependency data.

For technical polish, the dashboard uses a consistent design system. The Streamlit theme is defined in `.streamlit/config.toml`, and the Plotly colours and shared chart styling are defined in `app/main.py`. This keeps the dashboard visually consistent across pages.

The data loading functions use Streamlit caching, so the app reads local processed files efficiently and keeps load times responsive.

### 1:10-1:40 - Advanced Feature 1: Context-Aware Filtering

The first advanced feature is context-aware filtering.

In the sidebar, the user can select which FAO Food Price Index series to display, such as food, cereals, oils, meat, dairy, or sugar. The year-range slider updates the `1. Shock Context` tab, including the chart and the crisis-year markers.

This lets a policy viewer focus on a specific food category or time period without leaving the narrative flow. It also reduces cognitive load because the same chart can answer several related questions.

### 1:40-2:05 - Producer Signal and Tooltips

On `2. Producer Signal`, we connect the global food-price story to Australia and New Zealand producer-price data. Wheat is used as the default signal because it is a globally traded staple, appears in the AUS/NZ producer-price data, and gives a clear bridge between producer prices and food-security risk. The commodity selector still lets the viewer test other producer-price signals.

This page also demonstrates the second advanced feature: visual tooltips. The Plotly charts reveal deeper information on hover, including year, country, producer price, FFPI value, and data flags where relevant. The viewer can inspect details without cluttering the chart with too much text.

### 2:05-2:35 - Advanced Feature 3: Adjustable Exposure Weighting

On `3. Vulnerability`, the dashboard combines food-access stress and food-import dependency into a hunger-import exposure view.

The exposure index uses a weighted formula:

`exposure_index = food-access weight x normalised food-access stress + import weight x normalised food import dependency`

The sidebar slider lets the user adjust the food-access stress weight. The import-dependency weight automatically updates to one minus that value, so the two weights always sum to 1. This makes the model transparent and allows sensitivity testing.

The scatter plot shows which countries combine higher hunger stress with higher import dependency, and the policy watchlist updates with the current assumptions. We also added a lightweight sensitivity analysis showing which countries remain in the top priority group when the food-access weight changes from 0.40 to 0.80. This helps separate robust priorities from countries that only appear under one weighting assumption.

### 2:35-2:55 - Advanced Feature 4: What-If Parameterisation

On `4. What-If Action`, the dashboard turns the exposure model into a scenario tool.

In the sidebar, the user can adjust the producer-price shock, relevant import basket share, transmission coefficient, and producer-to-import pass-through. These controls estimate effective global pressure and update the priority ranking.

This is not a causal forecast. It is a transparent prioritisation model for early-warning discussion.

### 2:55-3:15 - Evidence Base and Close

Finally, `5. Evidence Base` provides transparency. It includes the source tables and commodity volatility checks, so the audience can inspect the cleaned data behind the visuals.

The main limitation is that we do not include bilateral trade-flow data, so the dashboard does not prove that specific countries import directly from Australia or New Zealand. Producer prices are also not the same as import prices.

Our final recommendation is to use hunger-import exposure as an early-warning layer. When producer-price signals and global food-price indicators rise together, food-security teams should prioritise countries that combine high food-access stress with high import dependency.

## Shorter Version If Needed

Hello, this is our final portfolio walkthrough for the FAOSTAT Food Price Shock Visualisation project. Our stakeholder is a UN or regional food-security policy board. The dashboard asks: when global food prices and Australia or New Zealand producer prices rise, which countries should be prioritised for monitoring and preparedness?

The dashboard is built in Streamlit in `app/main.py`, using cleaned data from `data/processed`. It joins FAOSTAT producer prices, FAO Food Price Index data, Global Hunger Index data, and World Bank food import dependency. The design system is defined through `.streamlit/config.toml` and shared Plotly styling in the code.

The first advanced feature is context-aware filtering. The sidebar controls food-price indices, year range, commodity, country, model weights, and scenario assumptions, and those controls update the tabs. The second advanced feature is Plotly tooltips, which reveal country, year, price, exposure, and data-quality details without overcrowding the visuals. The third advanced feature is what-if parameterisation. On `4. What-If Action`, users can adjust producer shock, basket share, transmission, and pass-through to update the priority ranking. We also added adjustable exposure weighting and sensitivity analysis on `3. Vulnerability`, where the food-access and import-dependency weights always sum to 1.

The key limitation is that this is not a bilateral trade-flow model or causal forecast. It is an early-warning and prioritisation tool. Our recommendation is to monitor countries where food-access stress and food-import dependency are both high when global food-price signals rise.
