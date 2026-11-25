"""Build the slide and poster versions of the three food-price charts.

Outputs (showcase/output/):
    slides/slides.html, slides/slides.pdf, slides/slide-1..4.png   16:9, 960 x 540 pt (PNG 1920 x 1080)
    01-shock.png, 02-exposure.png, 03-warning.png                   hero images (copies of slides 2-4)
    poster/poster.html, poster/poster-landscape.pdf, poster-landscape.png   A1 landscape (PNG 6000 px wide)

Run from the repository root (needs Node with Playwright and a Chromium for the PDF/PNG step):
    python showcase/build_showcase.py

Layout follows the UTS deck kit: palette A for structure, Viridis for data, Google Sans,
960 x 540 pt slides on 43.5-919 pt rails, and the A1 poster template (18 mm margins,
answer band, 18 pt floor). Every number comes from build_hero_charts.compute().
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt

import build_hero_charts as hc

OUT = hc.OUT
SLIDES = OUT / "slides"
POSTER = OUT / "poster"
RENDER = Path(__file__).with_name("render.mjs")

AUTHOR = "Tuan (Mike) Nguyen"
PROJECT = "Food price shock early warning"
APP_URL = "assignment3-faostat-viz.streamlit.app"
REPO_URL = "github.com/tuannm3812/assignment3-faostat-viz"

# Chapter accents (palette A) mark structure only: header rule, tracker, card top rules.
CHAPTERS = [
    ("shock", "The shock", "#32658A", "#EAF0F6"),
    ("exposure", "The exposure", "#825578", "#F3EDF3"),
    ("warning", "The warning", "#896521", "#F6F1E5"),
]


def svg(name: str, w_pt: float, h_pt: float, fs: float, **kw) -> str:
    plt.rcParams["svg.hashsalt"] = f"{name}-{w_pt}-{h_pt}"
    fig = hc.CHARTS[name](DATA, w_pt / 72, h_pt / 72, fs, **kw)
    return hc.to_svg(fig)


def esc(text: str) -> str:
    """Escape, then allow **bold**."""
    out = html.escape(text)
    parts = out.split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def fmt_month(ym: str) -> str:
    import pandas as pd

    return pd.Timestamp(ym + "-01").strftime("%b %Y")


# --------------------------------------------------------------------------- copy
def story(f: dict) -> dict:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    peaks = " → ".join(f"{v}" for _, v in s["peaks"])
    leads = sorted(w["lead_months"])
    now = w["latest_yoy_pct"]
    return {
        "shock": {
            "title": "Three food-price spikes since 2007, each peak higher than the last",
            "subtitle": f"FAO Food Price Index, all foods, monthly. Peaks: {peaks}. The {fmt_month(s['record'][0])} peak "
                        f"is the highest since the index began in {s['series_start'][:4]}.",
            "legend": [("band", hc.SHOCK, f"Shock month: prices more than {s['threshold_yoy_pct']:.0f}% above a year earlier"),
                       ("line", hc.FOOD, "All-food price index")],
            "source": f"**Source:** FAO Food Price Index (2014–16 = 100), {fmt_month(s['series_start'])} to "
                      f"{fmt_month(s['latest'][0])}. Shock months computed from year-on-year change.",
            "takeaway": f"Each shock lasted more than a year. Prices are still {s['latest'][1]} today, well above "
                        f"the 2014–16 base of 100.",
        },
        "exposure": {
            "title": f"{e['exposed_count']} of {e['countries_plotted']} countries pair serious hunger with high "
                     "food-import reliance",
            "subtitle": "Each dot is a country. These countries buy much of their food abroad, so a global price "
                        "spike lands on households that are already hungry.",
            "legend": [("dot", hc.EXPOSED, "Exposed: serious hunger and above-median food imports"),
                       ("dot", hc.OTHER, "Other countries")],
            "source": f"**Sources:** Global Hunger Index 2025; World Bank, food imports (% of merchandise imports), "
                      f"latest year {e['import_year_min']}–{e['import_year_max']} per country. "
                      "**Note:** labels name some of the 20 exposed countries.",
            "takeaway": "These 20 countries are the first places to watch and prepare when a shock signal appears.",
        },
        "warning": {
            "title": "Oils and cereals rose 20% before every food-price shock since 2000",
            "subtitle": f"The two-price signal fired {w['signals']} times. {w['followed_by_shock_within_12m']} were "
                        f"followed by a shock {leads[0]} to {leads[-1]} months later; one (2002) was not.",
            "legend": [("line", hc.FOOD, "All food"), ("line", hc.OILS, "Vegetable oils"),
                       ("line", hc.CEREALS, "Cereals"), ("band", hc.SHOCK, "Shock months"),
                       ("box", hc.SIGNAL, "Signal: oils and cereals both 20%+ above a year earlier, with months until the shock")],
            "source": f"**Source:** FAO Food Price Index, monthly, {fmt_month(w['period'][0])} to "
                      f"{fmt_month(w['period'][1])}. **Note:** the rule was read off this same history, so it is "
                      "a signal to watch, not a tested forecast.",
            "takeaway": f"No signal now. In {fmt_month(now['month'])} oils are +{now['oils']:.0f}% and cereals "
                        f"+{now['cereals']:.0f}% on a year earlier.",
        },
    }


# --------------------------------------------------------------------------- shared CSS
def font_css(prefix: str) -> str:
    return f"""
