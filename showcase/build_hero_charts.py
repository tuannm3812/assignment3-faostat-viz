"""Compute the food-price story and draw its three charts in the UTS deck kit style.

Every number used on a chart, slide or poster is computed here from data/processed/ and
written to showcase/output/findings.json, so headlines can be checked against the data.

Run from the repository root:
    python showcase/build_hero_charts.py      # findings.json + 16:9 hero PNGs
    python showcase/build_showcase.py         # slides and poster (calls this module)

Style follows the UTS deck kit (palette A for structure, Viridis for data, Google Sans).
Data colours keep one meaning everywhere:
    all-food index  #3B528B   vegetable oils  #21918C   cereals  #35B779
    shock months    Viridis yellow #FDE725 (pale band)
    exposed country #440154   other countries #B9C2CA   signal  ink #1B2430
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "showcase" / "output"
FONTS = ROOT / "showcase" / "fonts"

# Palette A structure tokens (UTS deck kit, templates/deck-kit.json)
INK = "#1B2430"
BODY = "#5A6370"
RULE = "#89949D"
HAIR = "#D8DEE3"

# Viridis data colours, one meaning each
FOOD = "#3B528B"
OILS = "#21918C"
CEREALS = "#35B779"
SHOCK = "#FDE725"
EXPOSED = "#440154"
EXPOSED_ZONE = "#F1ECF4"
OTHER = "#B9C2CA"
SIGNAL = INK

SHOCK_THRESHOLD = 20.0  # year-on-year % rise in the all-food index that counts as a shock month
SERIOUS_HUNGER = 20.0  # Global Hunger Index "serious" band starts at 20
IMPORT_YEAR_MIN = 2015  # ignore stale World Bank import shares
SIGNAL_START = pd.Timestamp("2000-01-01")


# --------------------------------------------------------------------------- data
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


def compute() -> dict:
    """Return everything the charts need (frames and the findings dict)."""
    ffpi, yoy = load_ffpi()
    food = ffpi["ffpi_food"]
    shock = yoy["ffpi_food"] > SHOCK_THRESHOLD
    eps = episodes(shock)
    major = [(a, b) for a, b in eps if (b - a).days > 180]
    peaks = []
    for a, b in major:
        window = food[a - pd.DateOffset(months=6) : b + pd.DateOffset(months=12)]
        peaks.append((window.idxmax(), float(window.max())))
    latest_t, latest_v = food.index[-1], float(food.iloc[-1])

    findings: dict = {
        "shock": {
            "threshold_yoy_pct": SHOCK_THRESHOLD,
            "major_episodes": [[a.strftime("%Y-%m"), b.strftime("%Y-%m")] for a, b in major],
            "peaks": [[t.strftime("%Y-%m"), round(v, 1)] for t, v in peaks],
            "record": [food.idxmax().strftime("%Y-%m"), round(float(food.max()), 1)],
            "series_start": food.index[0].strftime("%Y-%m"),
            "latest": [latest_t.strftime("%Y-%m"), round(latest_v, 1)],
            "max_yoy_pct": [yoy["ffpi_food"].idxmax().strftime("%Y-%m"), round(float(yoy["ffpi_food"].max()), 1)],
        }
    }

    # exposure
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
        "import_year_max": int(df["year"].max()),
        "median_food_import_pct": round(median_import, 1),
        "serious_hunger_threshold": SERIOUS_HUNGER,
        "exposed_count": int(len(exposed)),
        "exposed": exposed[["country_ghi", "food_import_pct", "ghi_2025"]].round(1).values.tolist(),
    }

    # warning
    signal = (yoy["ffpi_oils"] > SHOCK_THRESHOLD) & (yoy["ffpi_cereals"] > SHOCK_THRESHOLD) & ~shock
    shock_eps = episodes(shock[SIGNAL_START:])
    signal_eps = episodes(signal[SIGNAL_START:], max_gap=2)
    results = []
    for a, b in signal_eps:
        follow = shock[a : b + pd.DateOffset(months=12)]
        hit = follow[follow].index.min()
        lead = None if pd.isna(hit) else (hit.to_period("M") - a.to_period("M")).n
        results.append({"start": a, "end": b, "shock_start": None if pd.isna(hit) else hit, "lead": lead})
    hits = [r for r in results if r["lead"] is not None]
    missed = [a for a, _ in shock_eps if not signal[a - pd.DateOffset(months=12) : a].any()]
    now = yoy.index[-1]
    findings["warning"] = {
        "rule": f"vegetable oils and cereals both >{SHOCK_THRESHOLD:.0f}% above a year earlier, outside a shock",
        "period": [SIGNAL_START.strftime("%Y-%m"), now.strftime("%Y-%m")],
        "signals": len(results),
        "followed_by_shock_within_12m": len(hits),
        "lead_months": [r["lead"] for r in hits],
        "signal_runs": [
            [r["start"].strftime("%Y-%m"), r["end"].strftime("%Y-%m"),
             None if r["shock_start"] is None else r["shock_start"].strftime("%Y-%m")]
            for r in results
        ],
        "shock_episodes_since_2000": len(shock_eps),
        "shock_starts_without_prior_signal": [t.strftime("%Y-%m") for t in missed],
        "latest_yoy_pct": {
            "month": now.strftime("%Y-%m"),
            "oils": round(float(yoy["ffpi_oils"].iloc[-1]), 1),
            "cereals": round(float(yoy["ffpi_cereals"].iloc[-1]), 1),
            "all_food": round(float(yoy["ffpi_food"].iloc[-1]), 1),
        },
        "note": "Rule read off the full 2000-2026 history, not trained blind; treat as a signal to watch, not a forecast.",
    }
    return {
        "ffpi": ffpi, "yoy": yoy, "eps": eps, "peaks": peaks, "latest": (latest_t, latest_v),
        "df": df, "exposed": exposed, "median_import": median_import,
        "shock_eps": shock_eps, "signals": results, "findings": findings,
    }


# --------------------------------------------------------------------------- style
def setup_fonts() -> str:
    for path in FONTS.glob("*.ttf"):
        font_manager.fontManager.addfont(str(path))
    names = {f.name for f in font_manager.fontManager.ttflist}
    family = "Google Sans" if "Google Sans" in names else "DejaVu Sans"
    plt.rcParams.update(
        {
            "font.family": family,
            "svg.fonttype": "none",  # keep real text in SVG so pages render it in Google Sans
            "axes.edgecolor": HAIR,
            "axes.labelcolor": BODY,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "xtick.color": BODY,
            "ytick.color": BODY,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": HAIR,
            "grid.linewidth": 0.6,
            "figure.facecolor": "none",
            "axes.facecolor": "none",
            "savefig.transparent": True,
        }
    )
    return family


def to_svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg")
    plt.close(fig)
    svg = buf.getvalue()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    return svg


def rect(w: float, h: float, left: float, right: float, bottom: float, top: float) -> list[float]:
    """Axes rectangle from margins in points, so text room scales with font size, not figure size."""
    W, H = w * 72, h * 72
    return [left / W, bottom / H, 1 - (left + right) / W, 1 - (bottom + top) / H]


def band(ax, a, b, **kw):
    ax.axvspan(a - pd.Timedelta(days=15), b + pd.Timedelta(days=15), color=SHOCK, alpha=0.28, lw=0, zorder=0, **kw)


# --------------------------------------------------------------------------- charts
def chart_shock(d: dict, w: float, h: float, fs: float):
    """All-food index with shock months shaded and the three peaks labelled."""
    food = d["ffpi"]["ffpi_food"]
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes(rect(w, h, 2.6 * fs, 5.6 * fs, 2.0 * fs, 0.2 * fs))
    for a, b in d["eps"]:
        band(ax, a, b)
    ax.plot(food.index, food.values, color=FOOD, lw=fs * 0.2, zorder=3, solid_capstyle="round")
    ax.set_ylim(0, 185)
    ax.set_yticks([0, 50, 100, 150])
    ax.tick_params(length=0, labelsize=fs * 0.85, pad=fs * 0.4)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(food.index[0], food.index[-1] + pd.DateOffset(months=14))
    ax.text(food.index[0], 183, "Index (2014–16 = 100)", fontsize=fs * 0.85, color=BODY, va="top")
    ax.axhline(100, color=RULE, lw=0.8, ls=(0, (3, 3)), zorder=1)

    for i, (t, v) in enumerate(d["peaks"]):
        ax.scatter([t], [v], s=(fs * 0.7) ** 2, color=FOOD, zorder=4, edgecolor="white", linewidth=fs * 0.1)
        sub = t.strftime("%b %Y") + (" · record" if i == len(d["peaks"]) - 1 else "")
        ax.annotate(f"{v:.1f}", (t, v), xytext=(-fs * 0.9, fs * 0.05), textcoords="offset points", ha="right",
                    va="bottom", fontsize=fs * 1.25, fontweight="bold", color=INK)
        ax.annotate(sub, (t, v), xytext=(-fs * 0.9, -fs * 0.1), textcoords="offset points", ha="right",
                    va="top", fontsize=fs * 0.85, color=BODY)
    lt, lv = d["latest"]
    ax.scatter([lt], [lv], s=(fs * 0.6) ** 2, color="white", edgecolor=FOOD, linewidth=fs * 0.12, zorder=4)
    ax.annotate(f"{lv:.1f}\n{lt.strftime('%b %Y')}", (lt, lv), xytext=(fs * 0.6, -fs * 0.6),
                textcoords="offset points", ha="left", va="top", fontsize=fs * 0.85, color=BODY)
    return fig


def chart_exposure(d: dict, w: float, h: float, fs: float, labels: list[str] | None = None):
    df, exposed, med = d["df"], d["exposed"], d["median_import"]
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes(rect(w, h, 4.4 * fs, 0.6 * fs, 3.6 * fs, 0.2 * fs))
    ax.fill_between([med, 46], SERIOUS_HUNGER, 47, color=EXPOSED_ZONE, lw=0, zorder=0)
    ax.axvline(med, color=RULE, lw=0.9, ls=(0, (3, 3)), zorder=1)
    ax.axhline(SERIOUS_HUNGER, color=RULE, lw=0.9, ls=(0, (3, 3)), zorder=1)
    rest = df[~df["exposed"]]
    ax.scatter(rest["food_import_pct"], rest["ghi_2025"], s=(fs * 0.62) ** 2, color=OTHER,
               edgecolor="white", linewidth=fs * 0.06, zorder=2)
    ax.scatter(exposed["food_import_pct"], exposed["ghi_2025"], s=(fs * 0.78) ** 2, color=EXPOSED,
               edgecolor="white", linewidth=fs * 0.08, zorder=3)
    short = {"Central African Republic": "Central African Rep.", "Congo (Republic of)": "Rep. of Congo",
             "Papua New Guinea": "Papua New Guinea"}
    nudge = {"Timor-Leste": (0.7, -0.9), "Afghanistan": (0.7, 0.5), "Haiti": (0.7, 0.6), "Niger": (0.7, -0.4),
             "Sierra Leone": (0.7, 0.2), "Madagascar": (0.7, 0.3), "Liberia": (0.7, 0.2),
             "Central African Republic": (0.7, -0.2), "Papua New Guinea": (-0.7, 0)}
    chosen = exposed.head(10) if labels is None else exposed[exposed["country_ghi"].isin(labels)]
    for _, r in chosen.iterrows():
        dx, dy = nudge.get(r["country_ghi"], (0.7, 0))
        ha = "right" if dx < 0 else "left"
        ax.annotate(short.get(r["country_ghi"], r["country_ghi"]), (r["food_import_pct"], r["ghi_2025"]),
                    xytext=(dx * fs, dy * fs), textcoords="offset points", fontsize=fs * 0.82, color=INK,
                    va="center", ha=ha)
    ax.text(25.2, SERIOUS_HUNGER - 0.6, "Serious hunger (GHI 20+)", color=BODY, fontsize=fs * 0.8, ha="left", va="top")
    ax.text(med + 0.4, 46.4, f"Above-median food imports ({med:.1f}%+)", color=BODY, fontsize=fs * 0.8,
            ha="left", va="top")
    ax.set_xlim(0, 46)
    ax.set_ylim(0, 47)
    ax.set_xlabel("Food imports, % of merchandise imports", fontsize=fs * 0.85, labelpad=fs * 0.4)
    ax.set_ylabel("Global Hunger Index 2025", fontsize=fs * 0.85, labelpad=fs * 0.4)
    ax.tick_params(length=0, labelsize=fs * 0.85)
    ax.grid(axis="x", color=HAIR, lw=0.6)
    return fig


def chart_warning(d: dict, w: float, h: float, fs: float):
    yoy = d["yoy"][SIGNAL_START:]
    fig = plt.figure(figsize=(w, h))
    strip = 2.6 * fs
    bottom = 2.0 * fs
    ax = fig.add_axes(rect(w, h, 4.0 * fs, 8.4 * fs, bottom + strip + 1.0 * fs, 0.2 * fs))
    axs = fig.add_axes(rect(w, h, 4.0 * fs, 8.4 * fs, bottom, h * 72 - bottom - strip), sharex=ax)
    for a, b in d["shock_eps"]:
        band(ax, a, b)
        band(axs, a, b)
    ax.axhline(0, color=RULE, lw=0.8)
    ax.axhline(SHOCK_THRESHOLD, color=INK, lw=0.9, ls=(0, (3, 3)), zorder=1)
    ax.plot(yoy.index, yoy["ffpi_cereals"], color=CEREALS, lw=fs * 0.13, zorder=2)
    ax.plot(yoy.index, yoy["ffpi_oils"], color=OILS, lw=fs * 0.13, zorder=3)
    ax.plot(yoy.index, yoy["ffpi_food"], color=FOOD, lw=fs * 0.2, zorder=4)
    ax.set_ylim(-60, 130)
    ax.set_yticks([-50, 0, 50, 100])
    ax.set_yticklabels(["−50%", "0", "+50%", "+100%"])
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", length=0, labelsize=fs * 0.85)
    ax.text(yoy.index[0], SHOCK_THRESHOLD + 3, "+20% line", color=INK, fontsize=fs * 0.8, va="bottom")
    ax.text(yoy.index[0], 127, "Change on a year earlier", color=BODY, fontsize=fs * 0.85, va="top")
    last = yoy.index[-1] + pd.DateOffset(months=4)
    ends = {"ffpi_food": ("All food", FOOD, 8), "ffpi_oils": ("Vegetable oils", OILS, 22),
            "ffpi_cereals": ("Cereals", CEREALS, -8)}
    for col, (label, color, y) in ends.items():
        ax.plot([yoy.index[-1], last - pd.DateOffset(months=1)], [yoy[col].iloc[-1], y], color=color, lw=0.8)
        ax.scatter([last], [y], s=(fs * 0.55) ** 2, color=color, marker="s", zorder=5)
        ax.text(last + pd.DateOffset(months=5), y, label, color=INK, fontsize=fs * 0.85, va="center",
                fontweight="bold" if col == "ffpi_food" else "normal")

    axs.set_ylim(0, 1)
    axs.set_yticks([])
    axs.grid(False)
    axs.spines["bottom"].set_visible(True)
    for r in d["signals"]:
        end = max(r["end"], r["start"] + pd.DateOffset(months=2))
        hit = r["lead"] is not None
        axs.axvspan(r["start"] - pd.Timedelta(days=15), end, ymin=0.52, ymax=0.98,
                    color=SIGNAL if hit else "white", ec=SIGNAL, lw=1.0)
        mid = r["start"] + (end - r["start"]) / 2
        x = mid if hit else r["start"] - pd.DateOffset(months=2)
        axs.text(x, 0.2 if hit else 0.75, f"{r['lead']} mo" if hit else "none", fontsize=fs * 0.8,
                 color=INK if hit else BODY, ha="center" if hit else "right", va="center")
    axs.text(yoy.index[0] - pd.DateOffset(months=5), 0.75, "Signal", fontsize=fs * 0.85, color=INK,
             fontweight="bold", ha="right", va="center")
    axs.text(yoy.index[0] - pd.DateOffset(months=5), 0.2, "Shock in", fontsize=fs * 0.8, color=BODY,
             ha="right", va="center")
    axs.tick_params(length=0, labelsize=fs * 0.85)
    axs.xaxis.set_major_locator(mdates.YearLocator(4))
    axs.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axs.set_xlim(yoy.index[0] - pd.DateOffset(months=3), yoy.index[-1] + pd.DateOffset(months=3))
    return fig


CHARTS = {"shock": chart_shock, "exposure": chart_exposure, "warning": chart_warning}


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    family = setup_fonts()
    d = compute()
    d["findings"]["font"] = family
    (OUT / "findings.json").write_text(json.dumps(d["findings"], indent=2, default=str))
    return d


if __name__ == "__main__":
    data = main()
    print(json.dumps(data["findings"], indent=2, default=str))
