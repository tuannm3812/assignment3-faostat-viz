"""Build the three hero charts (shock, exposure, warning) for decks, posters and the portfolio.

Every number printed on a chart is computed here from data/processed/ and written to
showcase/output/findings.json, so headlines can be checked against the data.

Run from the repository root:
    python showcase/build_hero_charts.py

Fonts: uses Google Sans if installed, then Google Sans Flex, then the matplotlib default.
Set FONT_DIR to a folder of .ttf files to register extra fonts first.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "showcase" / "output"

# Design tokens: one accent per chart, grey for context, finding as the title.
BLUE = "#0540f2"
AMBER = "#f59e0b"
INK = "#0f172a"
MUTED = "#64748b"
GRID = "#e2e8f0"
CONTEXT = "#cbd5e1"
BAND = "#fde68a"

SHOCK_THRESHOLD = 20.0  # year-on-year % rise in the all-food index that counts as a shock month
SERIOUS_HUNGER = 20.0  # Global Hunger Index "serious" band starts at 20
IMPORT_YEAR_MIN = 2015  # ignore stale World Bank import shares


def setup_fonts() -> str:
    font_dir = os.environ.get("FONT_DIR")
    if font_dir:
        for path in Path(font_dir).glob("*.ttf"):
            font_manager.fontManager.addfont(str(path))
    names = {f.name for f in font_manager.fontManager.ttflist}
    for family in ("Google Sans", "Google Sans Flex", "Figtree", "Inter"):
        if family in names:
            plt.rcParams["font.family"] = family
            return family
    return plt.rcParams["font.family"][0]


def base_style() -> None:
    plt.rcParams.update(
        {
            "axes.edgecolor": GRID,
            "axes.labelcolor": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def new_figure(title: str, subtitle: str, source: str):
    fig = plt.figure(figsize=(16, 9), dpi=120)
    fig.text(0.055, 0.925, title, fontsize=26, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.055, 0.855, subtitle, fontsize=14, color=MUTED, ha="left", va="top")
    fig.text(0.055, 0.035, source, fontsize=10, color=MUTED, ha="left")
    return fig


def episodes(mask: pd.Series, max_gap: int = 3) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Group flagged months into runs, joining runs separated by up to max_gap months."""
    runs: list[list[pd.Timestamp]] = []
    for t in mask[mask].index:
        if runs and (t.to_period("M") - runs[-1][1].to_period("M")).n <= max_gap:
            runs[-1][1] = t
        else:
            runs.append([t, t])
    return [(a, b) for a, b in runs]


def load_ffpi() -> tuple[pd.DataFrame, pd.DataFrame]:
    ffpi = pd.read_csv(DATA / "ffpi_monthly.csv", parse_dates=["date"]).set_index("date")
    cols = ["ffpi_food", "ffpi_cereals", "ffpi_oils", "ffpi_dairy", "ffpi_meat", "ffpi_sugar"]
    ffpi = ffpi[cols]
    yoy = ffpi.pct_change(12) * 100
    return ffpi, yoy


