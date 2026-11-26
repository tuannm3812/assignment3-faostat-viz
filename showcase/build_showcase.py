"""Build the slide deck and A1 poster for the food-price story.

Outputs (showcase/output/):
    slides/slides.html, slides/slides.pdf, slides/slide-1..20.png   16:9, 960 x 540 pt (PNG 1920 x 1080)
    01-shock.png, 02-exposure.png, 03-warning.png                   hero images (copies of the chart slides)
    poster/poster.html, poster/poster-landscape.pdf, .png          A1 landscape (PNG 6000 px wide)

Run from the repository root (needs Node with Playwright and a Chromium for the PDF/PNG step):
    python showcase/build_showcase.py

Layout follows the UTS deck kit and the Text-to-SQL showcase built with it: split cover, chapter tracker,
finding titles, a figure frame on the left with a takeaway and numbered notes on the right (red markers tie a
note to its place on the chart), an A1 poster with an answer band, section rows and a closing call to action.
Palette A marks structure; Viridis marks data. Every number comes from build_hero_charts.compute().
"""

from __future__ import annotations

import html
import io
import json
import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import build_hero_charts as hc

OUT = hc.OUT
SLIDES = OUT / "slides"
POSTER = OUT / "poster"
HERE = Path(__file__).parent
RENDER = HERE / "render.mjs"

AUTHOR = "Manh Tuan (Mike) Nguyen"
SCHOOL = "University of Technology Sydney"
SUBJECT = "36104 Data Visualisation and Narratives"
TITLE = ["Watch two prices.", "Protect twenty countries."]
PROJECT = "Food Price Shock Early Warning"
APP_URL = "https://assignment3-faostat-viz.streamlit.app/"
REPO_URL = "github.com/tuannm3812/assignment3-faostat-viz"
DATE = "November 2026"

INK, BODY, HAIR, CARD = "#1B2430", "#5A6370", "#D8DEE3", "#F4F5F6"
# Chapter accents (palette A): structure only.
CH = {
    "shock": ("The shock", "#32658A", "#EAF0F6"),
    "exposure": ("The exposure", "#825578", "#F3EDF3"),
    "warning": ("The warning", "#896521", "#F6F1E5"),
    "next": ("Next", "#526174", "#EDF0F3"),
}
ORDER = list(CH)


# --------------------------------------------------------------------------- helpers
def esc(text: str) -> str:
    """Escape, then allow **bold** and {k}key term{/k} (chapter-coloured)."""
    out = html.escape(text)
    parts = out.split("**")
    out = "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))
    return out.replace("{k}", '<span class="kt">').replace("{/k}", "</span>")


def month(ym: str) -> str:
    return pd.Timestamp(ym + "-01").strftime("%b %Y")


def svg(name: str, w_pt: float, h_pt: float, fs: float, **kw) -> str:
    plt.rcParams["svg.hashsalt"] = f"{name}-{w_pt:.0f}-{h_pt:.0f}-{fs}"
    fig = hc.CHARTS[name](DATA, w_pt / 72, h_pt / 72, fs, **kw)
    return hc.to_svg(fig)


def logo() -> str:
    return (HERE / "assets" / "uts-logo.svg").read_text().split("?>", 1)[-1]


def qr_svg(url: str) -> str:
    import qrcode
    import qrcode.image.svg

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode().split("?>", 1)[-1]


def legend(items) -> str:
    keys = "".join(f'<span class="key"><i class="k-{k}" style="--c:{c}"></i>{esc(t)}</span>' for k, c, t in items)
    return f'<div class="legend">{keys}</div>'


# --------------------------------------------------------------------------- native mini figures
def mini_spark(f: dict) -> str:
    """Annual all-food index, peaks dotted."""
    s = DATA["ffpi"]["ffpi_food"].resample("YS").mean()
    xs = [(i / (len(s) - 1)) * 300 for i in range(len(s))]
    ys = [100 - (v / 170) * 96 for v in s.values]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    dots = ""
    for t, v in DATA["peaks"]:
        i = list(s.index.year).index(t.year)
        dots += f'<circle cx="{xs[i]:.1f}" cy="{100 - (v / 170) * 96:.1f}" r="4" fill="{hc.FOOD}" stroke="#fff" stroke-width="1.5"/>'
    base = 100 - (100 / 170) * 96
    return (f'<svg viewBox="0 -4 300 108" class="mini"><line x1="0" x2="300" y1="{base:.1f}" y2="{base:.1f}" '
            f'stroke="#89949D" stroke-dasharray="3 3" stroke-width="1"/><polyline points="{pts}" fill="none" '
            f'stroke="{hc.FOOD}" stroke-width="2.5" stroke-linejoin="round"/>{dots}</svg>')


def mini_grid(n_on: int, n: int) -> str:
    """One square per country; exposed ones filled."""
    cols = 23
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        fill = hc.EXPOSED if i < n_on else "#D8DEE3"
        out.append(f'<rect x="{c * 13}" y="{r * 13}" width="10.5" height="10.5" rx="1.5" fill="{fill}"/>')
    rows = (n + cols - 1) // cols
    return f'<svg viewBox="0 0 {cols * 13} {rows * 13}" class="mini">{"".join(out)}</svg>'


def mini_signals(f: dict) -> str:
    """The five signals on a 2000-2026 line: filled when a shock followed, with the lead."""
    w = f["warning"]
    t0, t1 = pd.Timestamp("2000-01-01"), pd.Timestamp(w["period"][1] + "-01")
    span = (t1 - t0).days
    out = [f'<line x1="0" x2="300" y1="30" y2="30" stroke="{HAIR}" stroke-width="1.5"/>']
    for a, _, hit in w["signal_runs"]:
        x = (pd.Timestamp(a + "-01") - t0).days / span * 300
        if hit:
            lead = (pd.Timestamp(hit + "-01").to_period("M") - pd.Timestamp(a + "-01").to_period("M")).n
            out.append(f'<rect x="{x - 6:.1f}" y="18" width="12" height="24" rx="2" fill="{hc.SIGNAL}"/>'
                       f'<text x="{x:.1f}" y="58" text-anchor="middle" class="ml">{lead} mo</text>')
        else:
            out.append(f'<rect x="{x - 6:.1f}" y="18" width="12" height="24" rx="2" fill="#fff" stroke="{hc.SIGNAL}" '
                       f'stroke-width="1.5"/>')
    for yr in (2000, 2010, 2020):  # year ticks
        x = (pd.Timestamp(f"{yr}-01-01") - t0).days / span * 300
        out.append(f'<text x="{x:.1f}" y="10" text-anchor="{"start" if yr == 2000 else "middle"}" class="ml mute">{yr}</text>')
    return f'<svg viewBox="0 0 300 64" class="mini">{"".join(out)}</svg>'


def gauges(f: dict) -> str:
    """Today's year-on-year change against the +20% signal line."""
    now = f["warning"]["latest_yoy_pct"]
    rows = []
    for label, v, c in (("Vegetable oils", now["oils"], hc.OILS), ("Cereals", now["cereals"], hc.CEREALS)):
        pct = max(0.0, min(v, 30)) / 30 * 100
        rows.append(f'<div class="g"><span class="gl">{label}</span><span class="gb"><i style="width:{pct:.1f}%;'
                    f'background:{c}"></i><u style="left:{20 / 30 * 100:.1f}%"></u></span>'
                    f'<b>+{v:.0f}%</b></div>')
    return (f'<div class="gauges"><div class="gh">Now ({month(now["month"])}) against the +20% line</div>'
            f'{"".join(rows)}</div>')


def heat_table(f: dict) -> str:
    """Largest year-on-year rise of each food group inside each shock, on a Viridis scale."""
    import matplotlib as mpl

    d = f["drivers"]
    cmap = mpl.colormaps["viridis"]
    head = "".join(f"<th>{g}</th>" for g in d["groups"])
    body = []
    for r in d["rows"]:
        top = max(r["values"][:-1])
        cells = []
        for g, v in zip(d["groups"], r["values"]):
            rgba = cmap(min(v, 130) / 130)
            hexc = mpl.colors.to_hex(rgba)
            light = (0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]) > 0.55
            cls = ' class="lead"' if v == top else ""
            cells.append(f'<td{cls} style="background:{hexc};color:{INK if light else "#fff"}">+{v:.0f}%</td>')
        body.append(f'<tr><th>{r["shock"]}</th>{"".join(cells)}</tr>')
    stops = ", ".join(mpl.colors.to_hex(cmap(i / 8)) for i in range(9))
    scale = (f'<div class="hscale"><span>0%</span><i style="background:linear-gradient(90deg,{stops})"></i>'
             f'<span>+130%</span><em>Largest rise on a year earlier during the shock; outlined: the group that rose most</em></div>')
    return f'<table class="heat"><tr><th></th>{head}</tr>{"".join(body)}</table>{scale}'


def ranked(f: dict, n: int = 8) -> str:
    rows = "".join(
        f'<tr><td>{html.escape(c.replace("Central African Republic", "Central African Rep."))}</td>'
        f'<td><b>{g:.1f}</b></td><td>{imp:.1f}%</td></tr>'
        for c, imp, g in f["exposure"]["exposed"][:n]
    )
    return (f'<table class="rank"><tr><th>Highest hunger among the {f["exposure"]["exposed_count"]}</th>'
            f'<th>GHI</th><th>Food imports</th></tr>{rows}</table>')


# --------------------------------------------------------------------------- copy (all numbers from findings)
def story(f: dict) -> dict:
    s, e, w, dr = f["shock"], f["exposure"], f["warning"], f["drivers"]
    pk = s["peaks"]
    leads = sorted(w["lead_months"])
    now = w["latest_yoy_pct"]
    drv = {r["shock"]: dict(zip(dr["groups"], r["values"])) for r in dr["rows"]}
    k = list(drv)
    return {
        "shock": dict(
            title="Three food-price spikes since 2007, each peak higher than the last",
            subtitle=f"FAO Food Price Index, all foods, monthly, {month(s['series_start'])} to {month(s['latest'][0])}.",
            legend=[("band", hc.SHOCK, f"Shock month: prices more than {s['threshold_yoy_pct']:.0f}% above a year earlier"),
                    ("line", hc.FOOD, "All-food price index (2014–16 = 100)")],
            take="Each shock lasted a year or more, and each peak was higher than the one before.",
            notes=[
                ("2007–08 food price crisis", f"Peak **{pk[0][1]}** in {month(pk[0][0])}; oils rose {drv[k[0]]['Vegetable oils']:.0f}% on a year earlier."),
                ("2010–11 price spike", f"Peak **{pk[1][1]}** in {month(pk[1][0])}; cereals rose {drv[k[1]]['Cereals']:.0f}%."),
                ("2021–22 surge and the war in Ukraine", f"Record **{pk[2][1]}** in {month(pk[2][0])}, the highest since {s['series_start'][:4]}. "
                 f"Still **{s['latest'][1]}** in {month(s['latest'][0])}."),
            ],
            source=f"**Source:** FAO Food Price Index (2014–16 = 100). Shock months computed from year-on-year change.",
        ),
        "drivers": dict(
            title=f"Vegetable oils led two of the three shocks; meat never rose more than {max(r['values'][4] for r in dr['rows']):.0f}%",
            subtitle="Largest rise on a year earlier for each FAO food group during each shock period.",
            take="In every shock, either oils or cereals rose most. That is why the warning watches those two prices.",
            notes=[
                ("Vegetable oils", f"Rose most in {k[0]} (+{drv[k[0]]['Vegetable oils']:.0f}%) and {k[2]} (+{drv[k[2]]['Vegetable oils']:.0f}%)."),
                ("Cereals", f"Rose most in {k[1]} (+{drv[k[1]]['Cereals']:.0f}%), and +{drv[k[0]]['Cereals']:.0f}% in {k[0]}."),
                ("Dairy and sugar spiked once each", f"Dairy +{drv[k[0]]['Dairy']:.0f}% in {k[0]}, sugar +{drv[k[1]]['Sugar']:.0f}% in {k[1]}; "
                 f"neither led twice. Meat never passed +{max(r['values'][4] for r in dr['rows']):.0f}%."),
            ],
            source="**Source:** FAO Food Price Index sub-indices, monthly. Shock periods as defined on the previous page.",
        ),
        "exposure": dict(
            title=f"{e['exposed_count']} of {e['countries_plotted']} countries pair serious hunger with high food-import reliance",
            subtitle="Each dot is a country. These countries buy much of their food abroad, so a global spike reaches hungry households.",
            legend=[("dot", hc.EXPOSED, "Exposed: GHI 20+ and above-median food imports"),
                    ("dot", hc.OTHER, "Other countries")],
            take=f"These {e['exposed_count']} countries are where to prepare first when the signal appears.",
            source=(f"**Sources:** Global Hunger Index 2025; World Bank, food imports (% of merchandise imports), latest year "
                    f"{e['import_year_min']}–{e['import_year_max']}. **Note:** median food-import share {e['median_food_import_pct']}%."),
        ),
        "warning": dict(
            title="Oils and cereals rose 20% before every food-price shock since 2000",
            subtitle=f"Year-on-year change, {month(w['period'][0])} to {month(w['period'][1])}, with the two-price signal below.",
            legend=[("line", hc.FOOD, "All food"), ("line", hc.OILS, "Vegetable oils"), ("line", hc.CEREALS, "Cereals"),
                    ("band", hc.SHOCK, "Shock months"), ("box", hc.SIGNAL, "Signal: both 20%+ above a year earlier")],
            take=f"No signal now: oils +{now['oils']:.0f}% and cereals +{now['cereals']:.0f}% in {month(now['month'])}.",
            notes=[
                (f"{w['followed_by_shock_within_12m']} of {w['signals']} signals hit", f"A shock followed {leads[0]} to {leads[-1]} months later."),
                ("One false alarm", "The 2002 signal was not followed by a shock."),
                ("A signal, not a forecast", "The rule was read off this same history, so it still needs a test on years it has not seen."),
            ],
            source="**Source:** FAO Food Price Index, monthly. Signal: oils and cereals both more than 20% above a year earlier, outside a shock.",
        ),
        "next": [
            ("Monitor", "Check oils and cereals every month", "The FAO index is published monthly; the rule needs only two numbers."),
            ("Prepare", f"Put the {e['exposed_count']} exposed countries first", "Pre-position support where hunger is serious and food is imported."),
            ("Test", "Back-test the rule on held-out years", "Fix the rule on early data, then score it on later shocks."),
        ],
    }


