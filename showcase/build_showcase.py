"""Build the slide deck and A1 poster for the food-price story.

Outputs (showcase/output/):
    slides/slides.html, slides/slides.pdf, slides/slide-1..7.png   16:9, 960 x 540 pt (PNG 1920 x 1080)
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
SUBJECT = "Data Visualisation Design and Storytelling"
WORK = "Group assignment"
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
                       f'stroke-width="1.5"/><text x="{x - 9:.1f}" y="34" text-anchor="end" class="ml mute">none</text>')
    for yr in (2000, 2010, 2020):
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
            take="Each shock lasted more than a year, and prices have not gone back to the 2014–16 base.",
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
            take="Oils and cereals moved most in every shock, so they are the two prices the warning watches.",
            notes=[
                ("Vegetable oils", f"Rose most in {k[0]} (+{drv[k[0]]['Vegetable oils']:.0f}%) and {k[2]} (+{drv[k[2]]['Vegetable oils']:.0f}%)."),
                ("Cereals", f"Rose most in {k[1]} (+{drv[k[1]]['Cereals']:.0f}%), and +{drv[k[0]]['Cereals']:.0f}% in {k[0]}."),
                ("Meat stayed calm", f"Never more than +{max(r['values'][4] for r in dr['rows']):.0f}%, so it adds little warning."),
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
                ("A signal, not a forecast", "The rule was read off this same history; models trained before 2013 missed most of 2020–21."),
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
.heat td { text-align: center; font-size: 14pt; font-weight: 700; height: 62pt; border-radius: 2pt; }
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


def build_slides(f: dict, c: dict) -> list[str]:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    pages = []
    # 1 cover
    pages.append(
        f'<section class="slide cover"><div class="ulogo">{logo()}</div><div class="band">'
        f'<div class="lbl">{SUBJECT} | {WORK}</div><div class="ttl">{TITLE[0]}<br>{TITLE[1]}</div>'
        f'<div class="cs">An early-warning story from 36 years of FAO food prices, the 2025 Global Hunger Index and '
        f'World Bank trade data.</div></div>'
        f'<div class="who"><b>{AUTHOR}</b><br>{SCHOOL}<br>{DATE}</div>'
        f'<div class="art">{cover_art()}<p>Each column is one year of the FAO Food Price Index, one pill per 10 points; '
        f'ochre years include shock months.</p></div></section>'
    )
    # 2 summary
    leads = sorted(w["lead_months"])
    cards = [
        ("shock", "Food-price shocks keep getting bigger", f"{s['peaks'][2][1]}", f"record index, {month(s['peaks'][2][0])}",
         mini_spark(f), f"Peaks of {s['peaks'][0][1]}, {s['peaks'][1][1]} and {s['peaks'][2][1]}; still {s['latest'][1]} today."),
        ("exposure", "Hunger and import reliance overlap", f"{e['exposed_count']} of {e['countries_plotted']}", "countries most exposed",
         mini_grid(e["exposed_count"], e["countries_plotted"]), "Serious hunger (GHI 20+) and above-median food imports."),
        ("warning", "Two prices moved first", f"{w['followed_by_shock_within_12m']} of {w['signals']}", "signals followed by a shock",
         mini_signals(f), f"Oils and cereals both up 20%+ came {leads[0]}–{leads[-1]} months before every shock since 2000."),
    ]
    card_html = "".join(
        f'<div class="card" style="--ca:{CH[k][1]}"><div class="lab">{i + 1} · {CH[k][0]}</div><h3>{esc(h)}</h3>'
        f'<div class="num">{num}</div><div class="unit">{unit}</div>{fig}<p>{esc(p)}</p></div>'
        for i, (k, h, num, unit, fig, p) in enumerate(cards)
    )
    now = w["latest_yoy_pct"]
    pages.append(slide("shock", 2,
        header("shock", "Summary", overview=True) +
        '<h1>Food-price shocks are growing, and two prices warn of them early</h1>'
        '<div class="sub">What 36 years of FAO prices, the 2025 Global Hunger Index and World Bank trade data show.</div>'
        f'<div class="cards">{card_html}</div>'
        f'<div class="bandtake"><span>TAKEAWAY</span>{esc(f"No warning signal in {month(now["month"])}: oils +{now["oils"]:.0f}%, cereals +{now["cereals"]:.0f}%. Watch both monthly.")}</div>'))
    # 3 shock
    cs = c["shock"]
    pages.append(slide("shock", 3, header("shock", "Global food prices") +
        f'<h1>{esc(cs["title"])}</h1><div class="sub">{esc(cs["subtitle"])}</div>'
        f'<div class="left">{legend(cs["legend"])}<div class="fig">{svg("shock", 624.5, 318, 9, markers=True)}</div>'
        f'<div class="src">{esc(cs["source"])}</div></div>{right_col(cs)}'))
    # 4 drivers
    cd = c["drivers"]
    pages.append(slide("shock", 4, header("shock", "What drove each shock") +
        f'<h1>{esc(cd["title"])}</h1><div class="sub">{esc(cd["subtitle"])}</div>'
        f'<div class="left">{heat_table(f)}<div class="src">{esc(cd["source"])}</div></div>{right_col(cd)}'))
    # 5 exposure
    ce = c["exposure"]
    pages.append(slide("exposure", 5, header("exposure", "Who feels it first") +
        f'<h1>{esc(ce["title"])}</h1><div class="sub">{esc(ce["subtitle"])}</div>'
        f'<div class="left">{legend(ce["legend"])}<div class="fig">{svg("exposure", 624.5, 318, 9)}</div>'
        f'<div class="src">{esc(ce["source"])}</div></div>{right_col(ce, ranked(f))}'))
    # 6 warning
    cw = c["warning"]
    pages.append(slide("warning", 6, header("warning", "An early signal") +
        f'<h1>{esc(cw["title"])}</h1><div class="sub">{esc(cw["subtitle"])}</div>'
        f'<div class="left">{legend(cw["legend"])}<div class="fig">{svg("warning", 624.5, 318, 9)}</div>'
        f'<div class="src">{esc(cw["source"])}</div></div>{right_col(cw, gauges(f))}'))
    # 7 next
    steps = "".join(
        f'<div class="step"><div class="ic">{ICONS[a]}</div><div><small>{i + 1} · {a}</small><h3>{esc(h)}</h3><p>{esc(p)}</p></div></div>'
        for i, (a, h, p) in enumerate(c["next"])
    )
    pages.append(slide("next", 7, header("next", "What to do with it") +
        '<h1>Watch two prices monthly, prepare the 20 countries, and test the rule</h1>'
        '<div class="sub">Three steps that turn the charts into an early-warning routine.</div>'
        f'<div class="steps">{steps}</div>'
        f'<div class="cta"><h3>Explore the interactive dashboard</h3><div class="qr"><div>{qr_svg(APP_URL)}</div>'
        f'<span>Scenarios, country filters and the full data story</span></div></div>'
        f'<div class="data"><h4>Data and definitions</h4><b>FAO Food Price Index</b>, monthly, {month(s["series_start"])}–{month(s["latest"][0])}. '
        f'<b>Global Hunger Index 2025.</b> <b>World Bank</b> food imports, {e["import_year_min"]}–{e["import_year_max"]}.<br>'
        f'<b>Shock month:</b> all-food index 20%+ above a year earlier. <b>Signal:</b> oils and cereals both 20%+, outside a shock. '
        f'<b>Exposed:</b> GHI 20+ and food imports above the {e["median_food_import_pct"]}% median.</div>'))
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
.ml.mute { fill: #5A6370; }
"""

