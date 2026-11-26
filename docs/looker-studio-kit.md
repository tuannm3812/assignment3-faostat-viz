# Looker Studio Kit

Manh Tuan (Mike) Nguyen · 27 Nov 2026 · Live version: [Looker Studio Kit](https://claude.ai/artifact/HpMqEKmQTtVEUWhXT4euzR)

One layout, one set of colours and one way of writing titles for every Looker Studio report Mike builds: the UTS 36104 food price dashboard first, then the UNSW hackathon report. Every rule here was tested on the food price dashboard on 26 Nov 2026.

## How to use this kit

1. **Write the questions first.** One tab per question the reader asks (for example: what happened, who is exposed, is it coming again). The first tab is an overview.
2. **Mock it before building.** Draw each tab at the real canvas size with real numbers and get it approved. Building in Looker is slow; changing a mock is fast.
3. **Prepare the data in Google Sheets** (one sheet per chart grain, see Data prep).
4. **Build to the grid** in this kit, using the card, chart and table recipes.
5. **Run the QA checklist** in view mode before sharing.

## Canvas and grid

Use a landscape canvas of **1600 × 690 px**, display mode *Fit to width*, with tab navigation. 690 px is the tallest canvas that shows without scrolling in a 2560 × 1262 Chrome window, so nothing important is ever below the fold.

| Zone | Left (px) | Top (px) | Width (px) | Height (px) | Holds |
| --- | --- | --- | --- | --- | --- |
| Header band | 0 | 0 | 1600 | 60 | Report title left, author name right (report-level, so every tab shares it) |
| Left rail | 24 | 72 | 256 | 608 | Filters, how-it-works bullets, sources (report-level) |
| Card row | 296 | 72 | 1284 | 98 | 3 to 5 headline cards |
| Main area | 296 | 184 | 1284 | 496 | One main chart, or a chart + table side by side |

- **Gaps are 16 px** between everything (rail to content, card to card, row to row). Content always ends at x 1580 and y 680.
- **Cards across 1284 px:** 4 cards = widths 314, 304, 314, 304 at lefts 296, 626, 946, 1276. 3 cards = about 415 each.
- **Grid snap is 10 px** and you can't switch it off. Right and bottom edges land on multiples of 10, so plan sizes that end on 10s (1580, 680, 490) and use shift + arrow for 1 px nudges of the left/top.
- **Main area splits:** full width (1284 × 496); chart 704 + table 564; or a chart 286 tall with a 196 tall table under it.

## Left rail

The rail answers "what am I looking at and how do I change it", in three blocks, top to bottom. Make every rail element report-level so it stays put across tabs.

1. **FILTERS** (small caps heading, 20 px line icon at the right edge): drop-down controls 238 × 50, 7 px apart. Name them in plain words (Food group, Country), not field names.
2. **HOW IT WORKS** (small caps heading + icon): the rule as 3 bullets, one line idea each. Each bullet starts with a coloured dot (●) in the colour of what it describes. Bold the key terms and colour the series names the way the charts colour them (for example **vegetable oils** in teal, **cereals** in green, **20%+** in bold ink).
3. **SOURCES** (small caps heading + icon): one short paragraph in grey, 12 px: dataset, unit, coverage dates.

Don't add a "How to read" box. Each chart carries its own legend and finding title, so a separate key repeats them.

## Headline cards

A card is a Scorecard: a small caps label, one big number, and (on the overview) one grey line of context. Height 98 px, label 14 px caps, number about 36 px. Cards on chapter tabs are smaller than on the overview: one number, no icon.

- **Label says what and when:** VEGETABLE OILS NOW, BIGGEST JUMP ON A YEAR EARLIER, HUNGRIER THAN IN 2016. Rename the metric in the field editor; keep labels under about 30 characters so they don't cut off.
- **Arrows come from the number format,** not from icons. Field editor → Display format → Custom number format, then Apply.
- **Colour carries meaning:** use conditional formatting (Style → Add formatting) so the colour follows the data, and a fixed font colour only when the meaning never changes.

| Card shows | Custom number format | Colour rule |
| --- | --- | --- |
| A change in % | `'▲ +'0.0'%';'▼ -'0.0'%'` | Greater than 0 → red; less than 0 → green |
| A change in points | `'▲ '0.0;'▼ '0.0` | Same as above |
| A count that is bad news | `'▲ '0` | Fixed red |
| An on/off state (text) | none | Equal to "On" → red; equal to "Off" → green |
| A count of warning months | none | Fixed amber |
| A neutral level (peak, average) | none | Ink (default) |

Red ▲ always means worse (prices or hunger up); green ▼ means better. If a rise is good news in another project, flip the colours, not the arrows.

## Colour and type

Colour is a role, not decoration: each colour means one thing across every tab. Add these hexes as custom colours once (any colour picker → +) so they sit in the Custom swatch row.

| Role | Hex | Used for |
| --- | --- | --- |
| Ink | #1F2937 | Numbers, titles, body text |
| Header band | #1F2633 | The 60 px header (white text) |
| Muted grey | #5F6B7A | Context lines, sources, axis labels |
| Context grey | #B9C2CA | "Other" points, secondary bars, minor series |
| Main series | #3B528B | The headline series (for example All food) |
| Worse / alert | #B03A2E | ▲ rises, signal on, shocks that followed |
| Better / safe | #2E8B57 | ▼ falls, signal off |
| Warning / watch | #B88300 (bars #E0A800, shading #FCE8A8) | Warning months, shaded shock periods |
| Focus group | #440154 | The group the story is about (exposed countries) |
| Series pair | teal #1F9E89 + green #35B779 | Two series compared (vegetable oils, cereals) |

Type: **Google Sans Flex** everywhere. Title 26 px bold in the header; chart titles 14 px; card labels 14 px caps; card numbers 36 px; tables 12 px body and header; rail text 13 px; sources 12 px grey.

## Charts

Each tab has **one main chart** that answers its question. Add a second chart only if it shows something new.

- **The title states the finding,** with its number: "Food prices since 1990: three big spikes, in 2008, 2011 and 2022", not "Price index over time". Put units and definitions after a colon or in brackets.
- **Legend on one line under the title,** top left. Hide legends that repeat the title.
- **Highlight, don't rainbow.** The series the story is about gets its role colour and a thicker line; everything else is context grey. Empty years stay empty so the spikes stand out on their own.
- **Shade periods** (shocks, signal-on months) with a combo chart: a 0/1 metric drawn as bars in light amber behind the line, axis hidden. Draw thresholds (20%, the 100 base, a median) as reference lines with a short label.
- **Date axes:** time series with Year Month granularity and fewer ticks so labels sit on one row; for yearly bars use a Year dimension so every label is just the year.
- **Maps:** a three-step scale that matches the meaning (low = pale, serious = amber, severe = red), not a single-hue ramp.
- **Scatter quadrants:** two reference lines (threshold and median) with labels, the focus group in its role colour, the rest grey.
- **Built-in charts can't do callouts with arrows.** If a chart needs annotations, put the finding in the title instead.

## Tables

A table is the place for a ranked list with several attributes per row. Keep it to what fits without paging where you can (5 rows in 196 px, 20 rows in 496 px).

- **Flags:** add a `flag_url` column to the sheet (for example `https://flagcdn.com/w40/<iso2>.png`), then in the data source add a calculated field `IMAGE(flag_url, country)`. Put it first, give it a blank header (the character U+3164; U+2800 shows as dots in Google Sans) and drag its column narrow.
- **Bars in cells:** Style → the metric → Show as Bar, with the number shown. Focus metric in its role colour, the second metric in context grey.
- **Change columns:** reuse the card arrow format and red/green conditional rules, applied to that column only (the rule's "apply to" selector).
- **Text outcomes:** a rule like "What followed NOT EQUAL TO No shock followed → red text" colours the real events and leaves the false alarm grey.
- **Rows:** turn row numbers off; header and body 12 px; Top N instead of pagination when every row fits, so the footer disappears.
- **Filter and sort in the chart:** a chart filter (for example Exposed only, exposed = 1) and an explicit sort (hunger score descending, or a date ascending for a timeline). The sort field doesn't have to be shown.
- **Column names in plain words:** rename each field in the chart (Hunger score, Food imports %, Since 2016, Shock came after).

## Tab patterns

| Tab | Cards (y 72) | Main area (y 184) | Food price example |
| --- | --- | --- | --- |
| Overview | 5 cards with icon badge and one context line | Big main chart (about 800 wide) + one supporting view (map) | Price index lines 1990–2026 + hunger map |
| Chapter: what happened | 3 cards | Full-width chart, then a small chart under it that isolates the events | Price index with shock months shaded + shock months per year bars |
| Chapter: who is affected | 4 cards | Chart 704 wide + ranked table 564 wide | Hunger × imports scatter + 20 exposed countries with flags |
| Chapter: what's next | 4 cards (state, two drivers, count) | Full-width chart 286 tall + track-record table 196 tall | Oils and cereals with signal months shaded + every signal since 2000 and what followed |

Keep definitions identical across tabs (the same 3 major shocks, the same 20% trigger, the same 20 exposed countries). A number that differs between tabs reads as an error.

## Data prep

Do the analysis in Python (or SQL) and hand Looker small, tidy Google Sheets, one per chart grain: monthly series, one row per country, one row per event, and a single-row sheet of headline numbers. Looker then only filters and draws.

- **Precompute flags as 0/1 columns** (shock\_month, signal\_month, exposed, is\_latest). They drive shading, card counts (SUM) and chart filters.
- **Sheets turns text like "Mar 2004" into a date.** Write period labels that can't parse ("Mar 2004 only", "Sep to Nov 2002") or prefix them with an apostrophe, and check the column type in the data source after adding it.
- **Calculated fields belong in the data source** (Data panel → Add a field → Add calculated field). Use them for IMAGE() flags, short labels (CASE country WHEN "Central African Republic" THEN "Central African Rep." ...) and label mapping.
- **Version the sheet builder in the repo** (for example `showcase/build_looker_*.py`) so numbers can be rebuilt and checked against the deck.

## Editor how-tos and quirks

| Task | How | Watch out for |
| --- | --- | --- |
| Select a chart | Click empty canvas first, then the chart's axis or title strip | Clicking a data point in edit mode cross-filters the whole page (cards show "No data"). Clear it with the chart's reset arrow or the chip's x in the filter bar. |
| Move exactly | Arrow key = 10 px, shift + arrow = 1 px | Check position in Arrange or the element's style box |
| Resize | Hover the bottom-right handle, then drag | Starting just off the handle draws a selection box instead; edges snap to 10 px |
| Rename a field in a chart | Click the pill's type icon → Display name | Field editor also holds Display format for arrows |
| Swap a field | Drag the new field onto the old pill | Often inserts beside it; remove the old pill with its x and drag pills to reorder |
| Conditional colour | Style → Add formatting → condition, value, font colour → Save and add another | For tables, set the "apply to" column, or it colours the whole row |
| Chart filter | Add filter → Create a filter → field, condition, value | Pick the value from the suggestion list, or Save stays greyed out |
| Blank column header | Display name = the character U+3164 (U+2800 renders as a dots glyph) | A normal space is rejected |
| Scroll the style panel | Mouse wheel over the panel | If it won't scroll, collapse sections you've finished |
| New data source | Add data → Google Sheets → spreadsheet → Add → Add to report | Each data source keeps its own calculated fields |

## QA checklist before sharing

First measure every box in edit mode (left, top, width, height of each element) and check the gaps and edges by number; then check every tab in **View** mode, at the browser size the audience will use, with all filters reset.

- [ ] Nothing overlaps, and every box ends at x 1580 and y 680
- [ ] Card tops, chart tops and gaps line up across tabs (72, 184, 16 px)
- [ ] No card label or column header is cut off
- [ ] Every chart title states a finding with a number
- [ ] Colours follow the roles table: red worse, green better, amber warning
- [ ] Arrows point the right way for both a rise and a fall (test with a date filter)
- [ ] Headline numbers match the deck and the notebook
- [ ] The same definition gives the same number on every tab
- [ ] Tables show every row without paging, or say "1–20 / 20"
- [ ] Date labels sit on one row
- [ ] Sources and author credit are on the page
- [ ] Sharing is set to "Anyone with the link can view" before sending
- [ ] Every control tested on every tab: a narrow date range, each food group, one country

## Testing the controls

Change each control and look at every tab, because a chart that is right with all data can break under a filter.

- **"Now" cards ignore the date range.** Remove the Date range dimension from any card or table that should always show the latest value or the full record, or it goes blank or wrong when the range moves.
- **Fix the axis range on scatters.** Set axis min and max (for example 0 to 50 and 0 to 40) so one country doesn't zoom the chart to a single point.
- **Titles must hold under any filter.** Avoid fixed counts or periods in titles of filtered charts ("Exposed countries, hungriest first", not "The 20 exposed countries").
- **Set decimal precision.** Auto precision prints 154 next to 137.7; set 1 decimal on index cards.
- **Test both signs.** Pick a filter where a change is negative and check the ▼ branch of every custom format.

