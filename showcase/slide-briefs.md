# Slide briefs: Food Price Shock Early Warning

**Subject:** 36104 Data Visualisation and Narratives, UTS
**Author:** Manh Tuan (Mike) Nguyen
**Audience:** a UN food-systems panel or a regional food-security policy board

**The question:** When global food prices spike, which countries feel it first, and can we see it coming?

**The answer:** Watch vegetable oils and cereals. When both are more than 20% above a year earlier, prepare the 20 exposed countries first.

**Rule for numbers:** every number comes from `showcase/output/findings.json`, which `build_hero_charts.py` writes from `data/processed/`. Change a number there, never in the slide text.

**Rule for layout:** each slide has two parts.
- A canvas on the left holds the chart and red numbered markers placed on the evidence.
- A takeaway column on the right is split from the canvas by a hairline. It holds a takeaway box and notes whose numbers match the markers.
- Tables and charts never go in the takeaway column.

---

## Opening

### 1. Cover
- **Title:** Watch two prices. Protect twenty countries.
- **Subtitle:** An early-warning story from 36 years of FAO food prices, hunger and trade data.
- **Label:** 36104 Data Visualisation and Narratives
- **Byline:** Manh Tuan (Mike) Nguyen · University of Technology Sydney · November 2026
- **Visual:** a real photo of food distribution or a grain market on the right half. The illustrative shape sits bottom left: a strip of annual price pills, ochre in shock years.

### 2. Agenda
Four chapters, each with an icon and its slide names with page numbers:
- **The shock:** 6–8
- **The exposure:** 9–11
- **The warning:** 12–15
- **Next:** 16–17

The appendix is not listed.

### 3. Summary
- **Title:** Food-price shocks are growing, and two prices warn of them early
- **Cards:** three cards, each with a numbered circle (1–3), a headline number, a richer mini chart and two stats.
  1. **Shock:** 160.2 record (Mar 2022). Mini chart: annual index as an area chart with peaks labelled.
  2. **Exposure:** 20 of 91 countries. Mini chart: a dot grid with 20 filled.
  3. **Warning:** 4 of 5 signals. Mini chart: a timeline of signals with lead arrows.
- **Takeaway:** No signal in Mar 2026: oils +13%, cereals +1%. Watch both monthly.

### 4. The question
- **Title:** A food-security board needs to know when to act, and where
- **Visual:** a big photo on the left; the question in a dark box.
- **Three needs, each tied to a chapter:**
  - When will prices spike? (warning)
  - Where will it hurt most? (exposure)
  - How big can it get? (shock)
- **Also:** who the audience is and what they decide.

### 5. Data and method
- **Title:** Four public datasets, joined by country, give three simple measures
- **Sources, with their logos:**
  - FAO Food Price Index: 435 months, Jan 1990 to Mar 2026
  - Global Hunger Index 2025: 98 countries
  - World Bank food imports: latest year 2015–2024
  - FAOSTAT producer prices: Australia and New Zealand, 118 products, 1991–2025
- **Prepare:** join by ISO3 code, year-on-year change, drop outliers, keep import shares from 2015.
- **Measures:**
  - Shock month: all-food index more than 20% above a year earlier.
  - Exposed country: GHI 20+ and food imports above the 16.3% median.
  - Two-price signal: oils and cereals both 20%+.
- **Outputs:** the Streamlit dashboard, the Looker dashboard, this deck and poster, and findings.json.

---

## Chapter 1: The shock

### 6. Global food prices
- **Title:** Three food-price spikes since 2007, each peak higher than the last
- **Canvas:** monthly all-food index, 1990–2026, with shock months shaded. Annotations on the chart:
  - the fastest rise, +63% on a year earlier in Mar 2008
  - the three peaks: 132.7, 137.7 and 160.2
  - today's level, 128.5
  - the 2014–16 base of 100
- **Markers:**
  1. 2007–08 crisis: peak 132.7 (Jun 2008); oils rose 109%.
  2. 2010–11 spike: peak 137.7 (Feb 2011); cereals rose 68%.
  3. 2021–22 surge and the war in Ukraine: record 160.2 (Mar 2022).
  4. Two one-month blips (Jul 1995, Apr 2004), shaded but not counted as major shocks.
- **Takeaway:** Each shock lasted a year or more, and each peak was higher than the one before.

### 7. Anatomy of a shock
- **Title:** Prices fell after each peak, but only once came back to where the shock began
- **Canvas:** three small panels with the index around each shock against its level a year before. Each panel carries a strip below:
  - Rise: +86% / +48% / +68%
  - Months in shock: 16 / 12 / 16
  - Back to that level: Never / 54 months / Not yet
- **Markers:**
  1. 2008 floor of 71 never seen again.
  2. 2010–11 fastest climb, 5 months to peak.
  3. 2022 still 33 points above its start.
