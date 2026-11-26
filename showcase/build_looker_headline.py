"""Write the five headline numbers for the Looker report as a one-row CSV.

Output: showcase/output/looker/headline.csv, loaded into the "Food price headline numbers" Google Sheet
that backs the headline cards. Every value comes from showcase/output/findings.json.

Run from the repository root after build_hero_charts.py:  python showcase/build_looker_headline.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUT = Path(__file__).parent / "output"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def month(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def main() -> None:
    f = json.loads((OUT / "findings.json").read_text())
    s, e, w, now = f["shock"], f["exposure"], f["warning"], f["now"]
    (rec_m, rec_v), (lat_m, lat_v) = s["record"], s["latest"]
    earlier = [p for p in s["peaks"] if p[0] != rec_m]
    oils, cereals = w["latest_yoy_pct"]["oils"], w["latest_yoy_pct"]["cereals"]
    thr = s["threshold_yoy_pct"]
    on = oils > thr and cereals > thr
    lead = w["lead_months"]
    row = {
        "data_to": month(lat_m),
        "now_value": f"{lat_v:.1f}",
        "now_context": f"+{now['above_base_pct']}% vs 2014-16; {now['below_record_pct']}% below record",
        "peak_value": f"{rec_v:.1f}",
        "peak_context": f"{month(rec_m)}; earlier peaks " + " and ".join(f"{v}" for m, v in earlier),
        "exposed_value": f"{e['exposed_count']} of {e['countries_plotted']}",
        "exposed_context": "Serious hunger + high food imports",
        "signal_value": "On" if on else "Off",
        "signal_context": f"Oils {oils:+.1f}%, cereals {cereals:+.1f}% (trigger {thr:.0f}%)",
        "record_value": f"{w['followed_by_shock_within_12m']} of {w['signals']}",
        "record_context": f"Followed by a shock within {min(lead)}-{max(lead)} months",
    }
    path = OUT / "looker" / "headline.csv"
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(row))
        wr.writeheader()
        wr.writerow(row)
    print(path.read_text())


if __name__ == "__main__":
    main()
