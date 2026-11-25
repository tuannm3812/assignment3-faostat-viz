# Showcase charts

Three hero charts for decks, posters and the portfolio. Each covers one part of the story:

| Chart | Part | Headline (computed) |
| --- | --- | --- |
| `output/01-shock.png` | The shock | Food prices have spiked three times since 2007, each peak higher than the last |
| `output/02-exposure.png` | The exposure | 20 of 91 countries pair serious hunger with high food-import dependence |
| `output/03-warning.png` | The warning | Each food-price shock since 2000 followed a 20% jump in oils and cereals |

Rebuild from the repository root:

```bash
python showcase/build_hero_charts.py
```

Every number on a chart is written to `output/findings.json` by the same run.

## Definitions

- **Shock month:** the all-food FAO Food Price Index is more than 20% above the same month a year earlier.
- **Signal:** vegetable oils and cereals are both more than 20% above a year earlier, outside a shock.
- **Exposed country:** Global Hunger Index 2025 of 20 or more ("serious"), and food imports above the median share of
  merchandise imports (World Bank, latest year 2015 or later).

## Caveats

- The signal rule was read off the 2000-2026 history, so it is a watch signal, not a tested forecast. Machine-learning
  classifiers trained on pre-2013 data alone missed most of the 2020-21 run-up, so this simple rule is the stronger
  result here.
- Import shares come from different years per country (2015 to 2024).

Fonts: Google Sans if installed, else Google Sans Flex. Set `FONT_DIR` to a folder of `.ttf` files to register fonts.