MM = 72 / 25.4  # points per mm


def pts(notes) -> str:
    return '<div class="pts">' + "".join(
        f'<div class="pt"><span class="m">{i + 1}</span><span><b>{esc(h)}.</b> {esc(p)}</span></div>'
        for i, (h, p) in enumerate(notes)) + "</div>"


def build_poster(f: dict, c: dict) -> str:
    s, e, w = f["shock"], f["exposure"], f["warning"]
    now = w["latest_yoy_pct"]
    leads = sorted(w["lead_months"])
    inner = 841 - 36
    # row 1: shock chart (8 parts) + drivers (4 parts); row 2: exposure (5) + ranked (2) + warning (5)
    r1a = (inner - 6) * 0.64 - 12
    r2a = (inner - 12) * 0.36 - 12
    shock_fig = svg("shock", r1a * MM, 82 * MM, 22, markers=True)
    exp_fig = svg("exposure", r2a * MM, 116 * MM, 22, labels=["Haiti", "Niger", "Madagascar", "Papua New Guinea", "Sierra Leone"])
    warn_fig = svg("warning", r2a * MM, 86 * MM, 22)
    cs, cd, ce, cw = c["shock"], c["drivers"], c["exposure"], c["warning"]

    def card(key, h, body, span=""):
        return f'<div class="card" style="--acc:{CH[key][1]}{span}"><h2>{h}</h2>{body}</div>'

    steps = "".join(
        f'<div class="step"><h3>{ICONS[a]}{esc(h)}</h3><p>{esc(p)}</p></div>' for a, h, p in c["next"])
    return f"""
<div class="poster">
  <header>
    <div class="top">{SUBJECT} | {WORK}</div>
    <div class="title">{TITLE[0]} {TITLE[1]}</div>
    <div class="q">When global food prices spike, which countries feel it first, and can we see it coming?</div>
    <div class="team">{AUTHOR} · {SCHOOL}</div>
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
          legend(ce['legend']) + f'<div class="fig">{exp_fig}</div>' + f'<div class="src">{esc(ce["source"])}</div>')}
    {card('exposure', esc('The {k}hungriest{/k} of the exposed'), ranked(f, 9) +
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
    (SLIDES / "slides.html").write_text(page("".join(build_slides(f, copy)), SLIDE_CSS, PROJECT))
    (POSTER / "poster.html").write_text(page(build_poster(f, copy), POSTER_CSS, PROJECT + " poster"))
    (OUT / "copy.json").write_text(json.dumps(copy, indent=2, ensure_ascii=False))
    subprocess.run(["node", str(RENDER), "slides", str(SLIDES / "slides.html"), str(SLIDES)], check=True)
    subprocess.run(["node", str(RENDER), "poster", str(POSTER / "poster.html"), str(POSTER)], check=True)
    for n, name in ((3, "01-shock"), (5, "02-exposure"), (6, "03-warning")):
        shutil.copyfile(SLIDES / f"slide-{n}.png", OUT / f"{name}.png")
    print("Built slides and poster in", OUT)


DATA: dict = {}

if __name__ == "__main__":
    main()
