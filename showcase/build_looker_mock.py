"""Mock the four Looker tabs at 1600x690 with real data, as a layout proposal before rebuilding in Looker.

Every element maps to a native Looker Studio component (scorecard with comparison, combo chart, bar chart,
scatter, table with image and bar columns, bullet chart, geo map), so the approved mock can be built as is.

Run from the repository root:  python showcase/build_looker_mock.py
Outputs: showcase/output/looker/mock/mock.html (+ PNGs rendered by render.mjs-style Playwright call)
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
LOOK = ROOT / "output" / "looker"
OUT = LOOK / "mock"
FLAGS = ROOT / "assets" / "flags"

INK, GREY, HAIR, BG = "#1f2937", "#6b7280", "#e5e7eb", "#f3f4f6"
FOOD, OILS, CEREALS, EXPOSED, OTHER = "#3B528B", "#21918C", "#35B779", "#440154", "#B9C2CA"
SHADE, AMBER, RED, GREEN = "#ffe08a", "#E0A100", "#C0392B", "#2E8B57"

W, H = 1600, 690
RAIL_X, RAIL_W = 16, 232
CX = RAIL_X + RAIL_W + 16           # content x
CW = W - CX - 16                    # content width
TOP = 56 + 14                       # below header

ISO2 = {"MDG": "mg", "HTI": "ht", "NER": "ne", "CAF": "cf", "PNG": "pg", "LBR": "lr", "AFG": "af",
        "SLE": "sl", "TLS": "tl", "BEN": "bj", "MOZ": "mz", "KEN": "ke", "GNB": "gw", "GIN": "gn",
        "COG": "cg", "DJI": "dj", "RWA": "rw", "ZWE": "zw", "CIV": "ci", "SLB": "sb"}


def esc(s: str) -> str:
    return html.escape(str(s))


def flag(iso3: str) -> str:
    code = ISO2.get(iso3, "")
    p = FLAGS / f"{code}.svg"
    if not p.exists():
        p = Path("/tmp/claude-0/fi/package/flags/4x3") / f"{code}.svg"
    if not p.exists():
        return '<span class="flag"></span>'
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'<img class="flag" src="data:image/svg+xml;base64,{b64}">'


# ---------------------------------------------------------------- data
m = pd.read_csv(LOOK / "live_monthly.csv", parse_dates=["date"])
c = pd.read_csv(LOOK / "live_countries.csv")
s = pd.read_csv(LOOK / "live_signal.csv", parse_dates=["date"])
food = m[m.food_group == "All food"].set_index("date")
oils = m[m.food_group == "Vegetable oils"].set_index("date")
cer = m[m.food_group == "Cereals"].set_index("date")


# ---------------------------------------------------------------- svg helpers
def scale(v, a, b, lo, hi):
    return lo + (v - a) / (b - a) * (hi - lo)


def time_chart(w, h, series, shade=None, y=(0, 260), ticks=(0, 50, 100, 150, 200, 250), ref=None,
               ref_label="", years=range(1990, 2027, 5), x0=None, x1=None, yfmt="{:g}", pl=36):
    """Line chart over time with optional shaded months; series = [(pd.Series, colour, width)]."""
    pr, pt, pb = 12, 10, 22
    x0 = x0 or pd.Timestamp("1990-01-01")
    x1 = x1 or pd.Timestamp("2026-03-01")
    X = lambda d: scale(d.value, x0.value, x1.value, pl, w - pr)  # noqa: E731
    Y = lambda v: scale(v, y[0], y[1], h - pb, pt)  # noqa: E731
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for t in ticks:
        out.append(f'<line x1="{pl}" x2="{w-pr}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{HAIR}"/>')
        out.append(f'<text x="{pl-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{yfmt.format(t)}</text>')
    if shade is not None:
        step = (X(x1) - X(x0)) / max(1, (x1.year - x0.year) * 12 + x1.month - x0.month)
        for d in shade:
            out.append(f'<rect x="{X(d):.1f}" y="{pt}" width="{max(step,1.2):.1f}" height="{h-pb-pt}" fill="{SHADE}"/>')
    if ref is not None:
        out.append(f'<line x1="{pl}" x2="{w-pr}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" stroke="{GREY}" '
                   f'stroke-dasharray="5 4"/>')
        if ref_label:
            out.append(f'<text x="{pl+6}" y="{Y(ref)-5:.1f}" class="ax b">{esc(ref_label)}</text>')
    for ser, col, sw in series:
        pts = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in ser.dropna().items())
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{sw}" '
                   'stroke-linejoin="round"/>')
    for yr in years:
        d = pd.Timestamp(f"{yr}-01-01")
        out.append(f'<text x="{X(d):.1f}" y="{h-6}" class="ax" text-anchor="middle">{yr}</text>')
    out.append("</svg>")
    return "".join(out)


def legend(items):
    return '<div class="legend">' + "".join(
        f'<span><i style="background:{col};{"height:10px" if box else ""}"></i>{esc(lbl)}</span>'
        for lbl, col, box in items) + "</div>"


# ---------------------------------------------------------------- page chrome
ICON = {
    "up": '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1 11 10H1z" fill="currentColor"/></svg>',
    "down": '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 11 1 2h10z" fill="currentColor"/></svg>',
}


def card(label, value, note, tone=INK, delta=None, accent=None, extra=""):
    d = ""
    if delta:
        arrow, txt, col = delta
        d = f'<span class="delta" style="color:{col}">{ICON[arrow]}{esc(txt)}</span>'
    acc = f'style="border-left:4px solid {accent}"' if accent else ""
    return (f'<div class="card" {acc}><div class="lab">{esc(label)}</div>'
            f'<div class="num" style="color:{tone}">{value}</div>'
            f'<div class="note">{d}{note}</div>{extra}</div>')


def rail():
    return f"""