@font-face {{ font-family: 'Google Sans'; font-weight: 400; src: url('{prefix}GoogleSans-Regular.ttf'); }}
@font-face {{ font-family: 'Google Sans'; font-weight: 700; src: url('{prefix}GoogleSans-Bold.ttf'); }}
"""


def legend_html(items) -> str:
    out = []
    for kind, color, label in items:
        out.append(f'<span class="key"><i class="k-{kind}" style="--c:{color}"></i>{esc(label)}</span>')
    return '<div class="legend">' + "".join(out) + "</div>"


# --------------------------------------------------------------------------- slides
SLIDE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; }
body { font-family: 'Google Sans', sans-serif; color: #1B2430; }
@page { size: 960pt 540pt; margin: 0; }
.slide { position: relative; width: 960pt; height: 540pt; overflow: hidden; page-break-after: always; background: #fff; }
.hdr { position: absolute; left: 43.5pt; top: 32pt; display: flex; align-items: center; font-size: 10pt; }
.hdr .sec { font-weight: 700; letter-spacing: .02em; text-transform: uppercase; position: relative; }
.hdr .sec::after { content: ''; position: absolute; left: 0; bottom: -6pt; width: 30pt; height: 2pt; background: var(--acc); }
.hdr .sep { width: 1px; height: 11pt; background: #D8DEE3; margin: 0 8pt; }
.hdr .topic { color: #5A6370; }
.tracker { position: absolute; right: 41pt; top: 26pt; display: flex; gap: 6pt; }
.tracker div { width: 26pt; text-align: center; font-size: 8pt; color: #5A6370; padding-top: 7pt; border-top: 2pt solid #D8DEE3; }
.tracker div.on { color: var(--acc); font-weight: 700; border-top: 3.5pt solid var(--acc); background: var(--pale); padding-bottom: 2pt; }
h1 { position: absolute; left: 43.5pt; right: 41pt; top: 60pt; font-size: 24pt; line-height: 1.18; font-weight: 700; letter-spacing: -.005em; }
.sub { position: absolute; left: 43.5pt; right: 41pt; top: 100pt; font-size: 12pt; line-height: 1.4; color: #5A6370; }
.legend { position: absolute; left: 43.5pt; right: 41pt; top: 132pt; display: flex; flex-wrap: wrap; gap: 4pt 16pt; font-size: 8pt; color: #5A6370; }
.key { display: inline-flex; align-items: center; gap: 5pt; }
.key i { display: inline-block; }
.k-line { width: 16pt; height: 2.5pt; border-radius: 2pt; background: var(--c); }
.k-dot { width: 8pt; height: 8pt; border-radius: 50%; background: var(--c); }
.k-band { width: 14pt; height: 9pt; background: color-mix(in srgb, var(--c) 32%, white); }
.k-box { width: 14pt; height: 7pt; background: var(--c); }
.fig { position: absolute; left: 43.5pt; top: 152pt; width: 875.5pt; }
.fig svg { display: block; width: 100%; height: auto; }
.src { position: absolute; left: 43.5pt; right: 41pt; top: 432pt; font-size: 8pt; color: #5A6370; line-height: 1.35; }
.src b { color: #1B2430; }
.take { position: absolute; left: 43.5pt; right: 41pt; top: 456pt; height: 40pt; background: #F6F1E5; border-left: 3pt solid #B89245;
        display: flex; align-items: center; font-size: 10pt; }
.take span { width: 120pt; padding-left: 14pt; color: #765718; font-weight: 700; font-size: 8pt; letter-spacing: .06em; }
.foot { position: absolute; left: 0; right: 0; top: 512pt; border-top: 1px solid #1B2430; font-size: 8pt; color: #1B2430; }
.foot::before { content: ''; position: absolute; left: 0; top: -2.5pt; width: 43.5pt; height: 2.5pt; background: var(--acc); }
.foot .l { position: absolute; left: 43.5pt; top: 8pt; }
.foot .r { position: absolute; right: 41pt; top: 8pt; color: #5A6370; }
/* summary */
.cards { position: absolute; left: 43.5pt; right: 41pt; top: 146pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20pt; }
.card { background: #F4F5F6; border-top: 3pt solid var(--ca); padding: 14pt 14pt 16pt; height: 284pt; display: flex; flex-direction: column; }
.card .lab { font-size: 8pt; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--ca); }
.card .num { font-size: 54pt; font-weight: 700; line-height: 1; margin-top: 18pt; letter-spacing: -.01em; }
.card .unit { font-size: 10pt; color: #5A6370; margin-top: 6pt; }
.card h3 { font-size: 12pt; line-height: 1.3; margin-top: auto; padding-top: 12pt; border-top: 1px solid #D8DEE3; }
.card p { font-size: 10pt; line-height: 1.45; color: #5A6370; margin-top: 8pt; }
"""