# --------------------------------------------------------------------------- slides
SLIDE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; }
body { font-family: 'Google Sans', sans-serif; color: #1B2430; }
@page { size: 960pt 540pt; margin: 0; }
.slide { position: relative; width: 960pt; height: 540pt; overflow: hidden; page-break-after: always; background: #fff; }
.kt { color: var(--acc); }
.hdr { position: absolute; left: 43.5pt; top: 32pt; display: flex; align-items: center; font-size: 8pt; }
.hdr .sec { font-weight: 700; text-transform: uppercase; position: relative; letter-spacing: .02em; }
.hdr .sec::after { content: ''; position: absolute; left: 0; right: 0; bottom: -4pt; height: 1.5pt; background: var(--acc); }
.hdr .sep { width: 1px; height: 9pt; background: #D8DEE3; margin: 0 8pt; }
.hdr .topic { color: #5A6370; }
.tracker { position: absolute; right: 84pt; top: 30pt; display: flex; gap: 5pt; }
.tracker div { width: 21pt; text-align: center; font-size: 6.5pt; color: #5A6370; padding-top: 5pt; border-top: 2pt solid #D8DEE3; }
.tracker div.on { color: var(--acc); font-weight: 700; border-top: 3pt solid var(--acc); background: var(--pale); padding-bottom: 2pt; }
.ulogo { position: absolute; right: 41pt; top: 26pt; width: 32pt; height: 32pt; }
.ulogo svg { width: 100%; height: 100%; display: block; }
h1 { position: absolute; left: 43.5pt; right: 41pt; top: 66pt; font-size: 20pt; line-height: 1.2; font-weight: 700; }
.sub { position: absolute; left: 43.5pt; right: 41pt; top: 96pt; font-size: 10pt; color: #5A6370; }
.left { position: absolute; left: 43.5pt; width: 624.5pt; top: 122pt; bottom: 64pt; display: flex; flex-direction: column; }
.right { position: absolute; left: 688pt; width: 231pt; top: 122pt; bottom: 64pt; display: flex; flex-direction: column; gap: 12pt; }
.legend { display: flex; flex-wrap: wrap; gap: 3pt 12pt; font-size: 7pt; color: #5A6370; margin-bottom: 4pt; }
.key { display: inline-flex; align-items: center; gap: 4pt; }
.key i { display: inline-block; }
.k-line { width: 13pt; height: 2.2pt; border-radius: 2pt; background: var(--c); }
.k-dot { width: 7pt; height: 7pt; border-radius: 50%; background: var(--c); }
.k-band { width: 11pt; height: 8pt; background: color-mix(in srgb, var(--c) 32%, white); }
.k-box { width: 11pt; height: 6pt; background: var(--c); }
.fig svg { display: block; width: 100%; height: auto; }
.src { margin-top: auto; font-size: 7pt; color: #5A6370; line-height: 1.35; }
.src b { color: #1B2430; }
.take { background: #F6F1E5; border-top: 3pt solid #B89245; padding: 9pt 11pt 10pt; font-size: 10pt; line-height: 1.35; }
.take .lab { display: block; color: #765718; font-weight: 700; font-size: 6.5pt; letter-spacing: .08em; margin-bottom: 4pt; }
.notes { display: flex; flex-direction: column; gap: 10pt; }
.note { display: grid; grid-template-columns: 14pt 1fr; gap: 0 6pt; }
.note .m { width: 12pt; height: 12pt; border-radius: 50%; background: #B8452E; color: #fff; font-size: 7pt; font-weight: 700; display: grid; place-items: center; margin-top: 1pt; }
.note h4 { font-size: 9.5pt; line-height: 1.25; }
.note p { grid-column: 2; font-size: 8.5pt; line-height: 1.4; color: #5A6370; margin-top: 2pt; }
.note p b { color: #1B2430; }
.foot { position: absolute; left: 0; right: 0; top: 504pt; border-top: 1px solid #1B2430; font-size: 7pt; }
.foot::before { content: ''; position: absolute; left: 0; top: -2.5pt; width: 43.5pt; height: 2.5pt; background: var(--acc); }
.foot .l { position: absolute; left: 43.5pt; top: 9pt; font-weight: 700; }
.foot .r { position: absolute; right: 41pt; top: 9pt; color: #5A6370; }
/* cover */
.cover .ulogo { left: 43.5pt; top: 36pt; width: 52pt; height: 52pt; }
.cover .band { position: absolute; left: 0; width: 466pt; top: 132pt; height: 150pt; background: #EDF0F3; border-left: 6pt solid #32658A; padding: 22pt 30pt 0 37.5pt; }
.cover .lbl { font-size: 6.5pt; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #32658A; }
.cover .ttl { font-size: 26pt; line-height: 1.16; font-weight: 700; margin-top: 10pt; }
.cover .cs { font-size: 8.5pt; color: #5A6370; margin-top: 10pt; line-height: 1.4; }
.cover .who { position: absolute; left: 43.5pt; top: 306pt; font-size: 8pt; line-height: 1.6; color: #5A6370; }
.cover .who b { color: #1B2430; font-size: 9pt; }
.cover .art { position: absolute; left: 466pt; top: 0; right: 0; bottom: 0; background: #1B2430; }
.cover .art svg { position: absolute; left: 28pt; right: 28pt; bottom: 52pt; width: calc(100% - 56pt); height: auto; }
.cover .art p { position: absolute; left: 28pt; right: 28pt; bottom: 22pt; color: #89949D; font-size: 6.5pt; }
/* summary cards */
.cards { position: absolute; left: 43.5pt; right: 41pt; top: 124pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20pt; }
.card { background: #F4F5F6; border-top: 3pt solid var(--ca); padding: 11pt 12pt 12pt; height: 300pt; justify-content: flex-start; display: flex; flex-direction: column; }
.card .lab { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); }
.card h3 { font-size: 12pt; line-height: 1.25; margin-top: 6pt; }
.card .num { font-size: 26pt; font-weight: 700; margin-top: 12pt; line-height: 1; }
.card .unit { font-size: 8pt; color: #5A6370; margin-top: 3pt; }
.card .mini { width: 100%; height: auto; margin-top: 22pt; display: block; }
.card p { font-size: 8.5pt; color: #5A6370; line-height: 1.4; margin-top: auto; padding-top: 10pt; border-top: 1px solid #D8DEE3; }
.ml { font: 9px 'Google Sans'; fill: #1B2430; }
.ml.mute { fill: #5A6370; }
.bandtake { position: absolute; left: 43.5pt; right: 41pt; top: 444pt; height: 40pt; background: #F6F1E5; border-left: 3pt solid #B89245; display: flex; align-items: center; font-size: 10pt; }
.bandtake span { width: 110pt; padding-left: 12pt; color: #765718; font-weight: 700; font-size: 6.5pt; letter-spacing: .08em; }
/* heat table, ranked list, gauges */
.heat { width: 100%; border-collapse: separate; border-spacing: 3pt; margin-top: 8pt; }
.heat th { font-size: 8pt; font-weight: 700; color: #5A6370; text-align: center; padding: 3pt; }
.heat tr th:first-child { text-align: left; color: #1B2430; font-size: 10pt; width: 70pt; }
.heat td { text-align: center; font-size: 15pt; font-weight: 700; height: 80pt; border-radius: 2pt; }
.heat td.lead { outline: 2.5pt solid #1B2430; outline-offset: -2.5pt; }
.hscale { display: flex; align-items: center; gap: 6pt; font-size: 7pt; color: #5A6370; margin: 10pt 0 0 76pt; flex-wrap: wrap; }
.hscale i { width: 120pt; height: 7pt; border-radius: 1pt; }
.hscale em { font-style: normal; flex-basis: 100%; margin-top: 2pt; }
.rank { width: 100%; border-collapse: collapse; font-size: 8pt; }
.rank th { text-align: left; font-weight: 700; color: #5A6370; font-size: 7pt; border-bottom: 1px solid #89949D; padding: 0 0 3pt; }
.rank th + th, .rank td + td { text-align: right; }
.rank td { padding: 3.2pt 0; border-bottom: 1px solid #D8DEE3; }
.gauges { background: #F4F5F6; padding: 9pt 11pt; }
.gh { font-size: 7.5pt; color: #5A6370; margin-bottom: 6pt; }
.g { display: grid; grid-template-columns: 62pt 1fr 26pt; align-items: center; gap: 6pt; font-size: 8pt; margin-top: 4pt; }
.g b { text-align: right; }
.gb { position: relative; height: 8pt; background: #fff; }
.gb i { position: absolute; left: 0; top: 0; bottom: 0; }
.gb u { position: absolute; top: -3pt; bottom: -3pt; width: 0; border-left: 1.2pt dashed #1B2430; }
/* next */
.steps { position: absolute; left: 43.5pt; width: 560pt; top: 124pt; display: flex; flex-direction: column; gap: 12pt; }
.step { display: grid; grid-template-columns: 34pt 1fr; gap: 0 12pt; background: #F4F5F6; border-left: 3pt solid var(--acc); padding: 12pt 14pt; }
.step .ic { width: 34pt; height: 34pt; border-radius: 50%; background: #fff; display: grid; place-items: center; color: #32658A; }
.step .ic svg { width: 18pt; height: 18pt; }
.step small { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5A6370; }
.step h3 { font-size: 13pt; margin-top: 2pt; }
.step p { font-size: 8.5pt; color: #5A6370; margin-top: 3pt; }
.cta { position: absolute; left: 624pt; right: 41pt; top: 124pt; height: 192pt; background: #1B2430; color: #fff; padding: 16pt; display: flex; flex-direction: column; }
.cta h3 { font-size: 15pt; line-height: 1.25; }
.cta .qr { margin-top: auto; display: flex; align-items: flex-end; gap: 10pt; font-size: 8pt; color: #D8DEE3; }
.cta .qr div { width: 70pt; height: 70pt; background: #fff; padding: 4pt; }
.cta .qr svg { width: 100%; height: 100%; display: block; }
.data { position: absolute; left: 624pt; right: 41pt; top: 330pt; bottom: 64pt; font-size: 7.5pt; color: #5A6370; line-height: 1.45; }
.data h4 { font-size: 6.5pt; letter-spacing: .08em; text-transform: uppercase; color: #1B2430; margin-bottom: 4pt; }
.data b { color: #1B2430; }
"""

ICONS = {
    "Monitor": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    "Prepare": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "Test": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2h6M10 2v6L4 19a2 2 0 0 0 1.7 3h12.6a2 2 0 0 0 1.7-3L14 8V2"/><path d="M7 15h10"/></svg>',
}


def header(key: str, topic: str, overview: bool = False) -> str:
    label = "Overview" if overview else CH[key][0]
    tr = "".join(f'<div class="{"on" if k == key and not overview else ""}">{i + 1}</div>' for i, k in enumerate(ORDER))
    return (f'<div class="hdr"><span class="sec">{label}</span><span class="sep"></span><span class="topic">{topic}</span></div>'
            f'<div class="tracker">{tr}</div><div class="ulogo">{logo()}</div>')


def slide(key: str, n: int, inner: str) -> str:
    _, acc, pale = CH[key]
    return (f'<section class="slide" style="--acc:{acc};--pale:{pale}">{inner}'
            f'<div class="foot"><span class="l">{PROJECT}</span><span class="r">{n}</span></div></section>')


def right_col(c: dict, extra: str = "") -> str:
    notes = "".join(
        f'<div class="note"><span class="m">{i + 1}</span><h4>{esc(h)}</h4><p>{esc(p)}</p></div>'
        for i, (h, p) in enumerate(c.get("notes", []))
    )
    return (f'<div class="right"><div class="take"><span class="lab">TAKEAWAY</span>{esc(c["take"])}</div>'
            f'{extra}<div class="notes">{notes}</div></div>')


def cover_art() -> str:
    """Palette A motif: one column of pills per year of the annual index; ochre years had shock months."""
    s = DATA["ffpi"]["ffpi_food"].resample("YS").mean()
    shock_years = {t.year for a, b in DATA["eps"] for t in pd.date_range(a, b, freq="MS")}
    cols = []
    for i, (t, v) in enumerate(s.items()):
        n = int(round(v / 10))
        colour = "#B89245" if t.year in shock_years else "#32658A"
        for j in range(n):
            cols.append(f'<rect x="{i * 12}" y="{170 - (j + 1) * 11}" width="9" height="8.5" rx="2.5" fill="{colour}" '
                        f'opacity="{0.55 + 0.45 * j / 16:.2f}"/>')
    return f'<svg viewBox="0 0 {len(s) * 12} 172" role="img" aria-label="Annual FAO Food Price Index as stacked pills">{"".join(cols)}</svg>'


EXTRA_CSS = """
.card { height: 300pt; }
.card .mini { margin-top: 14pt; }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt; margin-top: auto; padding-top: 10pt; }
.stats div { background: #fff; padding: 6pt 8pt; }
.stats b { display: block; font-size: 13pt; }
.stats span { font-size: 7pt; color: #5A6370; line-height: 1.3; display: block; margin-top: 1pt; }
.card .stats + p { margin-top: 10pt; }
.outs { position: absolute; left: 43.5pt; right: 41pt; top: 384pt; }
.orow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10pt; }
.orow div { border-top: 2pt solid #1B2430; padding-top: 6pt; }
.orow b { font-size: 9pt; display: block; }
.orow span { font-size: 7.5pt; color: #5A6370; line-height: 1.4; display: block; margin-top: 2pt; }
.chip.dk { background: #2C3846; color: #fff; }
.trig { font-size: 7.8pt; background: #fff; padding: 6pt 8pt; margin-top: 10pt; line-height: 1.35; }
.tbl td:first-child { white-space: nowrap; }
.k-ring { width: 7pt; height: 7pt; border-radius: 50%; border: 1.3px solid var(--c); background: #fff; }
/* agenda */
.agenda { position: absolute; left: 43.5pt; right: 41pt; top: 128pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14pt; }
.ag { border-top: 3pt solid var(--ca); padding-top: 12pt; height: 250pt; display: flex; flex-direction: column; }
.ag .no { font-size: 38pt; font-weight: 700; color: var(--ca); line-height: 1; }
.ag .lab { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); margin-top: 10pt; }
.ag h3 { font-size: 13pt; line-height: 1.28; margin-top: 5pt; }
.ag ul { list-style: none; margin-top: 12pt; font-size: 8.5pt; color: #5A6370; line-height: 1.45; display: flex; flex-direction: column; gap: 5pt; }
.ag li { padding-left: 10pt; position: relative; }
.ag li::before { content: ''; position: absolute; left: 0; top: 5pt; width: 4pt; height: 4pt; border-radius: 50%; background: var(--ca); }
.ag .pg { margin-top: auto; font-size: 7.5pt; color: #5A6370; border-top: 1px solid #D8DEE3; padding-top: 6pt; }
/* question page */
.qbox { position: absolute; left: 43.5pt; width: 420pt; top: 128pt; height: 236pt; background: #1B2430; color: #fff; padding: 20pt 22pt; display: flex; flex-direction: column; }
.qbox small { font-size: 6.5pt; letter-spacing: .08em; font-weight: 700; color: #FDE725; }
.qbox .qq { font-size: 21pt; line-height: 1.25; font-weight: 700; margin-top: 10pt; }
.qbox p { margin-top: auto; font-size: 8.5pt; color: #D8DEE3; line-height: 1.45; }
.aud { position: absolute; left: 43.5pt; width: 420pt; top: 378pt; display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; }
.aud div { background: #F4F5F6; padding: 10pt 12pt; font-size: 8.5pt; color: #5A6370; line-height: 1.4; }
.aud b { display: block; color: #1B2430; font-size: 9.5pt; margin-bottom: 3pt; }
.needs { position: absolute; left: 488pt; right: 41pt; top: 128pt; height: 310pt; display: flex; flex-direction: column; gap: 12pt; }
.needs .need { flex: 1; align-items: center; }
.need { display: grid; grid-template-columns: 34pt 1fr; gap: 0 12pt; border-left: 3pt solid var(--ca); background: #F4F5F6; padding: 17pt 14pt; }
.need .ic { width: 34pt; height: 34pt; border-radius: 50%; background: #fff; display: grid; place-items: center; color: var(--ca); }
.need .ic svg { width: 17pt; height: 17pt; }
.need small { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); }
.need h3 { font-size: 12pt; margin-top: 2pt; }
.need p { font-size: 8.5pt; color: #5A6370; margin-top: 3pt; line-height: 1.4; }
/* flow */
.flow { position: absolute; left: 43.5pt; right: 41pt; top: 126pt; display: grid; grid-template-columns: 232pt 16pt 170pt 16pt 1fr; align-items: stretch; }
.fcol { display: flex; flex-direction: column; gap: 7pt; }
.fh { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5A6370; margin-bottom: 1pt; }
.src-card { background: #F4F5F6; border-left: 3pt solid #526174; padding: 7pt 10pt; }
.src-card b { font-size: 9pt; display: block; }
.src-card span { font-size: 7.5pt; color: #5A6370; line-height: 1.35; display: block; margin-top: 2pt; }
.src-card em { font-style: normal; font-weight: 700; color: #1B2430; }
.arrow { display: grid; place-items: center; color: #89949D; font-size: 14pt; }
.proc { background: #1B2430; color: #fff; padding: 12pt; display: flex; flex-direction: column; gap: 9pt; height: 100%; }
.proc b { font-size: 9.5pt; }
.proc div { font-size: 7.8pt; color: #D8DEE3; line-height: 1.4; border-top: 1px solid #5A6370; padding-top: 7pt; }
.proc div i { font-style: normal; color: #FDE725; font-weight: 700; margin-right: 4pt; }
.meas { border-top: 3pt solid var(--ca); background: #fff; box-shadow: inset 0 0 0 1px #D8DEE3; padding: 9pt 11pt; }
.meas small { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); }
.meas h4 { font-size: 10.5pt; margin-top: 2pt; }
.meas p { font-size: 7.8pt; color: #5A6370; line-height: 1.4; margin-top: 3pt; }
.meas p b { color: #1B2430; }
/* tables and pills */
.tbl { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
.tbl th { text-align: left; font-size: 7pt; font-weight: 700; color: #5A6370; border-bottom: 1.2px solid #1B2430; padding: 0 10pt 4pt 0; }
.tbl td { padding: 9pt 10pt 9pt 0; border-bottom: 1px solid #D8DEE3; vertical-align: middle; }
.tbl td.n, .tbl th.n { text-align: right; font-variant-numeric: tabular-nums; }
.tbl td b { font-size: 10pt; }
.pill { display: inline-block; font-size: 7pt; font-weight: 700; padding: 2pt 7pt; border-radius: 9pt; }
.pill.hit { background: #1B2430; color: #fff; }
.pill.miss { background: #fff; color: #B8452E; box-shadow: inset 0 0 0 1.2px #B8452E; }
.pill.never { background: #F6F1E5; color: #765718; }
.pill.ok { background: #EAF0F6; color: #32658A; }
.kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10pt; margin-bottom: 14pt; }
.kpi { background: #F4F5F6; border-top: 3pt solid var(--acc); padding: 9pt 11pt; }
.kpi .v { font-size: 22pt; font-weight: 700; line-height: 1; }
.kpi .u { font-size: 7.5pt; color: #5A6370; margin-top: 4pt; line-height: 1.35; }
.tblnote { font-size: 7.5pt; color: #5A6370; margin-top: 8pt; line-height: 1.4; }
/* bars */
.bars { display: flex; flex-direction: column; gap: 12pt; margin-top: 8pt; }
.bar { display: grid; grid-template-columns: 92pt 1fr 46pt 46pt; align-items: center; gap: 8pt; font-size: 10pt; }
.bar .tr { position: relative; height: 28pt; background: #F4F5F6; }
.bar .tr i { position: absolute; top: 3pt; bottom: 3pt; }
.bar .tr u { position: absolute; top: -4pt; bottom: -4pt; width: 0; border-left: 1.3px dashed #1B2430; }
.bar .tr s { position: absolute; top: 0; bottom: 0; width: 0; border-left: 1px solid #89949D; }
.bar b, .bar em { text-align: right; font-variant-numeric: tabular-nums; }
.bar em { font-style: normal; color: #5A6370; }
.barhead { display: grid; grid-template-columns: 92pt 1fr 46pt 46pt; gap: 8pt; font-size: 7pt; font-weight: 700; color: #5A6370; border-bottom: 1.2px solid #1B2430; padding-bottom: 4pt; }
.barhead span:nth-child(3), .barhead span:nth-child(4) { text-align: right; }
.axisl { position: relative; height: 12pt; margin: 4pt 108pt 0 100pt; font-size: 7pt; color: #5A6370; }
.axisl span { position: absolute; transform: translateX(-50%); }
.cmp { background: #F4F5F6; padding: 9pt 11pt; }
.cmp h5 { font-size: 7.5pt; color: #5A6370; font-weight: 400; margin-bottom: 5pt; }
.cmp .r { display: grid; grid-template-columns: 70pt 1fr 32pt; align-items: center; gap: 6pt; font-size: 8pt; margin-top: 3pt; }
.cmp .r span:last-child { text-align: right; font-weight: 700; }
.cmp .r i { display: block; height: 8pt; }
/* rule diagram */
.rule { position: absolute; left: 43.5pt; right: 41pt; top: 128pt; height: 214pt; display: grid; grid-template-columns: 1fr 20pt 1fr 20pt 1fr; align-items: stretch; }
.rstep { background: #F4F5F6; border-top: 3pt solid var(--acc); padding: 13pt 14pt; display: flex; flex-direction: column; }
.rstep .no { width: 22pt; height: 22pt; border-radius: 50%; background: var(--acc); color: #fff; font-weight: 700; font-size: 10pt; display: grid; place-items: center; }
.rstep h3 { font-size: 13pt; margin-top: 9pt; line-height: 1.25; }
.rstep p { font-size: 8.5pt; color: #5A6370; margin-top: 5pt; line-height: 1.45; }
.rstep .viz { margin-top: auto; padding-top: 10pt; }
.rstep.dark { background: #1B2430; color: #fff; }
.rstep.dark p { color: #D8DEE3; }
.rstep.dark .no { background: #FDE725; color: #1B2430; }
.chip { display: inline-flex; align-items: center; gap: 5pt; background: #fff; padding: 5pt 8pt; font-size: 8.5pt; margin: 0 4pt 4pt 0; }
.chip i { width: 9pt; height: 9pt; border-radius: 2pt; }
.example { position: absolute; left: 43.5pt; right: 41pt; top: 362pt; background: #F6F1E5; border-left: 3pt solid #B89245; padding: 11pt 14pt; display: grid; grid-template-columns: 110pt repeat(4, 1fr); gap: 14pt; align-items: center; }
.example .lab { color: #765718; font-weight: 700; font-size: 6.5pt; letter-spacing: .08em; }
.example .ex b { display: block; font-size: 17pt; line-height: 1.1; }
.example .ex span { font-size: 7.5pt; color: #5A6370; }
/* roadmap and limits */
.road { position: absolute; left: 43.5pt; right: 41pt; top: 128pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12pt; }
.rm { background: #F4F5F6; border-top: 3pt solid var(--ca); padding: 12pt 13pt; height: 252pt; display: flex; flex-direction: column; }
.rm .when { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); }
.rm .ic { width: 30pt; height: 30pt; border-radius: 50%; background: #fff; display: grid; place-items: center; color: var(--ca); margin-top: 9pt; }
.rm .ic svg { width: 15pt; height: 15pt; }
.rm h3 { font-size: 12pt; margin-top: 9pt; line-height: 1.25; }
.rm p { font-size: 8.3pt; color: #5A6370; margin-top: 5pt; line-height: 1.45; }
.rm .who { margin-top: auto; border-top: 1px solid #D8DEE3; padding-top: 6pt; font-size: 7.5pt; color: #5A6370; }
.rm .who b { color: #1B2430; }
.bandtake.low { top: 398pt; }
.limits { position: absolute; left: 43.5pt; width: 560pt; top: 128pt; display: flex; flex-direction: column; gap: 10pt; }
.lim { display: grid; grid-template-columns: 22pt 1fr; gap: 0 10pt; background: #F4F5F6; padding: 11pt 13pt; }
.lim .no { width: 20pt; height: 20pt; border: 1.5px solid #B8452E; color: #B8452E; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 9pt; }
.lim h3 { font-size: 11pt; }
.lim p { font-size: 8.3pt; color: #5A6370; margin-top: 3pt; line-height: 1.45; }
.lim p b { color: #1B2430; }
.cta.tall { height: 230pt; }
.appx { position: absolute; left: 43.5pt; right: 41pt; top: 124pt; }
.appx .tbl td { font-size: 8pt; line-height: 1.4; padding: 6pt 10pt 6pt 0; }
.appx .tbl td:first-child { font-weight: 700; width: 130pt; }
"""

V5_CSS = """
/* ---------- shared upgrades (kit layout: canvas | hairline | takeaway column) ---------- */
.right { left: 680pt; width: 239pt; top: 118pt; bottom: 58pt; border-left: 1px solid #D8DEE3; padding-left: 14pt; gap: 11pt; }
.take { border-top: 0; border-left: 3pt solid #B89245; padding: 9pt 11pt 10pt; }
.nxt { margin-top: auto; font-size: 7.5pt; color: var(--acc); font-weight: 700; }
.mk { display: inline-grid; place-items: center; width: 12pt; height: 12pt; border-radius: 50%; background: #B8452E; color: #fff;
      font-size: 7pt; font-weight: 700; box-shadow: 0 0 0 1.2pt #fff; vertical-align: middle; }
.mk.abs { position: absolute; }
.flag { height: 9pt; width: 12pt; border-radius: 1pt; box-shadow: 0 0 0 .6pt rgba(27,36,48,.25); vertical-align: middle; object-fit: cover; }
.ico { width: 13pt; height: 13pt; vertical-align: middle; }
.lens { position: absolute; left: 43.5pt; right: 41pt; top: 109pt; font-size: 7.5pt; color: var(--acc); }
.lens b { font-weight: 700; }
.credit { font-size: 6pt; color: #89949D; }
.k-ring { width: 7pt; height: 7pt; border-radius: 50%; border: 1.3px solid var(--c); background: #fff; }
.k-flag { display: inline-flex; }
.legend .flag { height: 8pt; width: 11pt; }
/* ---------- cover ---------- */
.cv .photo { position: absolute; left: 466pt; top: 0; right: 0; bottom: 0; background-size: cover; background-position: center; }
.cv .photo::after { content: ''; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(27,36,48,0) 45%, rgba(27,36,48,.82) 100%); }
.cv .kpis3 { position: absolute; left: 490pt; right: 24pt; bottom: 30pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt; z-index: 2; }
.cv .kpis3 div { background: rgba(255,255,255,.95); padding: 8pt 10pt; border-top: 3pt solid var(--ca); }
.cv .kpis3 b { display: block; font-size: 16pt; line-height: 1; }
.cv .kpis3 span { display: block; font-size: 6.8pt; color: #5A6370; margin-top: 3pt; line-height: 1.3; }
.cv .pcredit { position: absolute; right: 24pt; bottom: 10pt; z-index: 2; font-size: 5.5pt; color: #D8DEE3; }
.cv .motif { position: absolute; left: 43.5pt; top: 392pt; width: 340pt; }
.cv .motif svg { width: 100%; height: auto; display: block; }
.cv .motif p { font-size: 6pt; color: #89949D; margin-top: 4pt; }
/* ---------- agenda ---------- */
.agenda2 { position: absolute; left: 43.5pt; right: 41pt; top: 118pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12pt; }
.agh { background: var(--pale); padding: 12pt 13pt; height: 90pt; position: relative; }
.agh .no { width: 20pt; height: 20pt; border-radius: 50%; background: var(--ca); color: #fff; font-weight: 700; font-size: 9pt; display: grid; place-items: center; }
.agh .ic { position: absolute; right: 12pt; top: 11pt; color: var(--ca); }
.agh .ic svg { width: 17pt; height: 17pt; }
.agh h3 { font-size: 14pt; margin-top: 10pt; color: var(--ca); }
.agh p { font-size: 8pt; color: #5A6370; margin-top: 2pt; }
.agl { margin-top: 10pt; display: flex; flex-direction: column; gap: 0; }
.agl div { display: flex; justify-content: space-between; align-items: center; font-size: 9pt; padding: 8.5pt 0; border-bottom: 1px solid #D8DEE3; }
.agl i { font-style: normal; font-size: 7pt; font-weight: 700; color: var(--ca); background: var(--pale); padding: 1.5pt 5pt; border-radius: 2pt; }
.opening { position: absolute; left: 43.5pt; right: 41pt; top: 384pt; border-top: 1px solid #D8DEE3; padding-top: 10pt; display: flex; gap: 14pt; align-items: center; font-size: 8pt; color: #5A6370; }
.opening b { color: #1B2430; }
.opening span i { font-style: normal; font-size: 7pt; font-weight: 700; background: #EDF0F3; padding: 1.5pt 5pt; border-radius: 2pt; margin-left: 4pt; }
/* ---------- summary ---------- */
.cards2 { position: absolute; left: 43.5pt; right: 41pt; top: 118pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 16pt; }
.card2 { background: #F4F5F6; border-top: 3pt solid var(--ca); padding: 11pt 12pt 12pt; height: 312pt; display: flex; flex-direction: column; }
.card2 .top { display: flex; align-items: center; gap: 8pt; }
.card2 .circ { width: 22pt; height: 22pt; border-radius: 50%; background: var(--ca); color: #fff; font-weight: 700; font-size: 10pt; display: grid; place-items: center; flex: none; }
.card2 .lab { font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ca); }
.card2 h3 { font-size: 11pt; line-height: 1.2; }
.card2 .num { font-size: 26pt; font-weight: 700; margin-top: 10pt; line-height: 1; }
.card2 .unit { font-size: 7.8pt; color: #5A6370; margin-top: 3pt; }
.card2 .mini { width: 100%; height: auto; margin-top: 10pt; display: block; background: #fff; }
.card2 .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8pt; margin-top: auto; padding-top: 9pt; }
.card2 .stats div { background: #fff; padding: 6pt 8pt; }
.card2 .stats b { display: block; font-size: 12.5pt; }
.card2 .stats span { font-size: 6.8pt; color: #5A6370; line-height: 1.3; display: block; margin-top: 1pt; }
.card2 p { font-size: 8pt; color: #5A6370; line-height: 1.4; margin-top: 8pt; padding-top: 7pt; border-top: 1px solid #D8DEE3; }
.ml { font: 8.5px 'Google Sans'; fill: #1B2430; }
.ml.b { font-weight: 700; }
.ml.mute { fill: #5A6370; }
.ml.s { font-size: 7.5px; }
.bandtake { top: 446pt; height: 38pt; }
.bandtake.low { top: 424pt; }
/* ---------- question ---------- */
.qphoto { position: absolute; left: 43.5pt; width: 452pt; top: 118pt; height: 376pt; background-size: cover; background-position: center; }
.qphoto .credit { position: absolute; right: 6pt; bottom: 4pt; color: #fff; text-shadow: 0 0 3px rgba(0,0,0,.6); }
.qbox2 { position: absolute; left: 43.5pt; width: 300pt; top: 300pt; background: #1B2430; color: #fff; padding: 14pt 16pt 15pt; }
.qbox2 small { font-size: 6.5pt; letter-spacing: .08em; font-weight: 700; color: #FDE725; }
.qbox2 .qq { font-size: 15.5pt; line-height: 1.25; font-weight: 700; margin-top: 6pt; }
.qbox2 p { font-size: 7.5pt; color: #D8DEE3; margin-top: 8pt; line-height: 1.4; }
.needs2 { position: absolute; left: 512pt; right: 41pt; top: 118pt; height: 278pt; display: flex; flex-direction: column; gap: 9pt; }
.needs2 .need { flex: 1; align-items: center; }
.needs2 .need { padding: 12pt 13pt; }
.aud2 { position: absolute; left: 512pt; right: 41pt; top: 412pt; display: grid; grid-template-columns: 1fr 1fr; gap: 9pt; }
.aud2 div { border-top: 2pt solid #1B2430; padding-top: 5pt; font-size: 7.8pt; color: #5A6370; line-height: 1.4; }
.aud2 b { display: block; color: #1B2430; font-size: 9pt; margin-bottom: 2pt; }
/* ---------- method ---------- */
.srow { position: absolute; left: 43.5pt; right: 41pt; top: 132pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10pt; }
.scard { background: #F4F5F6; padding: 11pt 12pt; height: 104pt; display: flex; flex-direction: column; }
.scard .logo { height: 26pt; display: flex; align-items: center; }
.scard .logo img { max-height: 26pt; max-width: 120pt; }
.scard .wm { font-weight: 700; font-size: 11pt; letter-spacing: .02em; color: var(--wc); display: flex; align-items: center; gap: 5pt; }
.scard .wm i { width: 18pt; height: 18pt; border-radius: 50%; background: var(--wc); display: inline-block; }
.scard b { font-size: 9pt; margin-top: 7pt; }
.scard span { font-size: 7.5pt; color: #5A6370; line-height: 1.35; margin-top: 2pt; }
.scard em { font-style: normal; font-weight: 700; color: #1B2430; }
.rowlab { position: absolute; left: 43.5pt; font-size: 6.5pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5A6370; }
.prep { position: absolute; left: 43.5pt; right: 41pt; top: 264pt; height: 40pt; background: #1B2430; color: #fff; display: grid; grid-template-columns: 90pt repeat(4, 1fr); align-items: center; gap: 10pt; padding: 0 14pt; }
.prep b { font-size: 9.5pt; }
.prep div { font-size: 7.6pt; color: #D8DEE3; line-height: 1.35; }
.prep div i { font-style: normal; color: #FDE725; font-weight: 700; margin-right: 4pt; }
.mrow { position: absolute; left: 43.5pt; right: 41pt; top: 336pt; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10pt; }
.mrow .meas { height: 74pt; }
.orow2 { position: absolute; left: 43.5pt; right: 41pt; top: 440pt; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10pt; }
.orow2 div { border-top: 2pt solid #1B2430; padding-top: 6pt; }
.orow2 b { font-size: 8.8pt; display: block; }
.orow2 span { font-size: 7.4pt; color: #5A6370; line-height: 1.4; display: block; margin-top: 2pt; }
.down { position: absolute; left: 0; right: 0; text-align: center; color: #89949D; font-size: 11pt; }
/* ---------- anatomy strip ---------- */
.astrip { display: grid; grid-template-columns: 12.6pt repeat(3, 188.4pt); column-gap: 14.4pt; margin-top: 4pt; }
.astrip > div { display: grid; grid-template-columns: 1fr 1fr 1.2fr; gap: 4pt; }
.astrip span { background: #F4F5F6; padding: 5pt 6pt; font-size: 6.8pt; color: #5A6370; line-height: 1.25; }
.astrip span b { display: block; font-size: 11pt; color: #1B2430; }
/* ---------- heat table with icons and markers ---------- */
.heat tr:first-child th { vertical-align: bottom; text-align: center; }
.heat tr th:first-child { vertical-align: middle; }
.heat th .hi { display: block; color: #526174; margin-bottom: 2pt; }
.heat th .hi svg { width: 15pt; height: 15pt; }
.heat td { position: relative; }
.heat td .mk { position: absolute; right: 5pt; top: 5pt; }
/* ---------- hunger by region ---------- */
.reg { position: absolute; left: 43.5pt; width: 624.5pt; top: 132pt; display: grid; grid-template-columns: 1fr 1fr; gap: 0 18pt; }
.rcol { display: flex; flex-direction: column; }
.rh { display: flex; justify-content: space-between; align-items: baseline; font-size: 7pt; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
      color: #825578; border-bottom: 1.2px solid #1B2430; padding-bottom: 3pt; margin-top: 6pt; }
.rh span { color: #5A6370; letter-spacing: 0; text-transform: none; font-weight: 400; }
.rr { display: grid; grid-template-columns: 14pt 92pt 1fr 30pt; align-items: center; gap: 5pt; height: 19.2pt; border-bottom: 1px solid #EDF0F3; font-size: 8pt; position: relative; }
.rr.w { font-weight: 700; }
.rr svg { width: 100%; height: 12pt; display: block; }
.rr .chg { text-align: right; font-variant-numeric: tabular-nums; font-size: 7.6pt; }
.rr .chg.up { color: #440154; font-weight: 700; }
.rr .chg.dn { color: #5A6370; font-weight: 400; }
.rr .mk { position: absolute; left: -16pt; }
.rax { display: grid; grid-template-columns: 14pt 92pt 1fr 30pt; gap: 5pt; font-size: 6.5pt; color: #5A6370; margin-top: 2pt; }
.rax svg { width: 100%; height: 10pt; }
.rsum { margin-top: 12pt; background: #F4F5F6; padding: 9pt 11pt; }
.rsum h5 { font-size: 7.5pt; color: #5A6370; font-weight: 400; margin-bottom: 6pt; }
.rsum .r { display: grid; grid-template-columns: 92pt 1fr 46pt; align-items: center; gap: 6pt; font-size: 8pt; margin-top: 4pt; }
.rsum .r i { display: block; height: 9pt; background: #B9C2CA; position: relative; }
.rsum .r i u { position: absolute; left: 0; top: 0; bottom: 0; background: #440154; }
.rsum .r span:last-child { text-align: right; font-weight: 700; }
/* ---------- exporters ---------- */
.cmp2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14pt; margin-top: 6pt; }
.cmp2 > div { background: #F4F5F6; padding: 8pt 10pt; }
.cmp2 h5 { font-size: 7.5pt; color: #5A6370; font-weight: 400; margin-bottom: 4pt; }
.cmp2 .r { display: grid; grid-template-columns: 14pt 70pt 1fr 36pt; align-items: center; gap: 5pt; font-size: 8pt; margin-top: 3pt; }
.cmp2 .r i { display: block; height: 8pt; }
.cmp2 .r span:last-child { text-align: right; font-weight: 700; }
.corr { display: flex; align-items: center; gap: 5pt; font-size: 8pt; color: #5A6370; margin-top: 8pt; }
.corr b { color: #1B2430; }
.globe { width: 11pt; height: 11pt; color: #3B528B; vertical-align: middle; }
/* ---------- rule ---------- */
.rule2 { position: absolute; left: 43.5pt; right: 41pt; top: 118pt; height: 262pt; display: grid; grid-template-columns: 1fr 18pt 1fr 18pt 1fr; }
.rule2 .rstep { padding: 12pt 13pt; }
.rule2 .rstep h3 { margin-top: 7pt; font-size: 12pt; }
.rule2 .rstep p { font-size: 8pt; }
.rule2 .rstep .viz { margin-top: auto; padding-top: 8pt; }
.rule2 .rstep .viz svg { width: 100%; height: auto; display: block; background: #fff; }
.rule2 .rstep.dark .viz svg { background: #2C3846; }
.example2 { position: absolute; left: 43.5pt; right: 41pt; top: 394pt; background: #F6F1E5; border-left: 3pt solid #B89245; padding: 11pt 14pt; display: grid; grid-template-columns: 100pt repeat(4, 1fr); gap: 14pt; align-items: center; }
.example2 .lab { color: #765718; font-weight: 700; font-size: 6.5pt; letter-spacing: .08em; }
.example2 .ex b { display: block; font-size: 17pt; line-height: 1.1; }
.example2 .ex span { font-size: 7.5pt; color: #5A6370; }
.why { position: absolute; left: 43.5pt; right: 41pt; top: 462pt; font-size: 7.8pt; color: #5A6370; }
.why b { color: #1B2430; }
/* ---------- back-test table with inline bars ---------- */
.bt { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
.bt th { font-size: 7pt; font-weight: 700; color: #5A6370; border-bottom: 1.2px solid #1B2430; padding: 0 8pt 4pt 0; text-align: left; }
.bt th.n { text-align: right; }
.bt td { padding: 14pt 8pt 14pt 0; border-bottom: 1px solid #D8DEE3; vertical-align: middle; }
.bt td.n { text-align: right; font-variant-numeric: tabular-nums; width: 40pt; }
.bt td.bcell { width: 92pt; }
.bt .bb { position: relative; height: 11pt; background: #F4F5F6; }
.bt .bb i { position: absolute; left: 0; top: 0; bottom: 0; }
.bt .bb u { position: absolute; top: -3pt; bottom: -3pt; border-left: 1.2px dashed #1B2430; }
.bt td.mkc { width: 16pt; }
/* ---------- today ---------- */
.bar .mkc { position: absolute; left: -16pt; }
.bar { position: relative; }
.gapnote { display: grid; grid-template-columns: 1fr 1fr; gap: 12pt; margin-top: 16pt; }
.gapnote div { background: #F4F5F6; padding: 8pt 10pt; font-size: 7.8pt; color: #5A6370; line-height: 1.4; }
.gapnote b { display: block; font-size: 13pt; color: #1B2430; }
/* ---------- close ---------- */
.cta2 { position: absolute; left: 624pt; right: 41pt; top: 118pt; height: 270pt; background: #1B2430; color: #fff; padding: 16pt; display: flex; flex-direction: column; }
.cta2 h3 { font-size: 15pt; line-height: 1.25; }
.cta2 ul { list-style: none; margin-top: 10pt; font-size: 8pt; color: #D8DEE3; display: flex; flex-direction: column; gap: 5pt; }
.cta2 li::before { content: '→ '; color: #FDE725; }
.cta2 .qr { margin-top: auto; display: flex; align-items: flex-end; gap: 10pt; font-size: 7.5pt; color: #D8DEE3; }
.cta2 .qr div { width: 74pt; height: 74pt; background: #fff; padding: 4pt; flex: none; }
.cta2 .qr svg { width: 100%; height: 100%; display: block; }
.data2 { position: absolute; left: 624pt; right: 41pt; top: 400pt; font-size: 7.5pt; color: #5A6370; line-height: 1.45; }
.data2 h4 { font-size: 6.5pt; letter-spacing: .08em; text-transform: uppercase; color: #1B2430; margin-bottom: 3pt; }
.limits { top: 118pt; }
/* ---------- appendix ---------- */
.road2 .rm { height: 196pt; }
.rphoto { position: absolute; left: 43.5pt; width: 418pt; top: 326pt; height: 162pt; background-size: cover; background-position: center 40%; }
.rphoto .credit { position: absolute; right: 6pt; bottom: 4pt; color: #fff; text-shadow: 0 0 3px rgba(0,0,0,.7); }
.rtake { position: absolute; left: 476pt; right: 41pt; top: 326pt; height: 162pt; background: #F6F1E5; border-left: 3pt solid #B89245; padding: 12pt 14pt; display: flex; flex-direction: column; }
.rtake .lab { color: #765718; font-weight: 700; font-size: 6.5pt; letter-spacing: .08em; }
.rtake p { font-size: 12pt; line-height: 1.35; margin-top: 5pt; }
.rnums { margin-top: auto; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8pt; }
.rnums div { border-top: 1.5pt solid #B89245; padding-top: 5pt; }
.rnums b { display: block; font-size: 15pt; }
.rnums span { font-size: 7pt; color: #5A6370; line-height: 1.3; display: block; }
.appdiv { background: #1B2430; color: #fff; }
.appdiv .ulogo { left: 43.5pt; top: 36pt; width: 40pt; height: 40pt; }
.appdiv small { position: absolute; left: 43.5pt; top: 210pt; font-size: 7pt; font-weight: 700; letter-spacing: .1em; color: #FDE725; }
.appdiv h2 { position: absolute; left: 43.5pt; top: 226pt; font-size: 40pt; }
.appdiv .al { position: absolute; left: 43.5pt; top: 300pt; display: flex; gap: 30pt; font-size: 11pt; color: #D8DEE3; }
.appdiv .al b { color: #fff; margin-right: 8pt; }
.appx2 { position: absolute; left: 43.5pt; right: 41pt; top: 118pt; }
.appx2 .tbl td { font-size: 9.5pt; line-height: 1.45; padding: 11pt 14pt 11pt 0; }
.appx2 .tbl td:first-child { font-weight: 700; width: 120pt; }
.tbl td:first-child { white-space: nowrap; }
"""

ICONS.update({
    "When": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "Where": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    "How big": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>',
    "Review": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>',
    "Next": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>',
})
FOOD_ICONS = {
    "Vegetable oils": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/></svg>',
    "Cereals": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V8"/><path d="M12 8c-2.5-.5-4-2.5-4-5 2.5.5 4 2.5 4 5z"/><path d="M12 8c2.5-.5 4-2.5 4-5-2.5.5-4 2.5-4 5z"/><path d="M12 14c-2.5-.5-4-2.5-4-5 2.5.5 4 2.5 4 5z"/><path d="M12 14c2.5-.5 4-2.5 4-5-2.5.5-4 2.5-4 5z"/></svg>',
    "Dairy": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2h6v3l2 3v13a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V8l2-3z"/><path d="M7 12h10"/></svg>',
    "Sugar": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8l8-4 8 4v8l-8 4-8-4z"/><path d="M4 8l8 4 8-4"/><path d="M12 12v8"/></svg>',
    "Meat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15.4 15.63a7.875 6 135 1 1 6.23-6.23 4.3 3.42 135 0 0-6.23 6.23"/><path d="m8.29 12.71-2.6 2.6a2.5 2.5 0 1 0-1.65 4.65A2.5 2.5 0 1 0 8.7 18.3l2.59-2.59"/></svg>',
    "All food": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10h18l-2 10H5z"/><path d="M8 10l4-6 4 6"/></svg>',
}
GLOBE = ('<svg class="globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/>'
         '<path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>')
ISO2 = {"Madagascar": "mg", "Haiti": "ht", "Niger": "ne", "Central African Republic": "cf", "Papua New Guinea": "pg",
        "Liberia": "lr", "Afghanistan": "af", "Sierra Leone": "sl", "Timor-Leste": "tl", "Benin": "bj", "Mozambique": "mz",
        "Kenya": "ke", "Guinea-Bissau": "gw", "Guinea": "gn", "Congo (Republic of)": "cg", "Djibouti": "dj", "Rwanda": "rw",
        "Zimbabwe": "zw", "Côte d'Ivoire": "ci", "Solomon Islands": "sb", "Australia": "au", "New Zealand": "nz",
        "Dem. Rep. of the Congo": "cd", "Nigeria": "ng", "Angola": "ao"}
REGION = {"Haiti": "Americas", "Papua New Guinea": "Asia and Pacific", "Afghanistan": "Asia and Pacific",
          "Timor-Leste": "Asia and Pacific", "Solomon Islands": "Asia and Pacific"}
SHORT = {"Central African Republic": "Central African Rep.", "Congo (Republic of)": "Rep. of Congo",
         "Dem. Rep. of the Congo": "DR Congo"}
ASSETS = HERE / "assets"
PHOTOS = {  # cropped copies of the photos credited in the appendix (see assets/photos/CREDITS.md)
    "cover": ("photo-peas.jpg", "Photo: DFID, Wikimedia Commons, CC BY 2.0"),
    "question": ("photo-uganda.jpg", "Photo: USAID in Africa, emergency food distribution in a Uganda refugee settlement. Wikimedia Commons, public domain"),
}


def flag(name: str) -> str:
    import base64
    code = ISO2.get(name)
    if not code or not (ASSETS / "flags" / f"{code}.svg").exists():
        return ""
    b64 = base64.b64encode((ASSETS / "flags" / f"{code}.svg").read_bytes()).decode()
    return f'<img class="flag" alt="" src="data:image/svg+xml;base64,{b64}">'


def asset_url(rel: str) -> str:
    return "../../assets/" + rel


def mk(n: int, style: str = "") -> str:
    return f'<span class="mk{" abs" if style else ""}" style="{style}">{n}</span>'


def logo_slot(key: str, wordmark: str, colour: str) -> str:
    for ext in ("svg", "png"):
        p = ASSETS / "logos" / f"{'fao' if key == 'faostat' else key}.{ext}"
        if p.exists():
            return f'<div class="logo"><img alt="{wordmark}" src="{asset_url(f"logos/{p.name}")}"></div>'
    return f'<div class="logo"><span class="wm" style="--wc:{colour}">{wordmark}</span></div>'


def right2(acc_take: str, notes, nxt: str | None = None) -> str:
    body = "".join(f'<div class="note"><span class="m">{i + 1}</span><h4>{esc(h)}</h4><p>{esc(p)}</p></div>'
                   for i, (h, p) in enumerate(notes))
    tail = f'<div class="nxt">→ {esc(nxt)}</div>' if nxt else ""
    return (f'<div class="right"><div class="take"><span class="lab">TAKEAWAY</span>{esc(acc_take)}</div>'
            f'<div class="notes">{body}</div>{tail}</div>')


# --------------------------------------------------------------------------- mini figures for the summary
def mini_area(f: dict) -> str:
    s = DATA["ffpi"]["ffpi_food"].resample("YS").mean()
    W, H, top, bot = 300, 150, 18, 134
    xs = [i / (len(s) - 1) * (W - 20) + 4 for i in range(len(s))]
    y = lambda v: bot - (v / 170) * (bot - top)  # noqa: E731
    pts = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, s.values))
    out = [f'<defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{hc.FOOD}" stop-opacity=".35"/>'
           f'<stop offset="1" stop-color="{hc.FOOD}" stop-opacity="0"/></linearGradient></defs>',
           f'<polygon points="{xs[0]:.1f},{bot} {pts} {xs[-1]:.1f},{bot}" fill="url(#ga)"/>',
           f'<line x1="4" x2="{W - 16}" y1="{y(100):.1f}" y2="{y(100):.1f}" stroke="#89949D" stroke-dasharray="3 3"/>',
           f'<text x="{W - 14}" y="{y(100) + 3:.1f}" class="ml s mute">100</text>',
           f'<polyline points="{pts}" fill="none" stroke="{hc.FOOD}" stroke-width="2.2" stroke-linejoin="round"/>']
    for t, v in DATA["peaks"]:
        i = list(s.index.year).index(t.year)
        out.append(f'<circle cx="{xs[i]:.1f}" cy="{y(s.iloc[i]):.1f}" r="3.5" fill="{hc.FOOD}" stroke="#fff" stroke-width="1.2"/>'
                   f'<text x="{xs[i]:.1f}" y="{y(s.iloc[i]) - 6:.1f}" text-anchor="middle" class="ml b s">{v:.0f}</text>')
    for yr in (1990, 2008, 2026):
        i = list(s.index.year).index(yr)
        out.append(f'<text x="{xs[i]:.1f}" y="{H - 2}" text-anchor="{"start" if yr == 1990 else "end" if yr == 2026 else "middle"}" class="ml s mute">{yr}</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="mini">{"".join(out)}</svg>'


def mini_scatter(f: dict) -> str:
    df, med = DATA["df"], DATA["median_import"]
    W, H, l, b = 300, 150, 6, 136
    x = lambda v: l + min(v, 46) / 46 * (W - 12)  # noqa: E731
    y = lambda v: b - min(v, 46) / 46 * (b - 8)  # noqa: E731
    out = [f'<rect x="{x(med):.1f}" y="{y(46):.1f}" width="{x(46) - x(med):.1f}" height="{y(20) - y(46):.1f}" fill="{hc.EXPOSED_ZONE}"/>',
           f'<line x1="{x(med):.1f}" x2="{x(med):.1f}" y1="{y(46):.1f}" y2="{b}" stroke="#89949D" stroke-dasharray="2 2"/>',
           f'<line x1="{l}" x2="{W - 6}" y1="{y(20):.1f}" y2="{y(20):.1f}" stroke="#89949D" stroke-dasharray="2 2"/>']
    for _, r in df[~df["exposed"]].iterrows():
        out.append(f'<circle cx="{x(r.food_import_pct):.1f}" cy="{y(r.ghi_2025):.1f}" r="2.3" fill="{hc.OTHER}"/>')
    for _, r in df[df["exposed"]].iterrows():
        out.append(f'<circle cx="{x(r.food_import_pct):.1f}" cy="{y(r.ghi_2025):.1f}" r="3" fill="{hc.EXPOSED}" stroke="#fff" stroke-width=".8"/>')
    out.append(f'<text x="{x(med) + 4:.1f}" y="{y(46) + 9:.1f}" class="ml s" style="fill:{hc.EXPOSED}">Exposed zone</text>')
    out.append(f'<text x="{l}" y="{H - 1}" class="ml s mute">Food imports →</text><text x="{W - 6}" y="{y(20) - 3:.1f}" text-anchor="end" class="ml s mute">GHI 20</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="mini">{"".join(out)}</svg>'


def mini_timeline(f: dict) -> str:
    w = f["warning"]
    t0, t1 = pd.Timestamp("2000-01-01"), pd.Timestamp(w["period"][1] + "-01")
    W, H = 300, 150
    X = lambda t: 8 + (pd.Timestamp(t) - t0).days / (t1 - t0).days * (W - 16)  # noqa: E731
    out = [f'<line x1="8" x2="{W - 8}" y1="84" y2="84" stroke="#D8DEE3" stroke-width="1.5"/>']
    for a, b in DATA["shock_eps"]:
        out.append(f'<rect x="{X(a):.1f}" y="58" width="{max(X(b) - X(a), 2):.1f}" height="52" fill="{hc.SHOCK}" opacity=".55"/>')
    for a, _, hit in w["signal_runs"]:
        xa = X(a + "-01")
        if hit:
            xh = X(hit + "-01")
            lead = (pd.Timestamp(hit + "-01").to_period("M") - pd.Timestamp(a + "-01").to_period("M")).n
            out.append(f'<rect x="{xa - 3:.1f}" y="76" width="6" height="16" rx="1.5" fill="{hc.SIGNAL}"/>'
                       f'<text x="{xa:.1f}" y="106" text-anchor="middle" class="ml s b">{lead} mo</text>')
        else:
            out.append(f'<rect x="{xa - 3:.1f}" y="76" width="6" height="16" rx="1.5" fill="#fff" stroke="{hc.SIGNAL}" stroke-width="1.2"/>'
                       f'<text x="{xa - 2:.1f}" y="70" text-anchor="end" class="ml s mute">false alarm</text>')
    for yr in (2000, 2010, 2020):
        out.append(f'<text x="{X(f"{yr}-01-01"):.1f}" y="142" text-anchor="{"start" if yr == 2000 else "middle"}" class="ml s mute">{yr}</text>')
    out.append(f'<rect x="{W - 116}" y="4" width="8" height="8" fill="{hc.SHOCK}" opacity=".7"/><text x="{W - 104}" y="11" class="ml s mute">shock</text>'
               f'<rect x="{W - 66}" y="4" width="5" height="9" fill="{hc.SIGNAL}"/><text x="{W - 57}" y="11" class="ml s mute">signal</text>')
    return f'<svg viewBox="0 0 {W} {H}" class="mini">{"".join(out)}</svg>'


def cover_motif() -> str:
    s = DATA["ffpi"]["ffpi_food"].resample("YS").mean()
    shock_years = {t.year for a, b in DATA["eps"] for t in pd.date_range(a, b, freq="MS")}
    out = []
    for i, (t, v) in enumerate(s.items()):
        n = int(round(v / 10))
        c = "#B89245" if t.year in shock_years else "#32658A"
        for j in range(n):
            out.append(f'<rect x="{i * 9.4:.1f}" y="{150 - (j + 1) * 8.6:.1f}" width="7" height="6.6" rx="2" fill="{c}" opacity="{0.35 + 0.65 * j / 16:.2f}"/>')
    return f'<svg viewBox="0 0 {len(s) * 9.4:.0f} 152">{"".join(out)}</svg>'


def rule_minis(f: dict) -> tuple[str, str, str]:
    yoy = DATA["yoy"]["2005-06":"2008-06"]
    W, H = 240, 120
    X = lambda i: 8 + i / (len(yoy) - 1) * (W - 16)  # noqa: E731
    Y = lambda v: 104 - (max(min(v, 100), -10) + 10) / 110 * 84  # noqa: E731
    lines = ""
    for col, c in (("ffpi_cereals", hc.CEREALS), ("ffpi_oils", hc.OILS)):
        lines += f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(yoy[col].values))}" fill="none" stroke="{c}" stroke-width="1.8"/>'
    i06 = list(yoy.index).index(pd.Timestamp("2006-12-01"))
    a = (f'<svg viewBox="0 0 {W} {H}">'
         f'<rect x="8" y="6" width="10" height="2.5" fill="{hc.OILS}"/><text x="22" y="10" class="ml s">Oils</text>'
         f'<rect x="50" y="6" width="10" height="2.5" fill="{hc.CEREALS}"/><text x="64" y="10" class="ml s">Cereals</text>'
         f'<line x1="8" x2="{W - 8}" y1="{Y(20):.1f}" y2="{Y(20):.1f}" stroke="#1B2430" stroke-dasharray="3 2"/>'
         f'<text x="{W - 8}" y="{Y(20) + 10:.1f}" text-anchor="end" class="ml s b">+20% line</text>{lines}'
         f'<circle cx="{X(i06):.1f}" cy="{Y(yoy["ffpi_oils"].iloc[i06]):.1f}" r="3.5" fill="#B8452E" stroke="#fff"/>'
         f'<text x="{X(i06) - 5:.1f}" y="{Y(yoy["ffpi_oils"].iloc[i06]) - 6:.1f}" text-anchor="end" class="ml s b" style="fill:#B8452E">Dec 2006</text>'
         f'<text x="8" y="{H - 2}" class="ml s mute">Jun 2005</text><text x="{W - 8}" y="{H - 2}" text-anchor="end" class="ml s mute">Jun 2008</text></svg>')
    ex = f["backtest"][2]
    gw, gx = 150, 56

    def gauge(lbl, v, c, yy):
        return (f'<text x="8" y="{yy + 10}" class="ml">{lbl}</text><rect x="{gx}" y="{yy}" width="{gw}" height="14" fill="#F4F5F6"/>'
                f'<rect x="{gx}" y="{yy}" width="{min(v, 45) / 45 * gw:.1f}" height="14" fill="{c}"/>'
                f'<text x="{gx + min(v, 45) / 45 * gw + 4:.1f}" y="{yy + 10}" class="ml b">+{v:.0f}%</text>')
    lx = gx + 20 / 45 * gw
    b = (f'<svg viewBox="0 0 {W} {H}"><text x="8" y="12" class="ml s mute">Dec 2006, change on a year earlier</text>'
         f'{gauge("Oils", ex["oils"], hc.OILS, 26)}{gauge("Cereals", ex["cereals"], hc.CEREALS, 50)}'
         f'<line x1="{lx:.1f}" x2="{lx:.1f}" y1="20" y2="72" stroke="#1B2430" stroke-dasharray="3 2"/>'
         f'<text x="{lx:.1f}" y="84" text-anchor="middle" class="ml s">+20%</text>'
         f'<rect x="8" y="94" width="{W - 16}" height="20" rx="10" fill="#1B2430"/>'
         f'<text x="{W / 2:.0f}" y="108" text-anchor="middle" class="ml b" style="fill:#FDE725">Both past the line: signal</text></svg>')
    c = (f'<svg viewBox="0 0 {W} {H}"><line x1="10" x2="{W - 10}" y1="64" y2="64" stroke="#5A6370" stroke-width="1.5"/>'
         f'<rect x="168" y="44" width="{W - 178}" height="40" fill="{hc.SHOCK}" opacity=".85"/>'
         f'<text x="{(168 + W - 10) / 2:.0f}" y="100" text-anchor="middle" class="ml s" style="fill:#D8DEE3">shock starts</text>'
         f'<rect x="22" y="52" width="8" height="24" rx="1.5" fill="#fff"/><text x="26" y="100" text-anchor="middle" class="ml s" style="fill:#D8DEE3">signal</text>'
         f'<path d="M32,50 Q99,8 166,50" fill="none" stroke="#FDE725" stroke-width="1.6"/>'
         f'<text x="99" y="22" text-anchor="middle" class="ml b" style="fill:#FDE725">1–5 months to prepare</text>'
         f'<text x="99" y="114" text-anchor="middle" class="ml s" style="fill:#89949D">Dec 2006 → May 2007: 5 months</text></svg>')
    return a, b, c


def dumbbell(v16: float, v25: float, worse: bool) -> str:
    X = lambda v: 3 + (min(max(v, 15), 40) - 15) / 25 * 154  # noqa: E731
    c = hc.EXPOSED if worse else hc.OTHER
    return (f'<svg viewBox="0 0 160 12"><line x1="{X(20):.1f}" x2="{X(20):.1f}" y1="0" y2="12" stroke="#D8DEE3" stroke-dasharray="2 2"/>'
            f'<line x1="{X(v16):.1f}" x2="{X(v25):.1f}" y1="6" y2="6" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>'
            f'<circle cx="{X(v16):.1f}" cy="6" r="2.6" fill="#fff" stroke="#5A6370" stroke-width="1"/>'
            f'<circle cx="{X(v25):.1f}" cy="6" r="3.3" fill="{c}"/></svg>')


def dumbbell_axis() -> str:
    X = lambda v: 3 + (v - 15) / 25 * 154  # noqa: E731
    t = "".join(f'<text x="{X(v):.1f}" y="8" text-anchor="{"end" if v == 40 else "start" if v == 15 else "middle"}" class="ml s mute">{v}</text>' for v in (15, 20, 25, 30, 35, 40))
    return f'<div class="rax"><span></span><span>GHI 2016 ○ → ● 2025</span><svg viewBox="0 0 160 10">{t}</svg><span></span></div>'


# --------------------------------------------------------------------------- slides
CHAPTERS = [
    ("shock", "How big are shocks, and what drives them?", "How big", [("Global food prices", 6), ("Anatomy of a shock", 7), ("What drove each shock", 8)]),
    ("exposure", "Who feels a global spike first?", "Where", [("Who feels it first", 9), ("Is it getting worse?", 10), ("The exporters' view", 11)]),
    ("warning", "Can two prices see a shock coming?", "When", [("How the rule works", 12), ("An early signal", 13), ("Back-test", 14), ("Where we are now", 15)]),
    ("next", "What should a food-security team do?", "Next", [("A monthly routine", 16), ("Limits and the dashboard", 17)]),
]


def build_slides(f: dict, c: dict) -> list[str]:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    an, ht, au, now, bt, dd = f["anatomy"], f["hunger_trend"], f["ausnz"], f["now"], f["backtest"], f["data"]
    leads = sorted(w["lead_months"])
    nowy = w["latest_yoy_pct"]
    pages: list[str] = []
    n = lambda: len(pages) + 1  # noqa: E731

    # 1 cover --------------------------------------------------------------
    ph, cr = PHOTOS["cover"]
    kp = [("shock", f"{s['peaks'][2][1]}", f"record food price index, {month(s['peaks'][2][0])}"),
          ("exposure", f"{e['exposed_count']} countries", "with serious hunger and heavy food imports"),
          ("warning", f"{w['followed_by_shock_within_12m']} of {w['signals']}", "two-price signals followed by a shock")]
    pages.append(
        f'<section class="slide cover cv"><div class="ulogo">{logo()}</div><div class="band">'
        f'<div class="lbl">{SUBJECT}</div><div class="ttl">{TITLE[0]}<br>{TITLE[1]}</div>'
        f'<div class="cs">An early-warning story from 36 years of FAO food prices, hunger and trade data.</div></div>'
        f'<div class="who"><b>{AUTHOR}</b><br>{SCHOOL}<br>{DATE}</div>'
        f'<div class="motif">{cover_motif()}<p>FAO Food Price Index, 1990–2026: one column per year, one pill per 10 points; ochre years had shock months.</p></div>'
        f'<div class="photo" style="background-image:url({asset_url("photos/" + ph)})"></div>'
        f'<div class="kpis3">{"".join(f"<div style=--ca:{CH[k][1]}><b>{v}</b><span>{t}</span></div>" for k, v, t in kp)}</div>'
        f'<div class="pcredit">{cr}</div></section>')

    # 2 agenda --------------------------------------------------------------
    cols = ""
    for i, (k, q, ic, items) in enumerate(CHAPTERS):
        lst = "".join(f"<div><span>{esc(t)}</span><i>{p}</i></div>" for t, p in items)
        cols += (f'<div style="--ca:{CH[k][1]};--pale:{CH[k][2]}"><div class="agh"><div class="no">{i + 1}</div>'
                 f'<div class="ic">{ICONS[ic]}</div><h3>{CH[k][0]}</h3><p>{esc(q)}</p></div><div class="agl">{lst}</div></div>')
    pages.append(slide("shock", n(), header("shock", "Agenda", overview=True) +
        '<h1>Four questions, one early-warning routine</h1>'
        '<div class="sub">From what is happening, to who it hurts, to how to see it coming and what to do.</div>'
        f'<div class="agenda2">{cols}</div>'
        '<div class="opening"><b>Opening</b><span>Summary<i>3</i></span><span>The question<i>4</i></span><span>Data and method<i>5</i></span>'
        '<span style="margin-left:auto">Appendix: definitions, sources and credits after slide 17</span></div>'
        f'<div class="bandtake low"><span>THE ANSWER</span>Watch vegetable oils and cereals; when both pass +20%, prepare the {e["exposed_count"]} exposed countries first.</div>'))

    # 3 summary --------------------------------------------------------------
    cards = [
        ("shock", "Food-price shocks keep getting bigger", f"{s['peaks'][2][1]}", f"record index, {month(s['peaks'][2][0])} (2014–16 = 100)",
         mini_area(f), [(f"+{max(a['rise_pct'] for a in an):.0f}%", "largest rise in a shock"), (f"{max(a['months_in_shock'] for a in an)} mo", "longest shock")],
         f"Peaks of {s['peaks'][0][1]}, {s['peaks'][1][1]} and {s['peaks'][2][1]}; still {s['latest'][1]} today."),
        ("exposure", "Hunger and food imports overlap", f"{e['exposed_count']} of {e['countries_plotted']}", "countries in the exposed zone",
         mini_scatter(f), [(str(ht["serious_hunger_count"]), "countries with serious hunger"), (str(ht["worse_count"]), "of the 20 hungrier than 2016")],
         "Serious hunger (GHI 20+) and above-median food imports."),
        ("warning", "Two prices moved first", f"{w['followed_by_shock_within_12m']} of {w['signals']}", "signals followed by a shock",
         mini_timeline(f), [(f"{leads[0]}–{leads[-1]} mo", "warning before a shock"), (f"0 of {w['shock_episodes_since_2000']}", "shocks missed since 2000")],
         "Oils and cereals both 20%+ above a year earlier came before every shock since 2000."),
    ]
    card_html = "".join(
        f'<div class="card2" style="--ca:{CH[k][1]}"><div class="top"><span class="circ">{i + 1}</span><div><div class="lab">{CH[k][0]}</div>'
        f'<h3>{esc(h)}</h3></div></div><div class="num">{num}</div><div class="unit">{unit}</div>{fig}'
        f'<div class="stats">{"".join(f"<div><b>{v}</b><span>{t}</span></div>" for v, t in st)}</div><p>{esc(p)}</p></div>'
        for i, (k, h, num, unit, fig, st, p) in enumerate(cards))
    pages.append(slide("shock", n(), header("shock", "Summary", overview=True) +
        '<h1>Food-price shocks are growing, and two prices warn of them early</h1>'
        '<div class="sub">What 36 years of FAO prices, the 2025 Global Hunger Index and World Bank trade data show.</div>'
        f'<div class="cards2">{card_html}</div>'
        f'<div class="bandtake" style="top:446pt"><span>TAKEAWAY</span>{esc(f"No warning signal in {month(nowy["month"])}: oils +{nowy["oils"]:.0f}%, cereals +{nowy["cereals"]:.0f}%. Watch both monthly.")}</div>'))

    # 4 question -------------------------------------------------------------
    ph, cr = PHOTOS["question"]
    needs = [
        ("warning", "When", "When will prices spike?", "A signal that comes before the shock, from numbers FAO publishes every month.", "slides 12–15"),
        ("exposure", "Where", "Where will it hurt most?", f"A short list of countries where serious hunger meets heavy food imports: {e['exposed_count']} today.", "slides 9–11"),
        ("shock", "How big", "How big can it get?", f"How far prices rose in past shocks (up to +{max(a['rise_pct'] for a in an):.0f}%) and how long they stayed high.", "slides 6–8"),
    ]
    need_html = "".join(
        f'<div class="need" style="--ca:{CH[k][1]}"><div class="ic">{ICONS[ic]}</div><div><small>{CH[k][0]} · {sl}</small>'
        f'<h3>{esc(h)}</h3><p>{esc(p)}</p></div></div>' for k, ic, h, p, sl in needs)
    pages.append(slide("shock", n(), header("shock", "The question", overview=True) +
        '<h1>A food-security board needs to know when to act, and where</h1>'
        '<div class="sub">One decision question for the people who fund and plan food support.</div>'
        f'<div class="qphoto" style="background-image:url({asset_url("photos/" + ph)})"><span class="credit">{cr}</span></div>'
        '<div class="qbox2"><small>THE QUESTION</small><div class="qq">When global food prices spike, which countries feel it first, '
        'and can we see it coming?</div><p>A sparkline story: from what is (price stress today) to what could be (support in place before the next shock).</p></div>'
        f'<div class="needs2">{need_html}</div>'
        '<div class="aud2"><div><b>Who it is for</b>A UN food-systems panel or a regional food-security policy board.</div>'
        '<div><b>What they decide</b>Which countries to watch, and when to move money and supplies.</div></div>'))

    # 5 data and method --------------------------------------------------------
    srcs = [
        ("fao", "FAO", "#1F5BA8", "FAO Food Price Index", f"Monthly, <em>{dd['months']} months</em> ({month(s['series_start'])}–{month(s['latest'][0])}); all food and five groups."),
        ("ghi", "Global Hunger Index", "#C0392B", "Global Hunger Index 2025", f"<em>{dd['ghi_countries']} countries</em> scored; 2000, 2008 and 2016 for trends."),
        ("worldbank", "The World Bank", "#0071BC", "World Bank food imports", f"Food as % of merchandise imports; latest year {e['import_year_min']}–{e['import_year_max']}."),
        ("faostat", "FAOSTAT", "#1F5BA8", "FAOSTAT producer prices", f"Australia and New Zealand, <em>{au['items']} farm products</em>, {au['years'][0]}–{au['years'][1]}."),
    ]
    src_html = "".join(f'<div class="scard">{logo_slot(k, wm, col)}<b>{nm}</b><span>{dt}</span></div>' for k, wm, col, nm, dt in srcs)
    meas = [
        ("shock", "Measure 1", "Shock month", f"All-food index more than <b>{s['threshold_yoy_pct']:.0f}%</b> above the same month a year earlier."),
        ("exposure", "Measure 2", "Exposed country", f"GHI <b>20+</b> (serious hunger) and food imports above the <b>{e['median_food_import_pct']}%</b> median."),
        ("warning", "Measure 3", "Two-price signal", "Vegetable oils <b>and</b> cereals both 20%+ above a year earlier, before a shock starts."),
    ]
    meas_html = "".join(f'<div class="meas" style="--ca:{CH[k][1]}"><small>{a}</small><h4>{b}</h4><p>{p}</p></div>' for k, a, b, p in meas)
    pages.append(slide("shock", n(), header("shock", "Data and method", overview=True) +
        '<h1>Four public datasets, joined by country, give three simple measures</h1>'
        '<div class="sub">Every number in this deck is computed from these files by one script, so it can be checked and rerun.</div>'
        f'<div class="rowlab" style="top:120pt">1 · Sources</div><div class="srow">{src_html}</div>'
        '<div class="rowlab" style="top:252pt">2 · Prepare</div>'
        '<div class="prep"><b>Clean and join</b><div><i>a</i>Match countries by ISO3 code</div><div><i>b</i>Monthly prices to change on a year earlier</div>'
        '<div><i>c</i>Flag estimates; drop outlier farm prices</div><div><i>d</i>Keep import shares from 2015 or later</div></div>'
        f'<div class="rowlab" style="top:324pt">3 · Measures</div><div class="mrow">{meas_html}</div>'
        '<div class="rowlab" style="top:428pt">4 · Outputs</div><div class="orow2">'
        '<div><b>Streamlit dashboard</b><span>Six tabs, from the brief to the evidence base, with what-if controls</span></div>'
        '<div><b>Looker Studio dashboard</b><span>Price history, peaks and a hunger map for quick sharing</span></div>'
        '<div><b>This deck and an A1 poster</b><span>Built by one script from the same processed data</span></div>'
        '<div><b>findings.json</b><span>Every number on these slides, saved for checking</span></div></div>'))

    # 6 shock -----------------------------------------------------------------
    cs = c["shock"]
    notes6 = cs["notes"] + [("Two one-month blips", "Jul 1995 and Apr 2004 crossed the line for a single month; shaded, not counted as major shocks.")]
    pages.append(slide("shock", n(), header("shock", "Global food prices") +
        f'<h1>{esc(cs["title"])}</h1><div class="sub">{esc(cs["subtitle"])}</div>'
        f'<div class="left">{legend(cs["legend"])}<div class="fig">{svg("shock", 624.5, 322, 9, markers=True)}</div>'
        f'<div class="src">{esc(cs["source"])}</div></div>'
        + right2(cs["take"], notes6, "Next: what each shock looked like up close")))

    # 7 anatomy ---------------------------------------------------------------
    strip = "<i></i>"
    for a in an:
        back = (f"{a['months_to_base']} months" if a["back_to_base"] else ("Not yet" if a is an[-1] else "Never"))
        strip += (f'<div><span><b>+{a["rise_pct"]:.0f}%</b>rise</span><span><b>{a["months_in_shock"]} mo</b>in shock</span>'
                  f'<span><b>{back}</b>back to start level</span></div>')
    pages.append(slide("shock", n(), header("shock", "Anatomy of a shock") +
        '<h1>Prices fell after each peak, but only once came back to where the shock began</h1>'
        '<div class="sub">All-food index around each major shock, against its level twelve months before the shock started.</div>'
        f'<div class="left">{legend([("band", hc.SHOCK, "Shock months"), ("line", hc.FOOD, "All-food index"), ("line", hc.RULE, "Level a year before the shock")])}'
        f'<div class="fig">{svg("anatomy", 624.5, 262, 9)}</div><div class="astrip">{strip}</div>'
        '<div class="src"><b>Source:</b> FAO Food Price Index, monthly. Rise: peak against the level twelve months before the first shock month.</div></div>'
        + right2(f"Each shock resets the floor. After 2008 the index never fell back to {an[0]['base']:.0f}; today it is {s['latest'][1]}.",
                 [(f"2008: a floor of {an[0]['base']:.0f} never seen again", f"The low after the peak was {an[0]['low_after']}, still {an[0]['low_after'] - an[0]['base']:.0f} points above where the shock began."),
                  ("2010–11: the fastest climb", f"{an[1]['months_to_peak']} months from the first shock month to the peak; back to its start level after {an[1]['months_to_base']} months."),
                  ("2021–22: still above its start", f"{s['latest'][1]} in {month(s['latest'][0])}, {s['latest'][1] - an[2]['base']:.0f} points above the {an[2]['base']:.0f} where it began.")],
                 "Next: which food groups drove each shock")))

    # 8 drivers ---------------------------------------------------------------
    import matplotlib as mpl
    d8 = f["drivers"]
    cmap = mpl.colormaps["viridis"]
    head = "".join(f'<th><span class="hi">{FOOD_ICONS[g]}</span>{g}</th>' for g in d8["groups"])
    marks8 = {(2, "Vegetable oils"): 1, (1, "Cereals"): 2, (0, "Dairy"): 3}
    body = ""
    for ri, r in enumerate(d8["rows"]):
        top = max(r["values"][:-1])
        cells = ""
        for g, v in zip(d8["groups"], r["values"]):
            rgba = cmap(min(v, 130) / 130)
            light = (0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]) > 0.55
            m = mk(marks8[(ri, g)]) if (ri, g) in marks8 else ""
            cells += (f'<td{" class=lead" if v == top else ""} style="background:{mpl.colors.to_hex(rgba)};color:{INK if light else "#fff"}">'
                      f'+{v:.0f}%{m}</td>')
        body += f'<tr><th>{r["shock"]}</th>{cells}</tr>'
    stops = ", ".join(mpl.colors.to_hex(cmap(i / 8)) for i in range(9))
    heat = (f'<table class="heat"><tr><th></th>{head}</tr>{body}</table><div class="hscale"><span>0%</span>'
            f'<i style="background:linear-gradient(90deg,{stops})"></i><span>+130%</span>'
            f'<em>Largest rise on a year earlier during the shock; outlined: the group that rose most</em></div>')
    cd = c["drivers"]
    pages.append(slide("shock", n(), header("shock", "What drove each shock") +
        f'<h1>{esc(cd["title"])}</h1><div class="sub">{esc(cd["subtitle"])}</div>'
        f'<div class="left">{heat}<div class="src">{esc(cd["source"])}</div></div>'
        + right2(cd["take"], cd["notes"], "Next: which countries feel a spike first")))

    # 9 exposure ----------------------------------------------------------------
    ce = c["exposure"]
    hl = ht["high_hunger_low_import"]
    ex0 = e["exposed"]
    gb = next(x for x in ex0 if x[0] == "Guinea-Bissau")
    pages.append(slide("exposure", n(), header("exposure", "Who feels it first") +
        f'<h1>{esc(ce["title"])}</h1><div class="sub">{esc(ce["subtitle"])}</div>'
        f'<div class="left">{legend(ce["legend"])}<div class="fig">{svg("exposure", 624.5, 322, 9, labels=[x[0] for x in ex0[:10]] + ["Guinea-Bissau", "Djibouti"], marks=True)}</div>'
        f'<div class="src">{esc(ce["source"])}</div></div>'
        + right2(ce["take"],
                 [(f"Hungriest: {ex0[0][0]} and {ex0[1][0]}", f"GHI {ex0[0][2]} and {ex0[1][2]}; {ex0[1][0]} also buys {ex0[1][1]:.0f}% of its imports as food."),
                  (f"Most import-reliant: {gb[0]}", f"Food is {gb[1]:.1f}% of its merchandise imports, the highest of the 20."),
                  ("Hungry but less exposed", f"{SHORT.get(hl[0], hl[0])}, {hl[1]} and {hl[2]} have serious hunger but import little food, so world prices reach them less directly.")],
                 "Next: are these countries getting better or worse?")))

    # 10 hunger by region --------------------------------------------------------
    hx = DATA["hunger"].copy()
    hx["region"] = hx["country_ghi"].map(lambda c_: REGION.get(c_, "Sub-Saharan Africa"))
    marks10 = {"Haiti": 1, "Kenya": 2, "Benin": 2, "Mozambique": 3}

    def rows(df_):
        out = ""
        for _, r in df_.sort_values("ghi_2025", ascending=False).iterrows():
            wz = r["change"] > 0
            m = mk(marks10[r["country_ghi"]]) if r["country_ghi"] in marks10 and r["country_ghi"] != "Benin" else ""
            out += (f'<div class="rr{" w" if wz else ""}">{m}{flag(r["country_ghi"])}<span>{SHORT.get(r["country_ghi"], r["country_ghi"])}</span>'
                    f'{dumbbell(r["ghi_2016"], r["ghi_2025"], wz)}<span class="chg {"up" if wz else "dn"}">{r["change"]:+.1f}</span></div>')
        return out

    def region_block(name):
        df_ = hx[hx["region"] == name]
        nw = int((df_["change"] > 0).sum())
        return f'<div class="rh">{name} · {len(df_)}<span>{nw} hungrier</span></div>{rows(df_)}'
    summ = ""
    for name in ("Sub-Saharan Africa", "Asia and Pacific", "Americas"):
        df_ = hx[hx["region"] == name]
        nw = int((df_["change"] > 0).sum())
        summ += f'<div class="r"><span>{name}</span><i style="width:{len(df_) / 15 * 100:.0f}%"><u style="width:{nw / len(df_) * 100:.0f}%"></u></i><span>{nw} of {len(df_)}</span></div>'
    wz = ht["worse"]
    imp = lambda c_: float(hx.loc[hx["country_ghi"] == c_, "food_import_pct"].iloc[0])  # noqa: E731
    ghi25 = lambda c_: float(hx.loc[hx["country_ghi"] == c_, "ghi_2025"].iloc[0])  # noqa: E731
    pages.append(slide("exposure", n(), header("exposure", "Is it getting worse?") +
        f'<h1>{ht["worse_count"]} of the {ht["of"]} exposed countries are hungrier than in 2016, Haiti most of all</h1>'
        '<div class="sub">Global Hunger Index in 2016 and 2025 for the exposed countries, grouped by region, highest hunger first.</div>'
        f'<div class="reg"><div class="rcol">{dumbbell_axis()}{region_block("Sub-Saharan Africa")}</div>'
        f'<div class="rcol">{dumbbell_axis()}{region_block("Asia and Pacific")}{region_block("Americas")}'
        f'<div class="rsum"><h5>Exposed countries by region; purple share is hungrier than in 2016</h5>{summ}</div></div></div>'
        '<div class="left" style="top:auto;height:20pt"><div class="src"><b>Source:</b> Global Hunger Index 2016 and 2025 (20+ is serious). Flags: flag-icons (MIT).</div></div>'
        + right2("A third of the list is moving the wrong way, so the watch list needs a yearly refresh.",
                 [(f"{wz[0][0]}: +{wz[0][3]}", f"From **{wz[0][1]}** to **{wz[0][2]}**, the largest rise, and it buys {imp(wz[0][0]):.0f}% of its imports as food."),
                  (f"{wz[1][0]} and {wz[2][0]}", f"Up {wz[1][3]} and {wz[2][3]} points, both now at {wz[1][2]}."),
                  (f"{ht['most_improved'][0]}: {ht['most_improved'][1]:+.1f}", f"The largest fall of the 20, yet still in the serious band at {ghi25(ht['most_improved'][0]):.1f}.")],
                 "Next: what a spike looks like for big food exporters")))

    # 11 exporters ----------------------------------------------------------------
    c08, c22 = au["change_2008"], au["change_2022"]

    def cmpblock(title, ch):
        mx = max(ch.values())
        r = ""
        for k, col, icon in (("World", hc.FOOD, GLOBE), ("Australia", INK, flag("Australia")), ("New Zealand", hc.RULE, flag("New Zealand"))):
            r += f'<div class="r">{icon}<span>{k}</span><i style="width:{ch[k] / mx * 100:.0f}%;background:{col}"></i><span>+{ch[k]:.1f}%</span></div>'
        return f'<div><h5>{title}</h5>{r}</div>'
    leg11 = (f'<div class="legend"><span class="key">{GLOBE}<i class="k-line" style="--c:{hc.FOOD}"></i>World food prices (FAO)</span>'
             f'<span class="key">{flag("Australia")}<i class="k-line" style="--c:{INK}"></i>Australia farm prices</span>'
             f'<span class="key">{flag("New Zealand")}<i class="k-line" style="--c:{hc.RULE}"></i>New Zealand farm prices</span>'
             f'<span class="key"><i class="k-band" style="--c:{hc.SHOCK}"></i>Shock years</span></div>')
    pages.append(slide("exposure", n(), header("exposure", "The exporters' view") +
        '<h1>Australian and New Zealand farm prices barely felt the world spikes</h1>'
        f'<div class="sub">World food prices against the median farm-gate price index of {au["items"]} products, {au["years"][0]}–{au["years"][1]}.</div>'
        f'<div class="left">{leg11}<div class="fig">{svg("ausnz", 624.5, 236, 9)}</div>'
        f'<div class="cmp2">{cmpblock("Change on the year before, 2008", c08)}{cmpblock("Change on the year before, 2022", c22)}</div>'
        f'<div class="corr">{mk(4)} Year-to-year correlation with world prices: {flag("Australia")} Australia <b>{au["corr_with_world"]["Australia"]}</b> · '
        f'{flag("New Zealand")} New Zealand <b>{au["corr_with_world"]["New Zealand"]}</b> (1 would mean they move together)</div>'
        '<div class="src"><b>Sources:</b> FAO Food Price Index (annual mean); FAOSTAT producer price indices (2014–16 = 100), median across products, outliers removed.</div></div>'
        + right2("Big exporters are buffered. A world spike lands on the countries that buy their food abroad.",
                 [("2008: a third of the world rise", f"World +{c08['World']:.1f}%; Australia +{c08['Australia']:.1f}%, New Zealand +{c08['New Zealand']:.1f}%."),
                  ("2022: almost flat at the farm gate", f"World +{c22['World']:.1f}%; Australia +{c22['Australia']:.1f}%, New Zealand +{c22['New Zealand']:.1f}%."),
                  ("A slow, steady climb instead", f"Australia rose from {DATA['ausnz'].loc[2014, 'Australia']:.0f} in 2014 to {DATA['ausnz']['Australia'].iloc[-1]:.0f} in {au['years'][1]}, without the spikes."),
                  ("A weak year-to-year link", f"Correlation with world prices: {au['corr_with_world']['Australia']} (Australia), {au['corr_with_world']['New Zealand']} (New Zealand). Exposure is about imports.")],
                 "Next: how to see a spike coming")))

    # 12 how the rule works ----------------------------------------------------------
    va, vb, vc = rule_minis(f)
    ex = bt[2]
    pages.append(slide("warning", n(), header("warning", "How the rule works") +
        '<h1>The warning needs two numbers a month and one line at +20%</h1>'
        '<div class="sub">Anyone can check it from the FAO release, without a model.</div>'
        '<div class="rule2">'
        f'<div class="rstep"><div class="no">1</div><h3>Read two prices</h3><p>Each month, compare vegetable oils and cereals with the same month a year earlier.</p><div class="viz">{va}</div></div>'
        '<div class="arrow">→</div>'
        f'<div class="rstep"><div class="no">2</div><h3>Both above +20%?</h3><p>The signal fires only when both pass the line before a shock has started. One alone is not enough.</p><div class="viz">{vb}</div></div>'
        '<div class="arrow">→</div>'
        f'<div class="rstep dark"><div class="no">3</div><h3>Prepare the {e["exposed_count"]} countries</h3><p>Since 2000 a shock followed {w["followed_by_shock_within_12m"]} of {w["signals"]} signals, {leads[0]} to {leads[-1]} months later: the window to move support.</p><div class="viz">{vc}</div></div>'
        '</div>'
        f'<div class="example2"><span class="lab">WORKED EXAMPLE</span>'
        f'<div class="ex"><b>{month(ex["start"])}</b><span>Signal month</span></div>'
        f'<div class="ex"><b>+{ex["oils"]:.0f}%</b><span>Vegetable oils on a year earlier</span></div>'
        f'<div class="ex"><b>+{ex["cereals"]:.0f}%</b><span>Cereals on a year earlier</span></div>'
        f'<div class="ex"><b>{ex["lead"]} months</b><span>until the 2007–08 crisis began ({month(ex["shock_start"])})</span></div></div>'
        '<div class="why"><b>Why these two?</b> In every major shock either oils or cereals rose most (slide 8), and both are traded worldwide, so they move before the full basket does.</div>'))

    # 13 warning chart ------------------------------------------------------------------
    cw = c["warning"]
    pages.append(slide("warning", n(), header("warning", "An early signal") +
        f'<h1>{esc(cw["title"])}</h1><div class="sub">{esc(cw["subtitle"])}</div>'
        f'<div class="left">{legend(cw["legend"])}<div class="fig">{svg("warning", 624.5, 322, 9, marks=True)}</div>'
        f'<div class="src">{esc(cw["source"])}</div></div>'
        + right2(cw["take"],
                 [(f"Dec 2006: {ex['lead']} months ahead", f"Oils +{ex['oils']:.0f}% and cereals +{ex['cereals']:.0f}%; the 2007–08 crisis began in {month(ex['shock_start'])}."),
                  ("2002: the one false alarm", "Both prices passed +20% for three months, but the all-food index did not follow."),
                  ("Mar 2026: oils rising, cereals flat", f"Oils +{nowy['oils']:.0f}% and cereals +{nowy['cereals']:.0f}%: no signal yet.")],
                 "Next: the full back-test")))

    # 14 back-test -------------------------------------------------------------------------
    rows14 = ""
    for i, r in enumerate(bt):
        hit = r["lead"] is not None
        m = mk(1) if r["start"] == "2006-12" else mk(2) if not hit else mk(3) if r["start"] == "2004-03" else ""

        def bar(v, col):
            return f'<div class="bb"><i style="width:{min(v, 40) / 40 * 100:.0f}%;background:{col}"></i><u style="left:50%"></u></div>'
        lead = (f'<div class="bb"><i style="width:{r["lead"] / 6 * 100:.0f}%;background:#1B2430"></i></div>' if hit else "")
        rows14 += (f'<tr><td class="mkc">{m}</td><td><b>{month(r["start"])}</b></td><td class="n">+{r["oils"]:.1f}%</td><td class="bcell">{bar(r["oils"], hc.OILS)}</td>'
                   f'<td class="n">+{r["cereals"]:.1f}%</td><td class="bcell">{bar(r["cereals"], hc.CEREALS)}</td>'
                   f'<td>{month(r["shock_start"]) if hit else "None in 12 months"}</td><td class="n">{f"{r['lead']} mo" if hit else "–"}</td><td class="bcell" style="width:60pt">{lead}</td>'
                   f'<td>{"<span class=\"pill hit\">Hit</span>" if hit else "<span class=\"pill miss\">False alarm</span>"}</td></tr>')
    kp = (f'<div class="kpis"><div class="kpi"><div class="v">{w["followed_by_shock_within_12m"]} of {w["signals"]}</div><div class="u">signals followed by a shock within 12 months</div></div>'
          f'<div class="kpi"><div class="v">{leads[0]}–{leads[-1]} mo</div><div class="u">warning before the shock began</div></div>'
          f'<div class="kpi"><div class="v">0 of {w["shock_episodes_since_2000"]}</div><div class="u">shocks since 2000 that came without a signal</div></div></div>')
    pages.append(slide("warning", n(), header("warning", "Back-test") +
        '<h1>Every shock since 2000 had a signal first; one signal had no shock</h1>'
        '<div class="sub">Each two-price signal since January 2000, the price moves that set it off, and what followed. Dashed line: +20%.</div>'
        f'<div class="left">{kp}<table class="bt"><tr><th></th><th>Signal month</th><th class="n">Oils</th><th></th><th class="n">Cereals</th><th></th>'
        f'<th>Shock began</th><th class="n">Lead</th><th></th><th>Result</th></tr>{rows14}</table>'
        '<div class="src"><b>Source:</b> FAO Food Price Index, monthly, Jan 2000 to Mar 2026. Signal and shock as defined on slide 5. Bars: 0 to +40% (prices), 0 to 6 months (lead).</div></div>'
        + right2("The rule caught every shock since 2000, but it was read off the same history.",
                 [("Lead times are short", f"{leads[0]} to {leads[-1]} months is enough to plan, not to build new programmes."),
                  ("False alarm in 2002", "Both prices passed +20% for three months, but the all-food index did not follow."),
                  ("A one-month shock in 2004", "The April 2004 hit led into a single shock month; the other three led into the major shocks.")],
                 "Next: where prices stand today")))

    # 15 today ------------------------------------------------------------------------------
    gr = now["groups"]
    lo, hi = -30, 30
    xp = lambda v: (min(max(v, lo), hi) - lo) / (hi - lo) * 100  # noqa: E731
    colmap = {"Vegetable oils": hc.OILS, "Cereals": hc.CEREALS, "All food": hc.FOOD}
    marks15 = {"Vegetable oils": 1, "Cereals": 2, "All food": 3}
    bars = ""
    for name, y, lvl in gr:
        a_, b_ = sorted([xp(0), xp(y)])
        m = mk(marks15[name], "left:-17pt") if name in marks15 else ""
        bars += (f'<div class="bar">{m}<span>{FOOD_ICONS[name].replace("<svg", "<svg class=ico")} {"<b>" + name + "</b>" if name in colmap else name}</span>'
                 f'<div class="tr"><s style="left:{xp(0):.1f}%"></s><i style="left:{a_:.1f}%;width:{b_ - a_:.1f}%;background:{colmap.get(name, hc.OTHER)}"></i>'
                 f'<u style="left:{xp(20):.1f}%"></u></div><b>{y:+.1f}%</b><em>{lvl:.1f}</em></div>')
    ticks = "".join(f'<span style="left:{xp(v):.1f}%">{f"{v:+d}%" if v else "0"}</span>' for v in (-30, -20, -10, 0, 10, 20, 30))
    oils = next(g for g in gr if g[0] == "Vegetable oils")
    cer = next(g for g in gr if g[0] == "Cereals")
    need = lambda g: g[2] / (1 + g[1] / 100) * 1.2  # noqa: E731
    pages.append(slide("warning", n(), header("warning", "Where we are now") +
        f'<h1>No signal in {month(now["month"])}, but vegetable oils are already at {oils[2]:.0f}</h1>'
        f'<div class="sub">Change on a year earlier for each FAO food group, {month(now["month"])}, against the +20% signal line.</div>'
        f'<div class="left"><div class="barhead"><span>Food group</span><span>Change on a year earlier (dashed line: +20%)</span><span>Change</span><span>Index</span></div>'
        f'<div class="bars">{bars}</div><div class="axisl">{ticks}</div>'
        f'<div class="gapnote"><div><b>{20 - oils[1]:.1f} points</b>more year-on-year rise needed for vegetable oils to reach the line</div>'
        f'<div><b>{20 - cer[1]:.1f} points</b>more for cereals; the signal needs both</div></div>'
        f'<div class="src"><b>Source:</b> FAO Food Price Index, {month(now["month"])}. Index: 2014–16 = 100.</div></div>'
        + right2("Oils are two-thirds of the way to the line; cereals are flat. Both must pass +20% for a signal.",
                 [("Oils are the highest group", f"Index **{oils[2]:.1f}**, up {oils[1]:.1f}% on a year earlier."),
                  ("Cereals are the brake", f"Up only {cer[1]:.1f}%. At today's year-ago levels the signal needs oils above **{need(oils):.0f}** and cereals above **{need(cer):.0f}**."),
                  ("All food is steady", f"**{s['latest'][1]}**, {now['below_record_pct']:.0f}% below the 2022 record but {now['above_base_pct']:.0f}% above 2014–16.")],
                 "Next: turning this into a routine")))

    # 16 roadmap ------------------------------------------------------------------------------
    wz = ht["worse"]
    road = [
        ("warning", "Every month", "Monitor", "Check oils and cereals", "Compare both with a year earlier when the FAO index is released early each month.", "Analyst, 15 minutes", "Input: two numbers from the FAO release"),
        ("exposure", "When the signal fires", "Prepare", f"Move the {e['exposed_count']} countries forward", "Start with the hungriest importers: Madagascar, Haiti, Niger.", "Programme leads", "Trigger: oils and cereals both above +20%"),
        ("shock", "Every year", "Review", "Refresh the watch list", f"Add new hunger and import data; {wz[0][0]}, {wz[1][0]} and {wz[2][0]} are trending worse.", "Policy board", "Trigger: each new Global Hunger Index"),
        ("next", "Before relying on it", "Test", "Back-test on unseen years", "Fix the rule on data to 2012 and score it on 2013 onwards.", "Data team", "Output: an honest hit rate on unseen shocks"),
    ]
    road_html = "".join(
        f'<div class="rm" style="--ca:{CH[k][1]}"><div class="when">{when}</div><div class="ic">{ICONS[ic]}</div>'
        f'<h3>{esc(h)}</h3><p>{esc(p)}</p><div class="trig">{esc(tg)}</div><div class="who"><b>Owner:</b> {who}</div></div>'
        for k, when, ic, h, p, who, tg in road)
    pages.append(slide("next", n(), header("next", "A monthly routine") +
        '<h1>A monthly check, a clear trigger and a yearly refresh</h1>'
        '<div class="sub">Four steps that turn the charts into an early-warning routine.</div>'
        f'<div class="road road2" style="top:118pt">{road_html}</div>'
        f'<div class="rphoto" style="background-image:url({asset_url("photos/photo-sacks.jpg")})"><span class="credit">Photo: Department of Foreign Affairs and Trade (Australia), Zimbabwe food distribution. Wikimedia Commons, CC BY 2.0</span></div>'
        f'<div class="rtake"><span class="lab">TAKEAWAY</span><p>Watch two prices monthly; when both pass +20%, the {e["exposed_count"]} exposed countries go first.</p>'
        f'<div class="rnums"><div><b>2</b><span>prices to read each month</span></div><div><b>+20%</b><span>the line both must pass</span></div>'
        f'<div><b>{leads[0]}–{leads[-1]} mo</b><span>to move food and money</span></div><div><b>{e["exposed_count"]}</b><span>countries to prepare first</span></div></div></div>'))

    # 17 limits and dashboard -------------------------------------------------------------------
    lims = [
        ("The rule was read off its own history", "The +20% line and the two prices were chosen by looking at 2000–2026, so the 4 of 5 score is in-sample. **A test on unseen years comes first.**"),
        ("Snapshots, not live data", f"Hunger is one 2025 score and import shares are the latest year from {e['import_year_min']}–{e['import_year_max']}. **Exposure can change faster than the data.**"),
        ("World prices are not shop prices", "Local currency, subsidies and stocks change how much of a world spike reaches a household. **Local price data would sharpen the list.**"),
    ]
    lim_html = "".join(f'<div class="lim"><div class="no">{i + 1}</div><div><h3>{esc(h)}</h3><p>{esc(p)}</p></div></div>' for i, (h, p) in enumerate(lims))
    pages.append(slide("next", n(), header("next", "Limits and the dashboard") +
        '<h1>Three limits to keep in mind, and where to explore the data</h1>'
        '<div class="sub">What the evidence can and cannot support, and the interactive version of this story.</div>'
        f'<div class="limits">{lim_html}</div>'
        '<div class="bandtake" style="top:392pt;right:auto;width:560pt;height:auto;padding:10pt 0"><span>IN SHORT</span>The signal is a prompt to prepare, not a forecast. Test it on unseen years before money depends on it.</div>'
        f'<div class="cta2"><h3>Explore the interactive dashboard</h3><ul><li>Executive brief and shock context</li><li>Producer signal for Australia and New Zealand</li>'
        f'<li>Vulnerability ranking with adjustable weights</li><li>What-if scenarios and the evidence base</li></ul>'
        f'<div class="qr"><div>{qr_svg(APP_URL)}</div><span>assignment3-faostat-viz.streamlit.app</span></div></div>'
        f'<div class="data2"><h4>Code and data</h4>{REPO_URL}<br>Every figure is rebuilt from the processed data by one script.</div>'))

    # appendix ------------------------------------------------------------------------------------
    defs = [
        ("Shock month", f"All-food index more than {s['threshold_yoy_pct']:.0f}% above the same month a year earlier. Runs with gaps of up to three months are joined; runs longer than six months are major shocks."),
        ("Two-price signal", "Vegetable oils and cereals both more than 20% above a year earlier, in a month that is not already a shock month. A hit is a shock starting within 12 months."),
        ("Exposed country", f"GHI 2025 of 20 or more and a food import share above the {e['median_food_import_pct']}% median: {e['exposed_count']} of {e['countries_plotted']} countries."),
        ("Global Hunger Index", "Combines undernourishment, child stunting, child wasting and child mortality. 20–34.9 is serious; 35–49.9 is alarming."),
        ("Food import share", f"World Bank: food imports as % of merchandise imports, latest year from {e['import_year_min']} per country."),
        ("Farm-gate prices", f"FAOSTAT producer price index for Australia and New Zealand, median across {au['items']} products per year; flagged outliers removed."),
    ]
    rows_a = "".join(f"<tr><td>{a}</td><td>{esc(b)}</td></tr>" for a, b in defs)
    pages.append('<section class="slide appdiv"><div class="ulogo">' + logo() + '</div><small>SUPPORTING MATERIAL</small><h2>Appendix</h2>'
                 '<div class="al"><div><b>A1</b>Definitions</div><div><b>A2</b>Sources and credits</div></div></section>')
    pages.append(slide("next", "A1", header("next", "Definitions", overview=True).replace(">Overview<", ">Appendix<") +
        '<h1>Definitions</h1><div class="sub">The thresholds behind every measure in the main story.</div>'
        f'<div class="appx2"><table class="tbl">{rows_a}</table></div>'))
    srcs_a = [
        ("FAO Food Price Index", "FAO, monthly real and nominal indices, 2014–16 = 100 (data/raw/fao_food_price_index.xlsx)."),
        ("FAOSTAT producer prices", "FAO, Producer Prices domain, Australia and New Zealand (data/raw/faostat_producer_prices_aus_nzl.csv)."),
        ("Global Hunger Index", "Welthungerhilfe and Concern Worldwide, 2025 edition with 2000, 2008 and 2016 scores (data/raw/global_hunger_index.xlsx)."),
        ("World Bank", "World Development Indicators, food imports (% of merchandise imports) (data/raw/worldbank_food_import_raw.csv)."),
        ("Cover photo", "A sack of split peas awaits distribution at a joint WFP and ACTED site in Bamako, Mali. DFID, Wikimedia Commons, CC BY 2.0."),
        ("Question photo", "Uganda refugee settlements emergency food distribution. USAID in Africa, Wikimedia Commons, public domain."),
        ("Roadmap photo", "Zimbabwe food distribution. Department of Foreign Affairs and Trade (Australia), Wikimedia Commons, CC BY 2.0."),
        ("Poster photo", "Uganda refugee settlements emergency food distribution. USAID in Africa, Wikimedia Commons, public domain."),
        ("Flags", "flag-icons by Panayiotis Lipiridis, MIT licence."),
        ("Logos", "Shown only to identify each data source; they remain the property of their owners."),
    ]
    rows_b = "".join(f"<tr><td>{a}</td><td>{esc(b)}</td></tr>" for a, b in srcs_a)
    pages.append(slide("next", "A2", header("next", "Sources and credits", overview=True).replace(">Overview<", ">Appendix<") +
        '<h1>Sources and credits</h1><div class="sub">Data files used by the build, and the images in this deck.</div>'
        f'<div class="appx2"><table class="tbl">{rows_b}</table></div>'))
    return pages


# --------------------------------------------------------------------------- poster
POSTER_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: 841mm 594mm; margin: 0; }
html, body { background: #fff; }
body { font-family: 'Google Sans', sans-serif; color: #1B2430; }
.poster { position: relative; width: 841mm; height: 594mm; padding: 18mm; display: flex; flex-direction: column; gap: 4mm; overflow: hidden; }
.kt { color: var(--acc); }
header { position: relative; }
.top { font-size: 20pt; letter-spacing: .06em; text-transform: uppercase; color: #5A6370; font-weight: 700; }
.title { font-size: 72pt; font-weight: 700; line-height: 1.04; letter-spacing: -.012em; margin-top: 2mm; }
.q { font-size: 26pt; color: #5A6370; margin-top: 2mm; }
.team { font-size: 22pt; font-weight: 700; margin-top: 2mm; }
.ulogo { position: absolute; right: 0; top: 0; width: 32mm; height: 32mm; }
.ulogo svg { width: 100%; height: 100%; display: block; }
.answer { background: #1B2430; color: #fff; display: grid; grid-template-columns: 150mm 1fr 210mm; gap: 10mm; padding: 6mm 10mm; align-items: center; }
.answer .num { font-size: 48pt; font-weight: 700; color: #FDE725; line-height: 1; }
.answer .numlab { font-size: 20pt; color: #D8DEE3; margin-top: 2mm; line-height: 1.3; }
.answer > div:nth-child(2) { border-left: .4mm solid #5A6370; padding-left: 10mm; }
.answer .verdict { font-size: 28pt; font-weight: 700; line-height: 1.2; }
.answer .reason { font-size: 22pt; color: #D8DEE3; margin-top: 2mm; line-height: 1.35; }
.answer .reason b { color: #fff; }
.answer .next { font-size: 20pt; line-height: 1.5; color: #D8DEE3; border-left: .4mm solid #5A6370; padding-left: 8mm; }
.answer .next .lab { font-weight: 700; letter-spacing: .08em; color: #FDE725; }
.answer .next b { color: #fff; font-weight: 400; }
.answer .next .n { display: inline-grid; place-items: center; width: 8mm; height: 8mm; border-radius: 50%; background: #FDE725; color: #1B2430; font-weight: 700; font-size: 18pt; margin-right: 2mm; }
.sec { font-size: 20pt; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #526174; display: flex; align-items: center; gap: 5mm; }
.sec::after { content: ''; flex: 1; height: .3mm; background: #D8DEE3; }
.row { display: grid; gap: 6mm; }
.card { background: #F4F5F6; border-top: 1.6mm solid var(--acc); padding: 5mm 6mm; display: flex; flex-direction: column; min-width: 0; }
.card h2 { font-size: 28pt; line-height: 1.18; }
.legend { display: flex; flex-wrap: wrap; gap: 1.5mm 6mm; font-size: 18pt; color: #5A6370; margin-top: 2.5mm; }
.key { display: inline-flex; align-items: center; gap: 2mm; }
.key i { display: inline-block; }
.k-line { width: 10mm; height: 1.5mm; border-radius: 1mm; background: var(--c); }
.k-dot { width: 4.5mm; height: 4.5mm; border-radius: 50%; background: var(--c); }
.k-band { width: 8mm; height: 5mm; background: color-mix(in srgb, var(--c) 32%, white); }
.k-box { width: 8mm; height: 4mm; background: var(--c); }
.fig { margin-top: 2mm; }
.fig svg { display: block; width: 100%; height: auto; }
.src { font-size: 18pt; color: #5A6370; margin-top: auto; padding-top: 2mm; line-height: 1.3; }
.src b { color: #1B2430; }
.pts { display: flex; flex-direction: column; gap: 3mm; margin-top: 3mm; }
.pt { display: grid; grid-template-columns: 8mm 1fr; gap: 0 3mm; font-size: 20pt; line-height: 1.3; color: #5A6370; }
.pt .m { width: 7.5mm; height: 7.5mm; border-radius: 50%; background: #B8452E; color: #fff; font-size: 18pt; font-weight: 700; display: grid; place-items: center; margin-top: .6mm; }
.pt b { color: #1B2430; }
.heat { width: 100%; border-collapse: separate; border-spacing: 1.2mm; margin-top: 3mm; }
.heat th { font-size: 18pt; font-weight: 700; color: #5A6370; text-align: center; padding: 1mm; line-height: 1.1; }
.heat tr th:first-child { text-align: left; color: #1B2430; width: 30mm; }
.heat td { text-align: center; font-size: 26pt; font-weight: 700; height: 22mm; border-radius: 1mm; }
.heat td.lead { outline: 1mm solid #1B2430; outline-offset: -1mm; }
.hscale { display: flex; align-items: center; gap: 2.5mm; font-size: 18pt; color: #5A6370; margin-top: 2mm; flex-wrap: wrap; }
.hscale i { width: 50mm; height: 3.5mm; }
.hscale em { font-style: normal; flex-basis: 100%; }
.rank { width: 100%; border-collapse: collapse; font-size: 20pt; margin-top: 3mm; }
.rank th { text-align: left; font-weight: 700; color: #5A6370; font-size: 18pt; border-bottom: .4mm solid #89949D; padding-bottom: 1mm; }
.rank th + th, .rank td + td { text-align: right; }
.rank td { padding: 1.9mm 0; border-bottom: .2mm solid #D8DEE3; }
.gauges { background: #fff; padding: 2mm 4mm; margin-top: 2mm; }
.gh { font-size: 18pt; color: #5A6370; margin-bottom: 1.5mm; }
.g { display: grid; grid-template-columns: 50mm 1fr 18mm; align-items: center; gap: 3mm; font-size: 20pt; margin-top: 1.5mm; }
.g b { text-align: right; }
.gb { position: relative; height: 4mm; background: #EDF0F3; }
.gb i { position: absolute; left: 0; top: 0; bottom: 0; }
.gb u { position: absolute; top: -1.5mm; bottom: -1.5mm; width: 0; border-left: .5mm dashed #1B2430; }
.nextrow { display: grid; grid-template-columns: 1fr 1fr 1fr 250mm; gap: 6mm; }
.step { background: #F4F5F6; border-top: 1.6mm solid #526174; padding: 4mm 5mm; }
.step h3 { font-size: 24pt; display: flex; align-items: center; gap: 3mm; }
.step h3 svg { width: 9mm; height: 9mm; color: #32658A; flex: none; }
.step p { font-size: 20pt; color: #5A6370; margin-top: 1.5mm; line-height: 1.3; }
.cta { background: #1B2430; color: #fff; padding: 5mm 7mm; display: flex; align-items: center; gap: 8mm; }
.cta h3 { font-size: 28pt; line-height: 1.2; flex: 1; }
.cta .qr { background: #fff; padding: 2mm; width: 34mm; height: 34mm; flex: none; }
.cta .qr svg { width: 100%; height: 100%; display: block; }
.cta small { display: block; font-size: 18pt; color: #D8DEE3; font-weight: 400; margin-top: 2mm; }
.foot { display: flex; justify-content: space-between; font-size: 18pt; color: #5A6370; border-top: .3mm solid #1B2430; padding-top: 2.5mm; margin-top: auto; }
.foot b { color: #1B2430; }
.ml { font: 20px 'Google Sans'; fill: #1B2430; }
header { padding-right: 236mm; }
.hphoto { position: absolute; right: -18mm; top: -18mm; width: 340mm; bottom: -2mm; background-size: cover; background-position: center 45%; opacity: .92;
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.35) 25%, #000 60%), linear-gradient(180deg, #000 70%, transparent 100%);
  -webkit-mask-composite: source-in; mask-composite: intersect; z-index: 0; }
header > *:not(.hphoto) { position: relative; z-index: 1; }
header .ulogo { position: absolute; }
.flag { height: 5mm; width: 6.7mm; vertical-align: middle; box-shadow: 0 0 0 .2mm rgba(27,36,48,.3); margin-right: 1.5mm; }
.rk2 td.nb { position: relative; padding-bottom: 3.2mm; }
.rk2 td.nb i { position: absolute; right: 0; bottom: 1mm; height: 1.4mm; }
.ml.mute { fill: #5A6370; }
.heat { table-layout: fixed; }
.heat tr:first-child th { vertical-align: bottom; }
.heat tr th:first-child { width: 34mm; }
.rk2 { table-layout: fixed; }
.rk2 th { vertical-align: bottom; line-height: 1.15; padding: 0 0 1.5mm; }
.rk2 th:first-child { width: 50%; }
.rk2 td { vertical-align: middle; padding: 2mm 0 3.6mm; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rk2 td + td, .rk2 th + th { padding-left: 4mm; }
.rk2 td.nb i { bottom: 1.4mm; }
"""

MM = 72 / 25.4  # points per mm


def pts(notes) -> str:
    return '<div class="pts">' + "".join(
        f'<div class="pt"><span class="m">{i + 1}</span><span><b>{esc(h)}.</b> {esc(p)}</span></div>'
        for i, (h, p) in enumerate(notes)) + "</div>"


def ranked_poster(f: dict, n: int = 10) -> str:
    rows = ""
    for c_, imp, g in f["exposure"]["exposed"][:n]:
        rows += (f'<tr><td>{flag(c_)} {html.escape(SHORT.get(c_, c_))}</td><td class="nb"><b>{g:.1f}</b><i style="width:{(g - 15) / 25 * 100:.0f}%;background:{hc.EXPOSED}"></i></td>'
                 f'<td class="nb">{imp:.1f}%<i style="width:{imp / 45 * 100:.0f}%;background:#B9C2CA"></i></td></tr>')
    return (f'<table class="rank rk2"><tr><th>Country</th>'
            f'<th>Hunger<br>(GHI 2025)</th><th>Food share<br>of imports</th></tr>{rows}</table>')


def build_poster(f: dict, c: dict) -> str:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    now = w["latest_yoy_pct"]
    leads = sorted(w["lead_months"])
    inner = 841 - 36
    # row 1: shock chart (8 parts) + drivers (4 parts); row 2: exposure (5) + ranked (2) + warning (5)
    r1a = (inner - 6) * 0.64 - 12
    r2a = (inner - 12) * 0.36 - 12
    shock_fig = svg("shock", r1a * MM, 82 * MM, 22, markers=True, poster=True)
    exp_fig = svg("exposure", r2a * MM, 96 * MM, 22, labels=["Haiti", "Madagascar"], marks=True, poster=True)
    warn_fig = svg("warning", r2a * MM, 86 * MM, 22, poster=True)
    cs, cd, ce, cw = c["shock"], c["drivers"], c["exposure"], c["warning"]
    ex0, hl = e["exposed"], f["hunger_trend"]["high_hunger_low_import"]
    gb = max(ex0, key=lambda x: x[1])

    def card(key, h, body, span=""):
        return f'<div class="card" style="--acc:{CH[key][1]}{span}"><h2>{h}</h2>{body}</div>'

    steps = "".join(
        f'<div class="step"><h3>{ICONS[a]}{esc(h)}</h3><p>{esc(p)}</p></div>' for a, h, p in c["next"])
    return f"""
<div class="poster">
  <header>
    <div class="top">{SUBJECT}</div>
    <div class="title">{TITLE[0]} {TITLE[1]}</div>
    <div class="q">When global food prices spike, which countries feel it first, and can we see it coming?</div>
    <div class="team">{AUTHOR} · {SCHOOL}</div>
    <div class="hphoto" style="background-image:url(../../assets/photos/photo-uganda-wide.jpg)"></div>
    <div class="ulogo">{logo()}</div>
  </header>
  <div class="answer">
    <div><div class="num">{w['followed_by_shock_within_12m']} of {w['signals']}</div>
      <div class="numlab">two-price signals were followed by a food-price shock, {leads[0]}–{leads[-1]} months later</div></div>
    <div><div class="verdict">Oils and cereals warn early; {e['exposed_count']} countries feel it first.</div>
      <div class="reason">{esc(f"Shocks are growing (**{s['peaks'][0][1]} → {s['peaks'][1][1]} → {s['peaks'][2][1]}**) and land hardest where hunger is serious and food is imported. Today there is **no signal**: oils +{now['oils']:.0f}%, cereals +{now['cereals']:.0f}% ({month(now['month'])}).")}</div></div>
    <div class="next"><div class="lab">NEXT</div>
      <div><span class="n">1</span><b>Monitor</b> oils and cereals monthly</div>
      <div><span class="n">2</span><b>Prepare</b> the {e['exposed_count']} exposed countries first</div>
      <div><span class="n">3</span><b>Test</b> the rule on held-out years</div></div>
  </div>
  <div class="sec">The shock, and what drove it</div>
  <div class="row" style="grid-template-columns: 64fr 36fr">
    {card('shock', esc('Three spikes since 2007, {k}each peak higher{/k} than the last'),
          legend(cs['legend']) + f'<div class="fig">{shock_fig}</div>' + pts(cs['notes']))}
    {card('shock', esc('{k}Vegetable oils{/k} led two of three shocks; meat stayed calm'),
          heat_table(f) + f'<div class="src">{esc(cd["source"].replace(" Shock periods as defined on the previous page.", ""))}</div>')}
  </div>
  <div class="sec">Who feels it first, and the early signal</div>
  <div class="row" style="grid-template-columns: 36fr 22fr 42fr">
    {card('exposure', esc(f"{{k}}{e['exposed_count']} of {e['countries_plotted']}{{/k}} countries: serious hunger, high food imports"),
          legend(ce['legend']) + f'<div class="fig">{exp_fig}</div>' + pts([(ex0[0][0], f"highest hunger, GHI {ex0[0][2]}"), (gb[0], f"most import-reliant, {gb[1]:.1f}% of imports are food"), (SHORT.get(hl[0], hl[0]), "serious hunger but imports little food")]) + f'<div class="src">{esc(ce["source"])}</div>')}
    {card('exposure', esc(f"The {{k}}hungriest{{/k}} of the {e['exposed_count']} exposed"), ranked_poster(f, 9) +
          '<div class="src"><b>GHI:</b> Global Hunger Index 2025 (20+ is serious). <b>Food imports:</b> % of merchandise imports.</div>')}
    {card('warning', esc('{k}Oils and cereals{/k} rose 20% before every shock since 2000'),
          legend(cw['legend']) + f'<div class="fig">{warn_fig}</div>' + gauges(f) +
          f'<div class="src"><b>Note:</b> the rule was read off this history, so it is a signal to watch, not a tested forecast. One false alarm (2002).</div>')}
  </div>
  <div class="sec">What is next</div>
  <div class="nextrow">{steps}
    <div class="cta"><h3>Explore the interactive dashboard<small>Scenarios, country filters and the full data story</small></h3><div class="qr">{qr_svg(APP_URL)}</div></div>
  </div>
  <div class="foot"><span><b>{PROJECT}</b> · {AUTHOR}</span><span>Data: FAO Food Price Index, Global Hunger Index 2025, World Bank · {REPO_URL}</span></div>
</div>"""


# --------------------------------------------------------------------------- render
def font_css(prefix: str) -> str:
    return (f"@font-face {{ font-family: 'Google Sans'; font-weight: 400; src: url('{prefix}GoogleSans-Regular.ttf'); }}"
            f"@font-face {{ font-family: 'Google Sans'; font-weight: 700; src: url('{prefix}GoogleSans-Bold.ttf'); }}")


def page(body: str, css: str, title: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>'
            f'<style>{font_css("../../fonts/")}{css}</style></head><body>{body}</body></html>')


def main() -> None:
    global DATA
    DATA = hc.main()
    f = DATA["findings"]
    copy = story(f)
    for d in (SLIDES, POSTER):
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("slide-*.png"):
            old.unlink()
    (SLIDES / "slides.html").write_text(page("".join(build_slides(f, copy)), SLIDE_CSS + EXTRA_CSS + V5_CSS, PROJECT))
    (POSTER / "poster.html").write_text(page(build_poster(f, copy), POSTER_CSS, PROJECT + " poster"))
    (OUT / "copy.json").write_text(json.dumps(copy, indent=2, ensure_ascii=False))
    subprocess.run(["node", str(RENDER), "slides", str(SLIDES / "slides.html"), str(SLIDES)], check=True)
    subprocess.run(["node", str(RENDER), "poster", str(POSTER / "poster.html"), str(POSTER)], check=True)
    for n, name in ((6, "01-shock"), (9, "02-exposure"), (13, "03-warning")):
        shutil.copyfile(SLIDES / f"slide-{n}.png", OUT / f"{name}.png")
    print("Built slides and poster in", OUT)


DATA: dict = {}

if __name__ == "__main__":
    main()