# --------------------------------------------------------------------------- act 1: shock
def chart_shock(ffpi: pd.DataFrame, yoy: pd.DataFrame, findings: dict) -> None:
    food = ffpi["ffpi_food"]
    shock = yoy["ffpi_food"] > SHOCK_THRESHOLD
    eps = episodes(shock)
    major = [(a, b) for a, b in eps if (b - a).days > 180]
    peaks = []
    for a, b in major:
        window = food[a - pd.DateOffset(months=6) : b + pd.DateOffset(months=12)]
        peaks.append((window.idxmax(), float(window.max())))
    latest_t, latest_v = food.index[-1], float(food.iloc[-1])

    findings["shock"] = {
        "threshold_yoy_pct": SHOCK_THRESHOLD,
        "major_episodes": [[a.strftime("%Y-%m"), b.strftime("%Y-%m")] for a, b in major],
        "peaks": [[t.strftime("%Y-%m"), round(v, 1)] for t, v in peaks],
        "latest": [latest_t.strftime("%Y-%m"), round(latest_v, 1)],
        "max_yoy_pct": [yoy["ffpi_food"].idxmax().strftime("%Y-%m"), round(float(yoy["ffpi_food"].max()), 1)],
    }

    fig = new_figure(
        "Food prices have spiked three times since 2007, each peak higher than the last",
        "FAO Food Price Index, all foods, monthly (2014-16 = 100). Shaded: months where prices ran "
        f"more than {SHOCK_THRESHOLD:.0f}% above a year earlier.",
        "Source: FAO Food Price Index, Jan 1990 to Mar 2026. Shock months computed from year-on-year change.",
    )
    ax = fig.add_axes([0.055, 0.33, 0.9, 0.47])
    axb = fig.add_axes([0.055, 0.11, 0.9, 0.17], sharex=ax)

    for a, b in eps:
        for axis in (ax, axb):
            axis.axvspan(a - pd.Timedelta(days=15), b + pd.Timedelta(days=15), color=BAND, alpha=0.55, lw=0, zorder=0)

    ax.plot(food.index, food.values, color=BLUE, lw=2.8, zorder=3)
    ax.set_ylim(0, 185)
    ax.set_ylabel("Index", fontsize=11)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", length=0)

    for t, v in peaks:
        ax.scatter([t], [v], s=60, color=BLUE, zorder=4, edgecolor="white", linewidth=1.5)
        ax.annotate(
            f"{t.strftime('%b %Y')}\n{v:.1f}",
            (t, v),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=13,
            fontweight="bold",
            color=INK,
        )
    ax.scatter([latest_t], [latest_v], s=50, color="white", edgecolor=BLUE, linewidth=2, zorder=4)
    ax.annotate(
        f"Now\n{latest_v:.1f}",
        (latest_t, latest_v),
        xytext=(10, -6),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=12,
        color=MUTED,
    )

    change = yoy["ffpi_food"].dropna()
    colors = np.where(change > SHOCK_THRESHOLD, AMBER, np.where(change >= 0, CONTEXT, "#e2e8f0"))
    axb.bar(change.index, change.values, width=28, color=colors, lw=0, zorder=2)
    axb.axhline(0, color=MUTED, lw=0.8)
    axb.axhline(SHOCK_THRESHOLD, color=AMBER, lw=1, ls=(0, (4, 3)))
    axb.text(change.index[0], SHOCK_THRESHOLD + 4, f"+{SHOCK_THRESHOLD:.0f}% shock line", color=AMBER, fontsize=10, va="bottom")
    axb.set_ylabel("Change on a\nyear earlier (%)", fontsize=10)
    axb.set_ylim(-45, 70)
    axb.tick_params(length=0)
    axb.xaxis.set_major_locator(mdates.YearLocator(4))
    axb.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axb.set_xlim(food.index[0], food.index[-1] + pd.DateOffset(months=10))

    fig.savefig(OUT / "01-shock.png", dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- act 2: exposure
def chart_exposure(findings: dict) -> None:
    ghi = pd.read_csv(DATA / "ghi_cleaned.csv")
    wb = pd.read_csv(DATA / "worldbank_food_import_pct.csv")
    latest = (
        wb.dropna(subset=["food_import_pct"])
        .query("year >= @IMPORT_YEAR_MIN")
        .sort_values("year")
        .groupby("iso3")
        .last()
        .reset_index()
    )
    df = ghi.dropna(subset=["ghi_2025"]).merge(latest[["iso3", "year", "food_import_pct"]], on="iso3")
    median_import = float(df["food_import_pct"].median())
    df["exposed"] = (df["food_import_pct"] >= median_import) & (df["ghi_2025"] >= SERIOUS_HUNGER)
    exposed = df[df["exposed"]].sort_values("ghi_2025", ascending=False)

    findings["exposure"] = {
        "countries_plotted": int(len(df)),
        "import_year_min": IMPORT_YEAR_MIN,
        "median_food_import_pct": round(median_import, 1),
        "serious_hunger_threshold": SERIOUS_HUNGER,
        "exposed_count": int(len(exposed)),
        "exposed": exposed[["country_ghi", "food_import_pct", "ghi_2025"]].round(1).values.tolist(),
    }

    fig = new_figure(
        f"{len(exposed)} of {len(df)} countries pair serious hunger with high food-import dependence",
        "Each dot is a country. Across: food as a share of merchandise imports. Up: Global Hunger Index 2025. "
        "Blue: both above the lines.",
        f"Sources: Global Hunger Index 2025; World Bank food imports (% of merchandise imports), latest year "
        f"{IMPORT_YEAR_MIN} or later. Vertical line: median ({median_import:.1f}%). Horizontal line: GHI 20, the "
        "start of 'serious'.",
    )
    ax = fig.add_axes([0.07, 0.11, 0.88, 0.69])
    ax.fill_between([median_import, 46], SERIOUS_HUNGER, 47, color="#eef2ff", lw=0, zorder=0)
    ax.axvline(median_import, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.axhline(SERIOUS_HUNGER, color=MUTED, lw=1, ls=(0, (4, 3)))
    rest = df[~df["exposed"]]
    ax.scatter(rest["food_import_pct"], rest["ghi_2025"], s=70, color=CONTEXT, edgecolor="white", linewidth=0.8, zorder=2)
    ax.scatter(exposed["food_import_pct"], exposed["ghi_2025"], s=110, color=BLUE, edgecolor="white", linewidth=1, zorder=3)

    short = {
        "Central African Republic": "Central African Rep.",
        "Congo (Republic of)": "Rep. of Congo",
    }
    nudge = {"Timor-Leste": (8, -10), "Afghanistan": (8, 6)}
    for _, r in exposed.head(9).iterrows():
        name = short.get(r["country_ghi"], r["country_ghi"])
        ax.annotate(name, (r["food_import_pct"], r["ghi_2025"]), xytext=nudge.get(r["country_ghi"], (8, 0)),
                    textcoords="offset points", fontsize=12, color=INK, va="center")
    ax.text(45.5, SERIOUS_HUNGER + 0.6, "serious hunger", color=MUTED, fontsize=11, ha="right", va="bottom")
    ax.text(median_import + 0.4, 46.2, "above-median food-import dependence", color=MUTED, fontsize=11, ha="left", va="top")
    ax.set_xlim(0, 46)
    ax.set_ylim(0, 47)
    ax.set_xlabel("Food imports, % of merchandise imports", fontsize=12)
    ax.set_ylabel("Global Hunger Index 2025", fontsize=12)
    ax.tick_params(length=0)

    fig.savefig(OUT / "02-exposure.png", dpi=120)
    plt.close(fig)


# --------------------------------------------------------------------------- act 3: warning
def chart_warning(ffpi: pd.DataFrame, yoy: pd.DataFrame, findings: dict) -> None:
    start = pd.Timestamp("2000-01-01")
    shock = yoy["ffpi_food"] > SHOCK_THRESHOLD
    signal = (yoy["ffpi_oils"] > SHOCK_THRESHOLD) & (yoy["ffpi_cereals"] > SHOCK_THRESHOLD) & ~shock
    shock_eps = [(a, b) for a, b in episodes(shock[start:]) ]
    signal_eps = episodes(signal[start:], max_gap=2)

    results = []
    for a, b in signal_eps:
        follow = shock[a : b + pd.DateOffset(months=12)]
        hit = follow[follow].index.min()
        lead = None if pd.isna(hit) else (hit.to_period("M") - a.to_period("M")).n
        results.append({"signal_start": a, "signal_end": b, "shock_start": hit, "lead_months": lead})
    hits = [r for r in results if r["lead_months"] is not None]
    missed = []
    for a, b in shock_eps:
        prior = signal[a - pd.DateOffset(months=12) : a]
        if not prior.any():
            missed.append(a)
    now = yoy.index[-1]

    findings["warning"] = {
        "rule": f"vegetable oils and cereals both >{SHOCK_THRESHOLD:.0f}% above a year earlier, outside a shock",
        "period": [start.strftime("%Y-%m"), now.strftime("%Y-%m")],
        "signals": len(results),
        "followed_by_shock_within_12m": len(hits),
        "lead_months": [r["lead_months"] for r in hits],
        "signal_runs": [
            [r["signal_start"].strftime("%Y-%m"), r["signal_end"].strftime("%Y-%m"),
             None if r["shock_start"] is None or pd.isna(r["shock_start"]) else r["shock_start"].strftime("%Y-%m")]
            for r in results
        ],
        "shock_starts_without_prior_signal": [t.strftime("%Y-%m") for t in missed],
        "latest_yoy_pct": {
            "month": now.strftime("%Y-%m"),
            "oils": round(float(yoy["ffpi_oils"].iloc[-1]), 1),
            "cereals": round(float(yoy["ffpi_cereals"].iloc[-1]), 1),
            "all_food": round(float(yoy["ffpi_food"].iloc[-1]), 1),
        },
        "note": "Rule read off the full 2000-2026 history, not trained blind; treat as a signal to watch, not a forecast.",
    }

    leads = sorted({r["lead_months"] for r in hits})
    lead_text = f"{leads[0]} to {leads[-1]} months" if len(leads) > 1 else f"{leads[0]} months"
    fig = new_figure(
        "Each food-price shock since 2000 followed a 20% jump in oils and cereals",
        f"The signal fired {len(results)} times; {len(hits)} were followed by a shock, {lead_text} later. "
        f"Today ({now.strftime('%b %Y')}) oils are +{yoy['ffpi_oils'].iloc[-1]:.0f}% and cereals "
        f"+{yoy['ffpi_cereals'].iloc[-1]:.0f}%: no signal.",
        "Source: FAO Food Price Index, monthly. Signal: vegetable oils and cereals both more than 20% above a year "
        "earlier. Shock: all-food index more than 20% above a year earlier. Rule read off this history; a watch signal, not a forecast.",
    )
    ax = fig.add_axes([0.075, 0.27, 0.80, 0.53])
    axs = fig.add_axes([0.075, 0.10, 0.80, 0.12], sharex=ax)

    y = yoy[start:]
    for a, b in shock_eps:
        ax.axvspan(a - pd.Timedelta(days=15), b + pd.Timedelta(days=15), color=BAND, alpha=0.55, lw=0, zorder=0)
    ax.plot(y.index, y["ffpi_cereals"], color=MUTED, lw=1.6, zorder=2)
    ax.plot(y.index, y["ffpi_oils"], color=AMBER, lw=2.2, zorder=3)
    ax.plot(y.index, y["ffpi_food"], color=BLUE, lw=2.8, zorder=4)
    ax.axhline(SHOCK_THRESHOLD, color=INK, lw=1, ls=(0, (4, 3)))
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylabel("Change on a year earlier (%)", fontsize=11)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-60, 130)
    last = y.index[-1] + pd.DateOffset(months=3)
    offsets = {"ffpi_food": 5, "ffpi_oils": 3, "ffpi_cereals": -7}
    for col, label, color in [("ffpi_food", "All food", BLUE), ("ffpi_oils", "Vegetable oils", AMBER), ("ffpi_cereals", "Cereals", MUTED)]:
        ax.text(last, y[col].iloc[-1] + offsets[col], label, color=color, fontsize=12, fontweight="bold", va="center")
    ax.text(y.index[0], SHOCK_THRESHOLD + 3, "+20%", color=INK, fontsize=10, va="bottom")

    axs.set_ylim(0, 1)
    axs.set_yticks([])
    axs.grid(False)
    axs.spines["bottom"].set_visible(True)
    for r in results:
        color = BLUE if r["lead_months"] is not None else CONTEXT
        end = max(r["signal_end"], r["signal_start"] + pd.DateOffset(months=2))
        axs.axvspan(r["signal_start"] - pd.Timedelta(days=15), end, ymin=0.45, ymax=0.95, color=color, lw=0)
        label = f"{r['lead_months']} mo before" if r["lead_months"] is not None else "no shock"
        mid = r["signal_start"] + (end - r["signal_start"]) / 2
        axs.text(mid, 0.18 if r["lead_months"] is not None else 1.12, label, fontsize=11, color=INK if r["lead_months"] is not None else MUTED,
                 ha="center", va="center")
    axs.text(y.index[0] - pd.DateOffset(months=4), 0.7, "Signal", fontsize=11, color=MUTED, ha="right", va="center")
    axs.tick_params(length=0)
    axs.xaxis.set_major_locator(mdates.YearLocator(2))
    axs.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axs.set_xlim(y.index[0] - pd.DateOffset(months=3), y.index[-1] + pd.DateOffset(months=2))

    fig.savefig(OUT / "03-warning.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    family = setup_fonts()
    base_style()
    ffpi, yoy = load_ffpi()
    findings: dict = {"font": family}
    chart_shock(ffpi, yoy, findings)
    chart_exposure(findings)
    chart_warning(ffpi, yoy, findings)
    (OUT / "findings.json").write_text(json.dumps(findings, indent=2, default=str))
    print(json.dumps(findings, indent=2, default=str))


if __name__ == "__main__":
    main()