- **Takeaway:** Each shock resets the floor.

### 8. What drove each shock
- **Title:** Vegetable oils led two of the three shocks; meat never rose more than 28%
- **Canvas:** heat table with a food-group icon in each header, the leading cell outlined, and markers on the cells.
- **Markers:**
  1. Oils (+109%, +125%)
  2. Cereals (+68% in 2010–11)
  3. Dairy and sugar spiked once each; meat stayed calm.
- **Takeaway:** In every shock either oils or cereals rose most, which is why the warning watches those two.

---

## Chapter 2: The exposure

### 9. Who feels it first
- **Title:** 20 of 91 countries pair serious hunger with high food-import reliance
- **Canvas:** scatter plot, with markers on Madagascar (highest hunger), on Guinea-Bissau (highest imports, 41.7%) and on DR Congo (hungry but imports little).
- **Notes:**
  1. Madagascar 35.8 and Haiti 35.7 lead the list.
  2. Guinea-Bissau buys 41.7% of its imports as food.
  3. DR Congo, Nigeria and Angola: serious hunger, low imports.
- **Takeaway:** These 20 countries are where to prepare first.

### 10. Is it getting worse?
- **Title:** 6 of the 20 exposed countries are hungrier than in 2016, Haiti most of all
- **Canvas:** country rows with flags, grouped by region:
  - Sub-Saharan Africa: 15
  - Asia and Pacific: 4
  - Americas: 1
- **Each row:** GHI 2016 to 2025 dumbbell, change, and an inline bar for food-import share.
- **Markers:**
  1. Haiti +5.8 (29.9 to 35.7)
  2. Kenya +2.8 and Benin +2.1
  3. Mozambique −10.5, the largest fall
- **Takeaway:** A third of the list is moving the wrong way, so it needs a yearly refresh.

### 11. The exporters' view
- **Title:** Australian and New Zealand farm prices barely felt the world spikes
- **Canvas:** the world index against Australian and NZ farm-price indices, 1991–2025, with a flag or globe on each line label. Annotated gaps for 2008 and 2022. A comparison bar row below the chart:
  - 2008: World +24.5%, Australia +7.7%, NZ +2.9%
  - 2022: World +14.9%, Australia +4.1%, NZ +0.4%
- **Markers:**
  1. 2008 gap
  2. 2022 gap
  3. Steady climb since 2014, from 94 to 121 in Australia
  4. Weak year-to-year link (r = 0.28 and 0.34)
- **Takeaway:** Big exporters are buffered; a world spike lands on countries that import their food.

---

## Chapter 3: The warning

### 12. How the rule works
- **Title:** The warning needs two numbers a month and one line at +20%
- **Visual:** three steps, each with a mini chart.
  1. Two price lines against the +20% line.
  2. A gate where both must pass.
  3. A timeline from signal to shock, with a 1–5 month window.
- **Worked example:** Dec 2006: oils +31%, cereals +39%; the shock began 5 months later, in May 2007.

### 13. An early signal
- **Title:** Oils and cereals rose 20% before every food-price shock since 2000
- **Canvas:** year-on-year chart and signal strip, with markers on the signals and on the 2002 false alarm.
- **Takeaway:** No signal now: oils +13% and cereals +1% (Mar 2026).

### 14. Back-test
- **Title:** Every shock since 2000 had a signal first; one signal had no shock
- **KPIs:**
  - 4 of 5 signals followed by a shock
  - 1–5 months of warning
  - 0 of 4 shocks missed
- **Table:** inline bars next to the oils and cereals numbers, with the +20% line drawn in each bar. Lead shown as a bar.
- **Markers:**
  1. Lead times are short.
  2. The 2002 false alarm.
  3. The April 2004 shock lasted a single month.

### 15. Where we are now
- **Title:** No signal in Mar 2026, but vegetable oils are already at 183
- **Canvas:** diverging bars for each group's change on a year earlier, against the +20% line.
- **Markers:**
  1. Oils are highest at 183.1.
  2. What would trigger the signal: oils above 194 and cereals above 132, at today's year-ago levels.
  3. All food 128.5.

---

## Chapter 4: Next

### 16. Roadmap
Four steps, each with a trigger and an owner:
- **Monitor:** every month
- **Prepare:** when the signal fires
- **Review:** every year
- **Test:** before relying on it

### 17. Limits and the dashboard
- **Limits:**
  - The rule is in-sample.
  - The data are snapshots.
  - World prices are not shop prices.
- **Dashboard:** QR code to the live dashboard.

---

## Appendix (after the closing slide; not in the agenda)

### A1. Definitions
Covers only the important terms:
- shock month
- two-price signal
- exposed country
- GHI bands
- food-import share
- farm-gate index

### A2. Sources and image credits
Data sources, plus the photo and logo credits with their licences.
