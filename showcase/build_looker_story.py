"""Build the figure cards for the Looker Studio story page.

Outputs (showcase/output/looker/): story-1-shock.png, story-2-exposure.png, story-3-warning.png
Each card carries the deck's finding title, legend, chart, takeaway and source, so the Looker story page
shows the same figures as the slides. Every number comes from build_hero_charts.compute().

Run from the repository root:  python showcase/build_looker_story.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import build_hero_charts as hc
import build_showcase as bs

HERE = Path(__file__).parent
OUT = hc.OUT / "looker"
W, H = 1200, 640  # CSS px per card; rendered at 2x

CSS = """
* { box-sizing: border-box; margin: 0; }
body { font-family: 'Google Sans', sans-serif; color: #1B2430; background: #fff; }
.card { width: %dpx; height: %dpx; padding: 28px 36px 22px; display: flex; flex-direction: column; background: #fff; }
.ch { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--a); }
h2 { font-size: 30px; line-height: 1.15; margin: 6px 0 4px; }
.sub { font-size: 15px; color: #5A6370; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 18px; font-size: 13px; color: #5A6370; margin: 12px 0 4px; }
.key { display: inline-flex; align-items: center; gap: 6px; }
.key i { display: inline-block; }
.k-line { width: 18px; height: 3px; border-radius: 2px; background: var(--c); }
.k-dot { width: 10px; height: 10px; border-radius: 50%%; background: var(--c); }
.k-band { width: 15px; height: 11px; background: color-mix(in srgb, var(--c) 32%%, white); }
.k-box { width: 15px; height: 8px; background: var(--c); }
.fig { flex: 1; min-height: 0; }
.fig svg { width: 100%%; height: 100%%; display: block; }
.take { border-left: 4px solid #B8452E; padding: 2px 0 2px 12px; font-size: 17px; font-weight: 700; margin-top: 6px; }
.src { font-size: 11.5px; color: #5A6370; margin-top: 8px; }
""" % (W, H)


def card(key: str, c: dict, fig: str) -> str:
    name, accent, _ = bs.CH[key]
    src = c.get("source", "")
    return (f'<div class="card" style="--a:{accent}"><div class="ch">{name}</div>'
            f'<h2>{bs.esc(c["title"])}</h2><div class="sub">{bs.esc(c["subtitle"])}</div>'
            f'{bs.legend(c["legend"])}<div class="fig">{fig}</div>'
            f'<div class="take">{bs.esc(c["take"])}</div><div class="src">{bs.esc(src)}</div></div>')


def main() -> None:
    bs.DATA = hc.main()
    f = bs.DATA["findings"]
    copy = bs.story(f)
    OUT.mkdir(parents=True, exist_ok=True)
    fw = (W - 72) * 0.75  # figure width in pt
    cards = {
        "1-shock": card("shock", copy["shock"], bs.svg("shock", fw, 330, 11)),
        "2-exposure": card("exposure", copy["exposure"],
                           bs.svg("exposure", fw, 310, 11, labels=["Haiti", "Madagascar", "Yemen", "Somalia"])),
        "3-warning": card("warning", copy["warning"], bs.svg("warning", fw, 320, 11)),
    }
    for name, body in cards.items():
        html_path = OUT / f"story-{name}.html"
        html_path.write_text(
            f'<!doctype html><html><head><meta charset="utf-8"><style>{bs.font_css("../../fonts/")}{CSS}</style>'
            f'</head><body>{body}</body></html>')
    subprocess.run(["node", str(HERE / "render_cards.mjs"), str(OUT), str(W), str(H)], check=True)
    print("Built Looker story cards in", OUT)


if __name__ == "__main__":
    main()
