"""Mock two vertical layouts for the Looker "The warning" tab, with signal annotations on the chart.

A: tall line chart (full main height), cards stacked on the right, compact signal table under them.
B: same layout, but the chart is vertical columns: the weaker of the two price changes each month
   (the signal is on when even the weaker one is 20%+ up), amber where the signal is on.

Run from the repository root:  python showcase/build_looker_warning_mock.py
Output: showcase/output/looker/mock/warning-vertical.html
"""

from __future__ import annotations

import pandas as pd

import build_looker_mock as bm
from build_looker_mock import (AMBER, CEREALS, GREEN, GREY, HAIR, INK, OILS, RED, SHADE, esc, page, scale)

s = pd.read_csv(bm.LOOK / "live_signal.csv", parse_dates=["date"]).set_index("date")
s["weaker"] = s[["oils_yoy", "cereals_yoy"]].min(axis=1)

# signal runs: (first month, last month, label line 1, label line 2, colour)
RUNS = [("2002-09", "2002-11", "2002", "false alarm", GREY),
        ("2004-03", "2004-03", "2004", "spike 1 mo later", RED),
        ("2006-12", "2007-04", "2007", "shock 5 mo later", RED),
        ("2010-08", "2010-08", "2010", "shock 1 mo later", RED),
        ("2020-11", "2021-02", "2021", "shock 4 mo later", RED)]

X0, X1 = pd.Timestamp("1991-01-01"), pd.Timestamp("2026-03-01")
CHART_W, MAIN_H = 900, 608          # Looker: chart box 296,72 -> 1196,680
SIDE_X = 296 + CHART_W + 16          # 1212
SIDE_W = 1580 - SIDE_X               # 368


def chart(kind: str, w: int, h: int) -> str:
    pl, pr, pt, pb = 44, 10, 84, 22   # top padding leaves room for annotation labels
    y0, y1 = (-60, 130) if kind == "line" else (-55, 100)
    X = lambda d: scale(d.value, X0.value, X1.value, pl, w - pr)
    Y = lambda v: scale(v, y0, y1, h - pb, pt)
    step = (X(X1) - X(X0)) / ((X1.year - X0.year) * 12 + X1.month - X0.month)
    o = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    ticks = (-50, 0, 50, 100) if kind == "line" else (-40, 0, 40, 80)
    for t in ticks:
        o.append(f'<line x1="{pl}" x2="{w-pr}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{HAIR}"/>'
                 f'<text x="{pl-6}" y="{Y(t)+4:.1f}" class="ax" text-anchor="end">{t:+g}%</text>')
    if kind == "line":
        for d in s.index[s.signal_month == 1]:
            o.append(f'<rect x="{X(d):.1f}" y="{pt}" width="{step:.1f}" height="{h-pb-pt}" fill="{SHADE}"/>')
        for col, sw, key in ((OILS, 1.3, "oils_yoy"), (CEREALS, 2, "cereals_yoy")):
            pts = " ".join(f"{X(d):.1f},{Y(v):.1f}" for d, v in s[key].items())
            o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{sw}"/>')
    else:
        for d, v in s.weaker.items():
            v = max(min(v, y1), y0)
            col = AMBER if s.signal_month[d] else "#B9C2CA"
            top, bot = (Y(v), Y(0)) if v >= 0 else (Y(0), Y(v))
            o.append(f'<rect x="{X(d):.1f}" y="{top:.1f}" width="{max(step-0.4,1):.1f}" height="{bot-top:.1f}" fill="{col}"/>')
    o.append(f'<line x1="{pl}" x2="{w-pr}" y1="{Y(20):.1f}" y2="{Y(20):.1f}" stroke="{GREY}" stroke-dasharray="5 4"/>'
             f'<text x="{w-pr-4}" y="{Y(20)-5:.1f}" class="ax b" text-anchor="end">trigger: 20% up</text>')
    # annotations: label above each run, thin leader down to the run
    lane = [14, 32, 50, 68, 14]   # one lane per label, so no leader crosses another label
    for i, (a, b, l1, l2, col) in enumerate(RUNS):
        xa, xb = X(pd.Timestamp(a)), X(pd.Timestamp(b)) + step
        xm = (xa + xb) / 2
        ly = lane[i]
        o.append(f'<line x1="{xm:.1f}" x2="{xm:.1f}" y1="{ly-10}" y2="{pt}" stroke="{col}" stroke-width="1"/>'
                 f'<text x="{xm+4:.1f}" y="{ly}" class="ann" fill="{col}">'
                 f'<tspan font-weight="700">{l1}</tspan> {esc(l2)}</text>')
    for yr in range(1995, 2027, 5):
        o.append(f'<text x="{X(pd.Timestamp(f"{yr}-01-01")):.1f}" y="{h-6}" class="ax" text-anchor="middle">{yr}</text>')
    o.append("</svg>")
    return "".join(o)