def slide_header(i_ch: int | None, topic: str) -> str:
    acc, pale = (CHAPTERS[i_ch][2], CHAPTERS[i_ch][3]) if i_ch is not None else ("#526174", "#EDF0F3")
    label = CHAPTERS[i_ch][1] if i_ch is not None else "Overview"
    tracker = "".join(
        f'<div class="{"on" if i == i_ch else ""}">{i + 1}</div>' for i in range(len(CHAPTERS))
    )
    return (f'<div class="hdr"><span class="sec">{label}</span><span class="sep"></span>'
            f'<span class="topic">{html.escape(topic)}</span></div><div class="tracker">{tracker}</div>'), acc, pale


def footer(n: int) -> str:
    return f'<div class="foot"><span class="l"><b>{PROJECT}</b> · {AUTHOR}</span><span class="r">{n}</span></div>'


def build_slides(f: dict, copy: dict) -> list[str]:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    pages = []
    hdr, acc, pale = slide_header(None, "Global food prices, 1990–2026")
    cards = [
        (CHAPTERS[0], f"{s['record'][1]}", f"index peak, {fmt_month(s['record'][0])}",
         "Food-price shocks keep getting bigger",
         f"Three shocks since 2007, peaking at {s['peaks'][0][1]}, {s['peaks'][1][1]} and {s['peaks'][2][1]}."),
        (CHAPTERS[1], f"{e['exposed_count']} of {e['countries_plotted']}", "countries most exposed",
         "Hunger and import reliance overlap",
         "Serious hunger (GHI 20+) and above-median food imports: a price spike hits these first."),
        (CHAPTERS[2], f"{w['followed_by_shock_within_12m']} of {w['signals']}", "signals followed by a shock",
         "Two prices moved first",
         f"Oils and cereals both up 20%+ came {min(w['lead_months'])}–{max(w['lead_months'])} months before every "
         "shock since 2000."),
    ]
    card_html = "".join(
        f'<div class="card" style="--ca:{ch[2]}"><div class="lab">{i + 1} · {ch[1]}</div><div class="num">{num}</div>'
        f'<div class="unit">{esc(unit)}</div><h3>{esc(h)}</h3><p>{esc(p)}</p></div>'
        for i, (ch, num, unit, h, p) in enumerate(cards)
    )
    now = w["latest_yoy_pct"]
    pages.append(
        f'<section class="slide" style="--acc:{acc};--pale:{pale}">{hdr}'
        f'<h1>Food-price shocks are growing, and two prices warn of them early</h1>'
        f'<div class="sub">What 36 years of FAO prices, the 2025 Global Hunger Index and World Bank '
        f'trade data show.</div><div class="cards">{card_html}</div>'
        f'<div class="take"><span>TAKEAWAY</span>{esc(f"No warning signal in {fmt_month(now["month"])}: oils +{now["oils"]:.0f}%, cereals +{now["cereals"]:.0f}% on a year earlier. Watch both monthly.")}</div>'
        f'{footer(1)}</section>'
    )
    topics = {"shock": "Global food prices", "exposure": "Who feels it first", "warning": "An early signal"}
    for i, (key, *_rest) in enumerate(CHAPTERS):
        c = copy[key]
        hdr, acc, pale = slide_header(i, topics[key])
        figure = svg(key, 875.5, 272, 10)
        pages.append(
            f'<section class="slide" style="--acc:{acc};--pale:{pale}">{hdr}<h1>{esc(c["title"])}</h1>'
            f'<div class="sub">{esc(c["subtitle"])}</div>{legend_html(c["legend"])}'
            f'<div class="fig">{figure}</div><div class="src">{esc(c["source"])}</div>'
            f'<div class="take"><span>TAKEAWAY</span>{esc(c["takeaway"])}</div>{footer(i + 2)}</section>'
        )
    return pages


