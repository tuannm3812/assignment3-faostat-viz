# Showcase: charts, slides and poster

The food-price story in three parts, drawn in the UTS deck kit style (palette A for structure, Viridis for data,
Google Sans). Every number on every output is computed from `data/processed/` and written to
`output/findings.json`; slide and poster copy is saved to `output/copy.json`.

| Output | What it is |
| --- | --- |
| `output/slides/slides.pdf`, `slide-1..20.png` | Eighteen 16:9 slides (960 × 540 pt, PNG 1920 × 1080): cover, agenda, summary, question, data and method; shock, anatomy, drivers; exposure, hunger trend, Australia and NZ farm prices; how the rule works, signal chart, back-test, today; roadmap, limits, appendix |
| `output/01-shock.png`, `02-exposure.png`, `03-warning.png` | Hero images for the portfolio and LinkedIn (copies of slides 6, 9 and 13) |
| `output/poster/poster-landscape.pdf`, `.png` | A1 landscape poster (PNG 6000 px wide) |

| Part | Headline (computed) |
| --- | --- |
| The shock | Three food-price spikes since 2007, each peak higher than the last (132.7, 137.7, 160.2) |
| The exposure | 20 of 91 countries pair serious hunger with high food-import reliance |
| The warning | Oils and cereals rose 20% before every food-price shock since 2000 (4 of 5 signals followed by a shock) |

## Rebuild

From the repository root (needs Node with Playwright and Chromium for the PDF and PNG step):

```bash
python showcase/build_showcase.py
```

`build_hero_charts.py` holds the calculations and chart drawing; `build_showcase.py` lays out the slides and
poster; `render.mjs` exports them.

## Colours (one meaning each, everywhere)

| Colour | Meaning |
| --- | --- |
| `#3B528B` | All-food price index |
| `#21918C` | Vegetable oils |
| `#35B779` | Cereals |
| Pale `#FDE725` band | Shock months |
| `#440154` | Exposed country |
| `#B9C2CA` | Other countries |
| `#1B2430` box | Signal |

Chapter accents (blue for the shock, plum for the exposure, ochre for the warning) mark structure only: header
rules, the tracker and card top rules.

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

Fonts: Google Sans v14.000 (SIL Open Font License, `fonts/OFL.txt`), from the official googlefonts release.

Layout follows the Text-to-SQL showcase built with the same kit: split cover with a data motif, chapter tracker
and UTS logo, finding titles, figure on the left with a takeaway and numbered notes on the right, and an A1 poster
with an answer band, three section rows and a closing call to action with a QR code to the live dashboard.
The UTS mark is the unchanged file from the deck kit (`assets/uts-logo.svg`); UTS owns it.