def legend(items):
    return '<div class="lg">' + "".join(
        f'<span><i style="background:{c};{"height:9px" if box else ""}"></i>{esc(t)}</span>' for t, c, box in items) + "</div>"


def card(label, value, col, note=""):
    return (f'<div class="vc"><div class="lab">{esc(label)}</div><div class="vn" style="color:{col}">{value}</div>'
            f'{f"<div class=note>{esc(note)}</div>" if note else ""}</div>')


def side():
    up = '<svg width="16" height="16" viewBox="0 0 12 12"><path d="M6 1 11 10H1z" fill="currentColor"/></svg>'
    cards = (card("Warning signal now", "Off", GREEN) + card("Vegetable oils now", f"{up}+13.2%", RED) +
             card("Cereals now", f"{up}+0.6%", RED) + card("Signal months", "13", AMBER))
    rows = "".join(f'<tr><td>{esc(r.signal_months.replace(" - ", " to "))}</td>'
                   f'<td style="color:{GREY if r.lead == "False alarm" else RED}">{esc(r.what_followed)}</td>'
                   f'<td class="n">{esc(r.lead)}</td></tr>'
                   for r in pd.read_csv(bm.LOOK / "live_signal_runs.csv").itertuples())
    table = (f'<div class="panel" style="height:196px"><div class="pt">4 of 5 signals were followed by a shock</div>'
             f'<table><tr><th>Signal on</th><th>What followed</th><th class="n">After</th></tr>{rows}</table></div>')
    return f'<div class="side"><div class="cards">{cards}</div>{table}</div>'


def tab(kind):
    if kind == "line":
        title = "Oils and cereals, % change on a year earlier; shaded = signal on (both 20%+ up)"
        lg = legend([("Vegetable oils", OILS, 0), ("Cereals", CEREALS, 0), ("Signal on", SHADE, 1)])
    else:
        title = "The weaker of oils and cereals, % change on a year earlier; amber = signal on (both 20%+ up)"
        lg = legend([("Signal on", AMBER, 1), ("Signal off", "#B9C2CA", 1)])
    ch = (f'<div class="panel" style="width:{CHART_W}px;height:{MAIN_H}px"><div class="pt">{esc(title)}</div>'
          f'{lg}{chart(kind, CHART_W - 24, MAIN_H - 66)}</div>')
    return f'<div class="row" style="height:{MAIN_H}px">{ch}{side()}</div>'


CSS = bm.CSS + f"""
main{{gap:0}} .pt{{font-size:13px;font-weight:400;color:{INK}}}
.lg{{display:flex;gap:14px;font-size:11px;color:{GREY};margin:6px 0 0}}
.lg span{{display:flex;align-items:center;gap:5px}} .lg i{{width:12px;height:2px;display:inline-block}}
svg text.ann{{font-size:11px;font-family:GS,Inter,Arial}}
.side{{width:{SIDE_W}px;display:flex;flex-direction:column;gap:16px}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.vc{{background:#fff;border-radius:8px;padding:10px 14px;height:88px}}
.vn{{font-size:28px;line-height:1.2;margin-top:4px;display:flex;align-items:center;gap:6px}}
.side table{{font-size:11.5px}} .side td{{padding:5px 4px}} .side th{{padding:4px}}
.cap{{width:1600px;margin:0 auto 8px;font:600 15px GS,Arial;color:{INK}}}
"""

if __name__ == "__main__":
    body = ('<div class="cap">A. Tall line chart with signal labels</div>' + page("The warning", tab("line")) +
            '<div class="cap">B. Vertical columns: the weaker of the two changes each month</div>' +
            page("The warning", tab("cols")))
    out = bm.OUT / "warning-vertical.html"
    out.write_text(f"<!doctype html><meta charset=utf-8><style>{CSS}</style>{body}")
    print(out)
