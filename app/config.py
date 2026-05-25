"""Shared configuration and visual constants for the dashboard."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
LEGACY_RAW_DIR = ROOT_DIR / "data" / "raw"

DATA_FILES = {
    "master_usd": "master_producer_prices_usd.csv",
    "master_idx": "master_producer_price_index.csv",
    "ffpi_monthly": "ffpi_monthly.csv",
    "ffpi_annual": "ffpi_annual.csv",
    "ghi": "ghi_cleaned.csv",
    "worldbank": "worldbank_food_import_pct.csv",
}

CRISIS_PERIODS = [
    (2007, 2009, "2007-09 food crisis"),
    (2010, 2012, "2010-11 Arab Spring"),
    (2021, 2023, "2022 Ukraine war"),
]

COLORS = {
    "AUS": "#14b8a6",
    "NZL": "#3b82f6",
    "FFPI": "#d97706",
    "risk": "#e11d48",
    "crisis": "#f59e0b",
    "neutral": "#64748b",
    "low": "#dbeafe",
    "mid": "#f59e0b",
    "high": "#be123c",
    "highlight": "#fff7ed",
}

CHART_TEMPLATE = "plotly_white"
COUNTRY_COLORS = {
    "AUS": COLORS["AUS"],
    "NZL": COLORS["NZL"],
    "Australia": COLORS["AUS"],
    "New Zealand": COLORS["NZL"],
}
FFPI_COLORS = {
    "ffpi_food": "#d97706",
    "ffpi_cereals": "#e11d48",
    "ffpi_meat": "#14b8a6",
    "ffpi_dairy": "#3b82f6",
    "ffpi_oils": "#8b5cf6",
    "ffpi_sugar": "#f59e0b",
}
RISK_SCALE = [
    [0.00, "#dbeafe"],
    [0.35, "#14b8a6"],
    [0.60, "#f59e0b"],
    [0.82, "#fb7185"],
    [1.00, "#be123c"],
]

EXPOSURE_WEIGHTS = {
    "ghi": 0.6,
    "import_dependency": 0.4,
}
SCENARIO_ASSUMPTIONS = {
    "basket_share": 0.45,
    "transmission_coeff": 0.429,
    "pass_through_rate": 0.50,
}
