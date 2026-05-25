# Delivery Quality Checklist

This checklist keeps the final submission aligned with the stakeholder narrative, technical requirements, and modelling limitations.

## Stakeholder Alignment

- The dashboard is framed for a UN food-systems panel or regional food-security policy board.
- The core decision question is clear: which countries should be prioritised for monitoring and preparedness when food-price pressure rises?
- The language uses "hunger-import exposure" and "structural exposure to global food-price pressure".
- The dashboard does not claim direct bilateral dependence on Australia or New Zealand.

## Analytical Integrity

- The exposure index is explained as a normalised weighted index, not a raw multiplication.
- The default weights are transparent: 60% hunger severity and 40% food import dependency.
- Scenario outputs are presented as prioritisation signals, not forecasts.
- The limitations section clearly covers missing bilateral trade data, price pass-through uncertainty, exchange rates, freight costs, and substitution.

## Dashboard Quality

- The sidebar acts as the global control panel for filters and model assumptions.
- The tabs follow the narrative sequence: Executive Brief, Shock Context, Producer Signal, Vulnerability, What-If Action, Evidence Base.
- Charts load cleanly without missing-data warnings.
- Hover tooltips expose useful details without crowding the page.
- The sensitivity analysis shows whether priority countries remain stable under alternative weights.
- The deployed Streamlit app is checked after each major push.

## Documentation Quality

- README includes the live app link, decision context, data sources, methodology, setup steps, limitations, and documentation links.
- Final portfolio documentation includes the data dictionary, advanced features, design system, credits, and code organisation.
- Video transcript focuses on technical delivery: Streamlit structure, cached data loading, modular code, advanced features, and evidence transparency.
- Archived Part 2 materials remain separate from the final Part 3 portfolio narrative.
