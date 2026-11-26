"""Write the two tables that back the interactive Looker Studio dashboard.

Outputs (loaded into Google Sheets that Looker reads):
  showcase/output/looker/live_monthly.csv    one row per month and food group, with year-on-year change and
                                              the shock and signal flags, so every number on the shock and
                                              warning tabs is computed live and follows the filters
  showcase/output/looker/live_countries.csv  one row per country with hunger score, food-import share and
                                              the exposed flag, for the exposure tab

The rules are the same as build_hero_charts.py: a shock month is the all-food index 20%+ above a year
earlier; a signal month is vegetable oils and cereals both 20%+ above a year earlier, outside a shock;
a country is exposed when its GHI 2025 is 20+ and its food-import share is at or above the median.

Run from the repository root:  python showcase/build_looker_live.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd  # noqa: E402

from build_hero_charts import SHOCK_THRESHOLD, compute  # noqa: E402

OUT = Path(__file__).parent / "output" / "looker"
GROUPS = {"ffpi_food": "All food", "ffpi_oils": "Vegetable oils", "ffpi_cereals": "Cereals",
          "ffpi_dairy": "Dairy", "ffpi_meat": "Meat", "ffpi_sugar": "Sugar"}


def monthly(d: dict) -> pd.DataFrame:
    ffpi, yoy = d["ffpi"], d["yoy"]
    shock = yoy["ffpi_food"] > SHOCK_THRESHOLD
    signal = (yoy["ffpi_oils"] > SHOCK_THRESHOLD) & (yoy["ffpi_cereals"] > SHOCK_THRESHOLD) & ~shock
    latest = ffpi.index.max()
    rows = []
    for col, name in GROUPS.items():
        part = pd.DataFrame({
            "date": ffpi.index.strftime("%Y-%m-%d"),
            "food_group": name,
            "price_index": ffpi[col].round(1).values,
            "yoy_pct": yoy[col].round(1).values,
            "rise_20_month": (yoy[col] > SHOCK_THRESHOLD).astype(int).values,
            "shock_month": shock.astype(int).values,
            "signal_month": signal.astype(int).values,
            "is_latest": (ffpi.index == latest).astype(int),
        })
        rows.append(part)
    out = pd.concat(rows, ignore_index=True)
    # a shock or signal month is counted once per month: flag it on the All food rows only
    not_food = out["food_group"] != "All food"
    out.loc[not_food, ["shock_month", "signal_month"]] = 0
    return out


def countries(d: dict) -> pd.DataFrame:
    df = d["df"].copy()
    med = d["median_import"]
    out = pd.DataFrame({
        "country": df["country_ghi"].replace({"Central African Republic": "Central African Rep."}),
        "iso3": df["iso3"],
        "ghi_2025": df["ghi_2025"].round(1),
        "ghi_2016": df["ghi_2016"].round(1),
        "ghi_change": (df["ghi_2025"] - df["ghi_2016"]).round(1),
        "food_import_pct": df["food_import_pct"].round(1),
        "import_year": df["year"].astype(int),
        "group": df["exposed"].map({True: "Exposed", False: "Other"}),
        "exposed": df["exposed"].astype(int),
        "worse_since_2016": ((df["ghi_2025"] - df["ghi_2016"]) > 0).astype(int),
        "median_import_pct": round(med, 1),
    })
    return out.sort_values("ghi_2025", ascending=False)


def main() -> None:
    d = compute()
    OUT.mkdir(parents=True, exist_ok=True)
    m, c = monthly(d), countries(d)
    m.to_csv(OUT / "live_monthly.csv", index=False)
    c.to_csv(OUT / "live_countries.csv", index=False)
    f = d["findings"]
    # sanity checks against the published findings
    assert c["exposed"].sum() == f["exposure"]["exposed_count"]
    assert len(c) == f["exposure"]["countries_plotted"]
    print(f"live_monthly.csv {len(m)} rows; live_countries.csv {len(c)} rows, {c['exposed'].sum()} exposed")


if __name__ == "__main__":
    main()
