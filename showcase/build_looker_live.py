"""Write the two tables that back the interactive Looker Studio dashboard.

Outputs (loaded into Google Sheets that Looker reads):
  showcase/output/looker/live_monthly.csv    one row per month and food group, with year-on-year change and
                                              the shock and signal flags, so every number on the shock and
                                              warning tabs is computed live and follows the filters
  showcase/output/looker/live_signal.csv     one row per month with oils and cereals year-on-year change
                                              side by side, for the warning tab
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

# ISO3 -> ISO2 for the flag images Looker shows in the exposure table (flagcdn.com)
ISO2 = {
    "COD": "cd", "MDG": "mg", "HTI": "ht", "NER": "ne", "CAF": "cf", "NGA": "ng", "PNG": "pg", "LBR": "lr", "AGO": "ao", "ZMB": "zm",
    "AFG": "af", "SLE": "sl", "TLS": "tl", "PAK": "pk", "BEN": "bj", "KEN": "ke", "MOZ": "mz", "IND": "in", "GNB": "gw", "ETH": "et",
    "GIN": "gn", "BFA": "bf", "COG": "cg", "MLI": "ml", "MWI": "mw", "DJI": "dj", "BWA": "bw", "RWA": "rw", "TZA": "tz", "ZWE": "zw",
    "CIV": "ci", "SLB": "sb", "UGA": "ug", "MRT": "mr", "BGD": "bd", "NAM": "na", "GAB": "ga", "GTM": "gt", "TGO": "tg", "GMB": "gm",
    "COM": "km", "CMR": "cm", "SWZ": "sz", "SEN": "sn", "MMR": "mm", "ZAF": "za", "KHM": "kh", "NPL": "np", "IDN": "id", "BOL": "bo",
    "LBY": "ly", "MYS": "my", "PHL": "ph", "MUS": "mu", "GHA": "gh", "TJK": "tj", "HND": "hn", "LKA": "lk", "VNM": "vn", "TTO": "tt",
    "ECU": "ec", "EGY": "eg", "SUR": "sr", "UKR": "ua", "JOR": "jo", "OMN": "om", "FJI": "fj", "THA": "th", "CPV": "cv", "MAR": "ma",
    "LBN": "lb", "GUY": "gy", "KGZ": "kg", "JAM": "jm", "SLV": "sv", "PAN": "pa", "IRN": "ir", "PER": "pe", "DZA": "dz", "ALB": "al",
    "ARG": "ar", "BRA": "br", "DOM": "do", "TUN": "tn", "COL": "co", "MEX": "mx", "SAU": "sa", "AZE": "az", "PRY": "py", "MDA": "md",
    "MNG": "mn",
}


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


def signal_table(d: dict) -> pd.DataFrame:
    """One row per month for the warning tab: the two signal prices side by side, plus the flags."""
    yoy = d["yoy"]
    shock = yoy["ffpi_food"] > SHOCK_THRESHOLD
    oils, cereals = yoy["ffpi_oils"] > SHOCK_THRESHOLD, yoy["ffpi_cereals"] > SHOCK_THRESHOLD
    signal = oils & cereals & ~shock
    out = pd.DataFrame({
        "date": yoy.index.strftime("%Y-%m-%d"),
        "oils_yoy": yoy["ffpi_oils"].round(1).values,
        "cereals_yoy": yoy["ffpi_cereals"].round(1).values,
        "food_yoy": yoy["ffpi_food"].round(1).values,
        "signal_month": signal.astype(int).values,
        "shock_month": shock.astype(int).values,
        "is_latest": (yoy.index == yoy.index.max()).astype(int),
        "signal_state": signal.map({True: "On", False: "Off"}).values,
    })
    return out.dropna(subset=["oils_yoy"])


def signal_runs(d: dict) -> pd.DataFrame:
    """One row per warning signal since 2000 and the shock that followed, for the warning-tab timeline."""
    w = d["findings"]["warning"]
    month = lambda ym: pd.Timestamp(ym + "-01").strftime("%b %Y")  # noqa: E731
    names = {"2004-04": "Apr 2004 spike", "2007-05": "2007-08 shock", "2010-09": "2010-11 shock",
             "2021-03": "2021-22 shock"}
    rows = []
    for start, end, shock in w["signal_runs"]:
        lead = None if shock is None else (pd.Period(shock, "M") - pd.Period(start, "M")).n
        rows.append({
            "signal_start": start + "-01",
            "signal_months": month(start) if start == end else f"{month(start)} - {month(end)}",
            "what_followed": names.get(shock, "No shock followed"),
            "lead": "False alarm" if lead is None else f"{lead} month{'s' if lead > 1 else ''}",
            "outcome": "False alarm" if lead is None else "Shock followed",
        })
    return pd.DataFrame(rows)


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
        "flag_url": df["iso3"].map(lambda c: f"https://flagcdn.com/w40/{ISO2[c]}.png"),
        "change_arrow": ((df["ghi_2025"] - df["ghi_2016"]) > 0).map({True: "▲", False: "▼"}),
    })
    return out.sort_values("ghi_2025", ascending=False)


def main() -> None:
    d = compute()
    OUT.mkdir(parents=True, exist_ok=True)
    m, c = monthly(d), countries(d)
    m.to_csv(OUT / "live_monthly.csv", index=False)
    c.to_csv(OUT / "live_countries.csv", index=False)
    sig = signal_table(d)
    sig.to_csv(OUT / "live_signal.csv", index=False)
    runs = signal_runs(d)
    runs.to_csv(OUT / "live_signal_runs.csv", index=False)
    assert list(runs["lead"].str.extract(r"(\d+)")[0].dropna().astype(int)) == d["findings"]["warning"]["lead_months"]
    f = d["findings"]
    # sanity checks against the published findings
    assert c["exposed"].sum() == f["exposure"]["exposed_count"]
    assert len(c) == f["exposure"]["countries_plotted"]
    print(f"live_monthly.csv {len(m)} rows; live_countries.csv {len(c)} rows, {c['exposed'].sum()} exposed")


if __name__ == "__main__":
    main()