# --------------------------------------------------------------------------- poster
POSTER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: 841mm 594mm; margin: 0; }
html, body { background: #fff; }
body { font-family: 'Google Sans', sans-serif; color: #1B2430; }
.poster { position: relative; width: 841mm; height: 594mm; padding: 18mm; display: flex; flex-direction: column; gap: 7mm; overflow: hidden; }
.top { font-size: 20pt; letter-spacing: .08em; text-transform: uppercase; color: #5A6370; }
.title { font-size: 64pt; font-weight: 700; line-height: 1.05; letter-spacing: -.012em; margin-top: 3mm; }
.q { font-size: 26pt; color: #5A6370; margin-top: 4mm; }
.team { font-size: 22pt; font-weight: 700; margin-top: 3mm; }
.answer { background: #1B2430; color: #fff; display: grid; grid-template-columns: 140mm 1fr 220mm; gap: 12mm; padding: 7mm 12mm; }
.answer .num { font-size: 48pt; font-weight: 700; color: #FDE725; line-height: 1; }
.answer .numlab { font-size: 20pt; color: #D8DEE3; margin-top: 3mm; line-height: 1.3; }
.answer .verdict { font-size: 28pt; font-weight: 700; line-height: 1.2; }
.answer .reason { font-size: 22pt; color: #D8DEE3; margin-top: 3mm; line-height: 1.35; }
.answer .reason b { color: #fff; }
.answer .next { font-size: 20pt; line-height: 1.35; color: #D8DEE3; }
.answer .next .lab { font-weight: 700; letter-spacing: .08em; color: #fff; margin-bottom: 2mm; }
.answer .next ol { padding-left: 8mm; }
.answer .next b { color: #fff; }
.body { flex: 1; display: grid; grid-template-columns: 170mm 1fr; gap: 10mm; min-height: 0; }
.ctx { display: flex; flex-direction: column; gap: 6mm; }
.ctx .box { background: #F4F5F6; border-top: 2mm solid #526174; padding: 6mm; }
.ctx h3 { font-size: 20pt; letter-spacing: .08em; text-transform: uppercase; color: #526174; margin-bottom: 3mm; }
.ctx p, .ctx li { font-size: 20pt; line-height: 1.35; color: #5A6370; }
.ctx li { margin-left: 7mm; margin-top: 2mm; }
.ctx b { color: #1B2430; }
.ev { display: grid; grid-template-rows: auto 1fr; gap: 8mm; min-height: 0; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8mm; }
.card { border-top: 2mm solid var(--acc); padding-top: 4mm; display: flex; flex-direction: column; }
.card .lab { font-size: 20pt; letter-spacing: .08em; text-transform: uppercase; color: var(--acc); font-weight: 700; }
.card h2 { font-size: 28pt; line-height: 1.2; margin-top: 2mm; }
.legend { display: flex; flex-wrap: wrap; gap: 2mm 8mm; font-size: 18pt; color: #5A6370; margin-top: 3mm; }
.key { display: inline-flex; align-items: center; gap: 2.5mm; }
.key i { display: inline-block; }
.k-line { width: 12mm; height: 1.6mm; border-radius: 1mm; background: var(--c); }
.k-dot { width: 5mm; height: 5mm; border-radius: 50%; background: var(--c); }
.k-band { width: 10mm; height: 6mm; background: color-mix(in srgb, var(--c) 32%, white); }
.k-box { width: 10mm; height: 5mm; background: var(--c); }
.fig { margin-top: 3mm; }
.fig svg { display: block; width: 100%; height: auto; }
.src { font-size: 18pt; color: #5A6370; margin-top: 2mm; line-height: 1.3; }
.src b { color: #1B2430; }
.foot { display: flex; justify-content: space-between; font-size: 18pt; color: #5A6370; border-top: 1px solid #1B2430; padding-top: 3mm; }
.foot b { color: #1B2430; }
"""

MM = 72 / 25.4  # points per mm
POSTER_LABELS = ["Haiti", "Niger", "Madagascar", "Papua New Guinea", "Sierra Leone"]


def build_poster(f: dict, copy: dict) -> str:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    now = w["latest_yoy_pct"]
    leads = sorted(w["lead_months"])
    ev_w = 841 - 36 - 170 - 10  # evidence column width, mm
    half = (ev_w - 8) / 2
    fig_shock = svg("shock", ev_w * MM, 100 * MM, 24)
    fig_exp = svg("exposure", half * MM, 158 * MM, 24, labels=POSTER_LABELS)
    fig_warn = svg("warning", half * MM, 158 * MM, 24)

    def card(i, key, fig, src_key=True):
        c = copy[key]
        ch = CHAPTERS[i]
        return (f'<div class="card" style="--acc:{ch[2]}"><div class="lab">{i + 1} · {ch[1]}</div>'
                f'<h2>{esc(c["title"])}</h2>{legend_html(c["legend"])}<div class="fig">{fig}</div>'
                f'<div class="src">{esc(c["source"])}</div></div>')

    return f"""
<div class="poster">
  <header>
    <div class="top">Data visualisation project | FAOSTAT food prices</div>
    <div class="title">Oils and cereals moved first in every food-price shock since 2000</div>
    <div class="q">When global food prices spike, which countries feel it first, and can we see it coming?</div>
    <div class="team">{AUTHOR}</div>
  </header>
  <div class="answer">
    <div><div class="num">{w['followed_by_shock_within_12m']} of {w['signals']}</div>
      <div class="numlab">times oils and cereals both rose 20%+, a food-price shock followed {leads[0]}–{leads[-1]} months later</div></div>
    <div><div class="verdict">Watch two prices, protect {e['exposed_count']} countries.</div>
      <div class="reason">{esc(f"Shocks are growing (peaks **{s['peaks'][0][1]} → {s['peaks'][1][1]} → {s['peaks'][2][1]}**) and land hardest where hunger is serious and food is mostly imported. Today there is **no signal**: oils +{now['oils']:.0f}%, cereals +{now['cereals']:.0f}% ({fmt_month(now['month'])}).")}</div></div>
    <div class="next"><div class="lab">NEXT</div><ol>
      <li><b>Monitor:</b> check oils and cereals each month.</li>
      <li><b>Prepare:</b> put the {e['exposed_count']} exposed countries first.</li>
      <li><b>Test:</b> back-test the rule on held-out years.</li></ol></div>
  </div>
  <div class="body">
    <div class="ctx">
      <div class="box"><h3>The data</h3><ul>
        <li><b>FAO Food Price Index</b>, monthly, {fmt_month(s['series_start'])} to {fmt_month(s['latest'][0])}, five food groups.</li>
        <li><b>Global Hunger Index 2025</b>, {e['countries_plotted']} countries with import data.</li>
        <li><b>World Bank</b> food imports as % of merchandise imports, latest year {e['import_year_min']}–{e['import_year_max']}.</li></ul></div>
      <div class="box"><h3>Definitions</h3><ul>
        <li><b>Shock month:</b> all-food index 20%+ above a year earlier.</li>
        <li><b>Signal:</b> oils and cereals both 20%+ above a year earlier, outside a shock.</li>
        <li><b>Exposed:</b> GHI 20+ and food imports above the {e['median_food_import_pct']}% median.</li></ul></div>
      <div class="box"><h3>Limits</h3><ul>
        <li>The rule was read off the same history: a signal to watch, not a forecast.</li>
        <li>Machine-learning models trained on pre-2013 data missed most of the 2020–21 rise.</li>
        <li>Import shares come from different years per country.</li></ul></div>
      <div class="box"><h3>Explore</h3><p>Interactive dashboard: <b>{APP_URL}</b></p></div>
    </div>
    <div class="ev">
      {card(0, 'shock', fig_shock)}
      <div class="row2">{card(1, 'exposure', fig_exp)}{card(2, 'warning', fig_warn)}</div>
    </div>
  </div>
  <div class="foot"><span><b>{PROJECT}</b> · {AUTHOR}</span><span>{REPO_URL}</span></div>
</div>"""


# --------------------------------------------------------------------------- render
def page(body: str, css: str, font_prefix: str, title: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
            f'<style>{font_css(font_prefix)}{css}</style></head><body>{body}</body></html>')


def render(kind: str, src: Path, out: Path) -> None:
    subprocess.run(["node", str(RENDER), kind, str(src), str(out)], check=True)


def main() -> None:
    global DATA
    DATA = hc.main()
    f = DATA["findings"]
    copy = story(f)
    for d in (SLIDES, POSTER):
        d.mkdir(parents=True, exist_ok=True)
    fonts_rel = "../../fonts/"

    slides = build_slides(f, copy)
    (SLIDES / "slides.html").write_text(page("".join(slides), SLIDE_CSS, fonts_rel, PROJECT))
    (POSTER / "poster.html").write_text(page(build_poster(f, copy), POSTER_CSS, fonts_rel, PROJECT + " poster"))
    (OUT / "copy.json").write_text(json.dumps(copy, indent=2, ensure_ascii=False))

    render("slides", SLIDES / "slides.html", SLIDES)
    render("poster", POSTER / "poster.html", POSTER)
    for i, name in enumerate(["01-shock", "02-exposure", "03-warning"], start=2):
        shutil.copyfile(SLIDES / f"slide-{i}.png", OUT / f"{name}.png")
    print("Built slides and poster in", OUT)


DATA: dict = {}

if __name__ == "__main__":
    main()