<aside class="rail">
  <div class="h">Filters</div>
  <div class="ctl"><span>Food group</span><b>All food ▾</b></div>
  <div class="ctl"><span>Dates</span><b>Jan 1990 – Mar 2026 ▾</b></div>
  <div class="ctl"><span>Country</span><b>All ▾</b></div>
  <div class="h" style="margin-top:22px">How the warning works</div>
  <ul class="bul">
    <li><i style="background:{OILS}"></i><span>Watch <b style="color:{OILS}">vegetable oils</b> and <b style="color:{CEREALS}">cereals</b></span></li>
    <li><i style="background:{AMBER}"></i><span><b>Signal on</b> when both are <b>20%+</b> above a year earlier</span></li>
    <li><i style="background:{RED}"></i><span><b>4 of 5</b> signals since 2000 led to a shock in <b>1–5 months</b></span></li>
  </ul>
  <div class="src"><div class="h small">Sources</div>FAO Food Price Index (2014–16 = 100), Jan 1990 – Mar 2026 ·
  FAOSTAT food imports, 2015–24 · Global Hunger Index 2025</div>
</aside>"""


def page(tab, body):
    tabs = "".join(f'<span class="{"on" if t == tab else ""}">{t}</span>'
                   for t in ["Overview", "The shock", "The exposure", "The warning"])
    return f"""<section class="frame" id="{tab.replace(' ', '-').lower()}">
<div class="tabs">{tabs}</div>
<div class="canvas">
<header><h1>Food Price Shock Early Warning</h1><span>Manh Tuan (Mike) Nguyen</span></header>
{rail()}
<main>{body}</main>
</div></section>"""


def panel(title, inner, w, h, sub=""):
    sub = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="panel" style="width:{w}px;height:{h}px"><div class="pt">{title}</div>{sub}{inner}</div>'


# ---------------------------------------------------------------- tabs
def overview():
    lat = food.index.max()
    yoy_now = food.yoy_pct.iloc[-1]
    cards = "".join([
        card("Price index now", f"{food.price_index.iloc[-1]:.1f}", "Mar 2026, all food",
             delta=("up", f"{yoy_now:+.1f}% on a year earlier", RED), accent=FOOD),
        card("Peak in range", f"{food.price_index.max():.1f}", "Mar 2022, the record high", accent=FOOD),
        card("Exposed countries", '20 <small>of 91</small>', "Serious hunger <b>and</b> high food imports",
             tone=EXPOSED, accent=EXPOSED),
        card("Warning signal now", '<span class="dot" style="background:#9ca3af"></span>Off',
             f'<b style="color:{OILS}">Oils +13.2%</b> · <b style="color:{CEREALS}">cereals +0.6%</b> · needs both 20%+',
             accent=AMBER),
    ])
    shock = food.index[food.rise_20_month == 1]
    lw, lh = 820, 470
    line = time_chart(lw - 24, lh - 92, [(cer.price_index, CEREALS, 1.4), (oils.price_index, OILS, 1.4),
                                         (food.price_index, FOOD, 2.6)], shade=shock, ref=100,
                      ref_label="2014–16 = 100")
    left = panel("Food prices over time: three spikes since 2007, each 20%+ above a year earlier",
                 legend([("All food", FOOD, 0), ("Vegetable oils", OILS, 0), ("Cereals", CEREALS, 0),
                         ("Month 20%+ above a year earlier", SHADE, 1)]) + line, lw, lh,
                 sub="Monthly FAO Food Price Index")
    rw = CW - lw - 16
    grad = f"linear-gradient(90deg,#eef0f3,{AMBER} 50%,{RED})"
    mapbox = (f'<div class="mapph">Looker geo map, kept<br><small>new 3-step colour scale: low = light grey, '
              f'20 (serious) = amber, 40+ = red. Hover shows country + score.</small></div>'
              f'<div class="grad"><span>5</span><i style="background:{grad}"></i><span>42.6</span></div>'
              f'<div class="sub" style="margin-top:6px">Serious hunger starts at 20. Somalia is highest (42.6).</div>')
    right = panel("Where hunger is worst (GHI 2025)", mapbox, rw, lh, sub="Hunger score by country")
    return f'<div class="row cards4">{cards}</div><div class="row">{left}{right}</div>'


def shock_tab():
    cards = "".join([
        card("Peak in range", f"{food.price_index.max():.1f}", "Mar 2022, the record high", accent=FOOD),
        card("Biggest jump on a year", '+63.2%', "Mar 2008, at the height of the 2007–08 shock",
             tone=RED, accent=RED),
        card("Months 20%+ up", "45", "3 major shocks + 2 one-month spikes", tone=INK, accent=AMBER),
    ])
    shock = food.index[food.rise_20_month == 1]
    main = time_chart(CW - 24, 278, [(food.price_index, FOOD, 2.4)], shade=shock, y=(0, 175),
                      ticks=(0, 50, 100, 150), ref=100, ref_label="2014–16 = 100")
    top = panel("All-food price index: shaded months are 20%+ above a year earlier",
                legend([("Price index", FOOD, 0), ("Month 20%+ up", SHADE, 1)]) + main, CW, 340)
    by = food.groupby(food.index.year).rise_20_month.sum()
    bw, bh, pl = CW - 24, 92, 36
    n = len(by)
    step = (bw - pl - 12) / n
    bars = [f'<svg width="{bw}" height="{bh}">']
    for i, (yr, v) in enumerate(by.items()):
        x = pl + i * step
        hh = v / 12 * (bh - 30)
        if v:
            bars.append(f'<rect x="{x+2:.1f}" y="{bh-20-hh:.1f}" width="{step-4:.1f}" height="{hh:.1f}" fill="{AMBER}"/>')
            bars.append(f'<text x="{x+step/2:.1f}" y="{bh-24-hh:.1f}" class="ax b" text-anchor="middle">{v}</text>')
        if yr % 5 == 0 or v:
            bars.append(f'<text x="{x+step/2:.1f}" y="{bh-6}" class="ax {"b" if v else ""}" '
                        f'text-anchor="middle">{"’" + str(yr)[2:] if v and yr % 5 else yr}</text>')
    bars.append(f'<line x1="{pl}" x2="{bw-12}" y1="{bh-20}" y2="{bh-20}" stroke="{HAIR}"/></svg>')
    bottom = panel("Shock months per year: prices calm most years, then spike together",
                   "".join(bars), CW, 150, sub="Months each year with the index 20%+ above a year earlier")
    return f'<div class="row cards3">{cards}</div><div class="row">{top}</div><div class="row">{bottom}</div>'


def exposure_tab():
    cards = "".join([
        card("Exposed countries", '20 <small>of 91</small>', "Hunger 20+ <b>and</b> imports above 16.3%",
             tone=EXPOSED, accent=EXPOSED),
        card("Average food imports", "17.4%", "Share of food supply bought abroad", accent=OTHER),
        card("Hungrier than in 2016", '24 <small>countries</small>', "",
             delta=("up", "hunger score rose since 2016", RED), accent=RED),
        card("Highest hunger score", "37.5", "Dem. Rep. Congo (Somalia has no import data)", accent=EXPOSED),
    ])
    sw, sh = 700, 470
    pl, pb, pt, pr = 36, 30, 10, 12
    iw, ih = sw - 24, sh - 92
    X = lambda v: scale(v, 0, 45, pl, iw - pr)  # noqa: E731
    Y = lambda v: scale(v, 0, 40, ih - pb, pt)  # noqa: E731
    sv = [f'<svg width="{iw}" height="{ih}">']
    for t in range(0, 41, 10):
        sv.append(f'<line x1="{pl}" x2="{iw-pr}" y1="{Y(t)}" y2="{Y(t)}" stroke="{HAIR}"/>'
                  f'<text x="{pl-6}" y="{Y(t)+4}" class="ax" text-anchor="end">{t}</text>')
    for t in range(0, 46, 10):
        sv.append(f'<text x="{X(t)}" y="{ih-14}" class="ax" text-anchor="middle">{t}%</text>')
    sv.append(f'<rect x="{X(16.3)}" y="{pt}" width="{X(45)-X(16.3)}" height="{Y(20)-pt}" fill="{EXPOSED}" opacity=".06"/>')
    sv.append(f'<line x1="{X(16.3)}" x2="{X(16.3)}" y1="{pt}" y2="{ih-pb}" stroke="{GREY}" stroke-dasharray="5 4"/>')
    sv.append(f'<line x1="{pl}" x2="{iw-pr}" y1="{Y(20)}" y2="{Y(20)}" stroke="{GREY}" stroke-dasharray="5 4"/>')
    sv.append(f'<text x="{X(16.3)+4}" y="{pt+12}" class="ax">median imports 16.3%</text>')
    sv.append(f'<text x="{pl+4}" y="{Y(20)-5}" class="ax">serious hunger 20+</text>')
    for _, r in c.sort_values("exposed").iterrows():
        col = EXPOSED if r.exposed else OTHER
        sv.append(f'<circle cx="{X(r.food_import_pct):.1f}" cy="{Y(r.ghi_2025):.1f}" r="4.5" fill="{col}" '
                  f'opacity="{0.95 if r.exposed else 0.8}"/>')
    sv.append(f'<text x="{(pl+iw)/2}" y="{ih-1}" class="ax" text-anchor="middle">Food imports, % of food supply</text>')
    sv.append("</svg>")
    scatter = panel("Exposed = hungry and import-dependent (top-right box)",
                    legend([("Exposed", EXPOSED, 0), ("Other", OTHER, 0)]) + "".join(sv), sw, sh,
                    sub="One dot per country · hunger score (GHI 2025) against food-import share")
    tw = CW - sw - 16
    top = c[c.exposed == 1].sort_values("ghi_2025", ascending=False).head(12)
    rows = []
    for _, r in top.iterrows():
        ch = r.ghi_change
        chc = RED if ch > 0 else GREEN
        arrow = ICON["up"] if ch > 0 else ICON["down"]
        rows.append(
            f'<tr><td>{flag(r.iso3)}{esc(r.country)}</td>'
            f'<td class="n"><span class="bar" style="width:{r.ghi_2025/40*70:.0f}px;background:{EXPOSED}"></span>{r.ghi_2025:.1f}</td>'
            f'<td class="n"><span class="bar" style="width:{r.food_import_pct/45*70:.0f}px;background:{OTHER}"></span>{r.food_import_pct:.1f}%</td>'
            f'<td class="n" style="color:{chc}">{arrow} {abs(ch):.1f}</td></tr>')
    table = ('<table><tr><th>Country</th><th class="n">Hunger score</th><th class="n">Food imports</th>'
             '<th class="n">Since 2016</th></tr>' + "".join(rows) + "</table>"
             '<div class="sub" style="margin-top:4px">12 of 20 shown · table pages through the rest</div>')
    tab = panel("The exposed countries, hungriest first", table, tw, sh)
    return f'<div class="row cards4">{cards}</div><div class="row">{scatter}{tab}</div>'


def warning_tab():
    def bullet(label, v, col):
        pct = max(0, min(v, 40)) / 40 * 100
        return (f'<div class="bul2"><div class="bl"><span>{label}</span><b style="color:{col}">{v:+.1f}%</b></div>'
                f'<div class="track"><i style="width:{pct:.0f}%;background:{col}"></i>'
                f'<em style="left:50%"></em></div><div class="bt"><span>0</span><span>trigger 20%</span><span>40%</span></div></div>')
    sig_card = card("Warning signal now", '<span class="dot" style="background:#9ca3af"></span>Off',
                    "Both prices must be 20%+ up", accent=AMBER)
    gauge = (f'<div class="card" style="border-left:4px solid {OILS};flex:1.6;padding-top:8px"><div class="lab">How close to the trigger '
             f'<span style="font-weight:400;text-transform:none">· Mar 2026, % vs a year earlier</span></div>'
             f'{bullet("Vegetable oils", 13.2, OILS)}{bullet("Cereals", 0.6, CEREALS)}</div>')
    rec = card("Track record since 2000", '4 <small>of 5</small>', "signals led to a shock within 1–5 months",
               tone=INK, accent=RED)
    sg = s.set_index("date")
    shade = sg.index[sg.signal_month == 1]
    main = time_chart(CW - 24, 268, [(sg.cereals_yoy, CEREALS, 2.2), (sg.oils_yoy, OILS, 1.4)], shade=shade,
                      y=(-60, 130), ticks=(-50, 0, 50, 100), ref=20, ref_label="trigger: 20% up on a year",
                      x0=pd.Timestamp("1991-01-01"), years=range(1995, 2027, 5), yfmt="{:+g}%", pl=46)
    top = panel("Oils and cereals, % change on a year earlier: shaded months = signal on",
                legend([("Vegetable oils", OILS, 0), ("Cereals", CEREALS, 0), ("Signal on", SHADE, 1)]) + main,
                CW, 330)
    runs = [("Sep – Nov 2002", "No shock followed", "False alarm", GREY),
            ("Mar 2004", "Apr 2004 spike", "1 month", RED),
            ("Dec 2006 – Apr 2007", "2007–08 shock", "5 months", RED),
            ("Aug 2010", "2010–11 shock", "1 month", RED),
            ("Nov 2020 – Feb 2021", "2021–22 shock", "4 months", RED)]
    tl = "".join(f'<div class="ev" style="border-top:3px solid {col}"><div class="lab">{esc(a)}</div>'
                 f'<div class="evb">{esc(b)}</div><div class="note" style="color:{col}">{"lead " if col == RED else ""}{esc(l)}</div></div>'
                 for a, b, l, col in runs)
    bottom = panel("Every signal since 2000, and what came next", f'<div class="tl">{tl}</div>', CW, 140)
    return (f'<div class="row cards3">{sig_card}{gauge}{rec}</div><div class="row">{top}</div>'
            f'<div class="row">{bottom}</div>')


CSS = f"""
@font-face{{font-family:GS;src:url(../../../fonts/GoogleSans-Regular.ttf)}}
@font-face{{font-family:GS;font-weight:700;src:url(../../../fonts/GoogleSans-Bold.ttf)}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#d1d5db;font-family:GS,Inter,Arial,sans-serif;color:{INK}}}
.frame{{width:{W}px;margin:0 auto 40px;background:#fff}}
.tabs{{height:40px;display:flex;justify-content:center;gap:28px;align-items:center;font-size:13px;color:{GREY};background:#fff}}
.tabs .on{{color:#1a73e8;border-bottom:2px solid #1a73e8;padding-bottom:6px;margin-top:8px}}
.canvas{{position:relative;width:{W}px;height:{H}px;background:{BG};overflow:hidden}}
header{{height:56px;background:#1f2633;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 24px}}
header h1{{font-size:24px;font-weight:700}} header span{{font-size:14px;opacity:.9}}
.rail{{position:absolute;left:{RAIL_X}px;top:{TOP}px;width:{RAIL_W}px;bottom:16px;background:#fff;border-radius:8px;padding:14px}}
.h{{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:{GREY};margin-bottom:8px}}
.h.small{{margin-bottom:4px}}
.ctl{{border:1px solid {HAIR};border-radius:6px;padding:6px 10px;margin-bottom:8px;font-size:11px;color:{GREY}}}
.ctl b{{display:block;font-size:13px;color:{INK};font-weight:400}}
.bul{{list-style:none;font-size:12.5px;line-height:1.4}}
.bul li{{display:flex;gap:8px;margin-bottom:9px}}
.bul i{{flex:none;width:8px;height:8px;border-radius:50%;margin-top:5px}}
.src{{position:absolute;bottom:14px;left:14px;right:14px;font-size:10.5px;line-height:1.4;color:{GREY}}}
main{{position:absolute;left:{CX}px;top:{TOP}px;width:{CW}px;bottom:16px;display:flex;flex-direction:column;gap:14px}}
.row{{display:flex;gap:16px}}
.card{{flex:1;background:#fff;border-radius:8px;padding:10px 14px;height:88px;position:relative}}
.lab{{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:{GREY}}}
.num{{font-size:28px;font-weight:700;line-height:1.15;margin-top:2px;display:flex;align-items:center;gap:8px}}
.num small{{font-size:13px;font-weight:400;color:{GREY}}}
.note{{font-size:12px;color:{GREY};margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.delta{{display:inline-flex;align-items:center;gap:3px;font-weight:700;margin-right:6px}}
.dot{{width:14px;height:14px;border-radius:50%;display:inline-block}}
.panel{{background:#fff;border-radius:8px;padding:12px 12px 8px;flex:none;overflow:hidden}}
.pt{{font-size:14px;font-weight:700}} .sub{{font-size:11.5px;color:{GREY};margin-top:1px}}
.legend{{display:flex;gap:16px;font-size:11.5px;color:{GREY};margin:6px 0 2px}}
.legend span{{display:flex;align-items:center;gap:5px}} .legend i{{width:14px;height:3px;display:inline-block}}
svg text.ax{{font-size:10.5px;fill:{GREY};font-family:GS,Inter,Arial}} svg text.b{{fill:{INK};font-weight:700}}
.mapph{{margin-top:10px;height:330px;border:1px dashed {OTHER};border-radius:6px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;color:{GREY};font-size:13px;padding:20px;gap:6px}}
.grad{{display:flex;align-items:center;gap:6px;font-size:11px;color:{GREY};margin-top:10px}}
.grad i{{flex:1;height:8px;border-radius:4px}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}}
th{{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:{GREY};text-align:left;padding:4px 6px;border-bottom:1px solid {HAIR}}}
td{{padding:5px 6px;border-bottom:1px solid #f1f2f4;white-space:nowrap}}
.n{{text-align:right}} .flag{{width:18px;height:13px;vertical-align:-2px;margin-right:7px;border-radius:2px;box-shadow:0 0 0 1px #0001;display:inline-block}}
.bar{{display:inline-block;height:8px;border-radius:2px;margin-right:6px;opacity:.85}}
td svg{{vertical-align:-1px}}
.bul2{{margin-top:3px}} .bl{{display:flex;justify-content:space-between;font-size:12px}}
.track{{position:relative;height:8px;background:#eef0f3;border-radius:4px;margin-top:2px}}
.track i{{position:absolute;left:0;top:0;bottom:0;border-radius:4px}}
.track em{{position:absolute;top:-3px;bottom:-3px;width:2px;background:{RED}}}
.bt{{display:none}}
.tl{{display:flex;gap:12px;margin-top:10px}} .ev{{flex:1;padding-top:8px}} .evb{{font-size:13.5px;font-weight:700;margin-top:2px}}
"""

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    body = (page("Overview", overview()) + page("The shock", shock_tab()) +
            page("The exposure", exposure_tab()) + page("The warning", warning_tab()))
    (OUT / "mock.html").write_text(f"<!doctype html><meta charset=utf-8><style>{CSS}</style>{body}")
    print(OUT / "mock.html")
