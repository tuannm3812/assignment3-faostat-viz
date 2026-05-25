"""Analytical transformations used by the dashboard tabs."""

from __future__ import annotations

import pandas as pd

from app.config import EXPOSURE_WEIGHTS, SCENARIO_ASSUMPTIONS
from app.data import load_ghi_indicators


def minmax_scale(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(0.0, index=series.index)
    return (series - min_value) / (max_value - min_value)


def build_vulnerability(
    ghi: pd.DataFrame,
    worldbank: pd.DataFrame,
    hunger_weight: float = EXPOSURE_WEIGHTS["ghi"],
) -> pd.DataFrame:
    import_weight = 1 - hunger_weight
    ghi_slim = ghi[["iso3", "country_ghi", "ghi_2000", "ghi_2008", "ghi_2016", "ghi_2025"]].dropna(
        subset=["iso3", "ghi_2025"]
    )
    latest_imports = (
        worldbank.dropna(subset=["food_import_pct"])
        .sort_values("year", ascending=False)
        .groupby("iso3", as_index=False)
        .first()[["iso3", "country_wb", "year", "food_import_pct"]]
    )
    vuln = ghi_slim.merge(latest_imports, on="iso3", how="inner")
    vuln["ghi_norm"] = minmax_scale(vuln["ghi_2025"])
    vuln["import_dependency_norm"] = minmax_scale(vuln["food_import_pct"])
    vuln["exposure_index"] = (
        hunger_weight * vuln["ghi_norm"] + import_weight * vuln["import_dependency_norm"]
    ) * 100
    return vuln.sort_values("exposure_index", ascending=False)


def build_undernourishment_exposure(
    ghi: pd.DataFrame,
    worldbank: pd.DataFrame,
    hunger_weight: float = EXPOSURE_WEIGHTS["ghi"],
) -> pd.DataFrame:
    import_weight = 1 - hunger_weight
    indicators = load_ghi_indicators()
    if indicators.empty:
        return build_vulnerability(ghi, worldbank, hunger_weight)

    ghi_slim = ghi[["iso3", "country_ghi", "ghi_2000", "ghi_2008", "ghi_2016", "ghi_2025"]].dropna(
        subset=["iso3", "ghi_2025"]
    )
    latest_imports = (
        worldbank.dropna(subset=["food_import_pct"])
        .sort_values("year", ascending=False)
        .groupby("iso3", as_index=False)
        .first()[["iso3", "country_wb", "year", "food_import_pct"]]
    )
    exposure = ghi_slim.merge(indicators, on="country_ghi", how="left").merge(latest_imports, on="iso3", how="inner")
    hunger_source = "undernourishment_2024"
    if exposure[hunger_source].notna().sum() < 10:
        exposure[hunger_source] = exposure["ghi_2025"]
        hunger_source = "ghi_2025"

    exposure[hunger_source] = exposure[hunger_source].fillna(exposure[hunger_source].median())
    exposure["hunger_metric"] = exposure[hunger_source]
    exposure["hunger_metric_label"] = (
        "Undernourishment 2022-24 (% population)" if hunger_source == "undernourishment_2024" else "GHI score 2025"
    )
    exposure["hunger_norm"] = minmax_scale(exposure["hunger_metric"])
    exposure["import_dependency_norm"] = minmax_scale(exposure["food_import_pct"])
    exposure["exposure_index"] = (
        hunger_weight * exposure["hunger_norm"]
        + import_weight * exposure["import_dependency_norm"]
    ) * 100
    return exposure.sort_values("exposure_index", ascending=False)


def zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def build_corrected_vulnerability(
    ghi: pd.DataFrame,
    worldbank: pd.DataFrame,
    hunger_weight: float = EXPOSURE_WEIGHTS["ghi"],
) -> pd.DataFrame:
    import_weight = 1 - hunger_weight
    exposure = build_undernourishment_exposure(ghi, worldbank, hunger_weight).copy()
    hunger = exposure["undernourishment_2024"] if "undernourishment_2024" in exposure else exposure["hunger_metric"]
    exposure["undernourishment_2024"] = hunger.fillna(hunger.median())
    exposure["food_import_pct"] = exposure["food_import_pct"].fillna(exposure["food_import_pct"].median())
    exposure["z_undernourishment"] = zscore(exposure["undernourishment_2024"])
    exposure["z_food_import"] = zscore(exposure["food_import_pct"])
    exposure["vulnerability_score"] = (
        hunger_weight * exposure["z_undernourishment"]
        + import_weight * exposure["z_food_import"]
    )
    return exposure.sort_values("vulnerability_score", ascending=False)


def build_ffpi_correlation(master_idx: pd.DataFrame, ffpi_annual: pd.DataFrame) -> pd.DataFrame:
    price_idx = (
        master_idx.groupby(["iso3", "country", "year"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "avg_producer_price_index"})
    )
    ffpi_cols = ["ffpi_food", "ffpi_cereals", "ffpi_meat", "ffpi_oils", "ffpi_sugar", "ffpi_dairy"]
    merged = price_idx.merge(ffpi_annual[["year", *ffpi_cols]], on="year", how="inner")

    rows = []
    for country, group in merged.groupby("country"):
        for col in ffpi_cols:
            rows.append(
                {
                    "country": country,
                    "ffpi_index": col.replace("ffpi_", "").title(),
                    "correlation": group["avg_producer_price_index"].corr(group[col]),
                }
            )
    return pd.DataFrame(rows).dropna(subset=["correlation"])


def build_wheat_signal(master_usd: pd.DataFrame, ffpi_annual: pd.DataFrame) -> pd.DataFrame:
    wheat = master_usd[master_usd["item"].eq("Wheat")].copy()
    if wheat.empty:
        return pd.DataFrame()
    wheat = wheat.merge(ffpi_annual[["year", "ffpi_food"]], on="year", how="left", suffixes=("", "_annual"))
    if "ffpi_food_annual" in wheat.columns:
        wheat["ffpi_food"] = wheat["ffpi_food_annual"].fillna(wheat["ffpi_food"])
    return wheat.sort_values(["country", "year"])


def build_scenario(
    exposure: pd.DataFrame,
    shock_pct: int | float,
    pass_through_rate: int | float | None = None,
    basket_share: int | float | None = None,
    transmission_coeff: int | float | None = None,
) -> tuple[pd.DataFrame, float]:
    scenario = exposure.copy()
    if pass_through_rate is None:
        pass_through_rate = SCENARIO_ASSUMPTIONS["pass_through_rate"]
    if basket_share is None:
        basket_share = SCENARIO_ASSUMPTIONS["basket_share"]
    if transmission_coeff is None:
        transmission_coeff = SCENARIO_ASSUMPTIONS["transmission_coeff"]
    pass_through_rate = float(pass_through_rate)
    basket_share = float(basket_share)
    transmission_coeff = float(transmission_coeff)
    effective_global_pressure_pct = (
        shock_pct
        * basket_share
        * transmission_coeff
        * pass_through_rate
    )
    scenario["implied_import_cost_pressure_pct"] = (
        scenario["food_import_pct"] * effective_global_pressure_pct / 100
    )
    scenario["scenario_pressure_score"] = scenario["exposure_index"] * scenario["implied_import_cost_pressure_pct"] / 100
    return scenario.sort_values("implied_import_cost_pressure_pct", ascending=False), effective_global_pressure_pct


def assign_policy_action(row: pd.Series) -> str:
    hunger = row.get("ghi_2025", row.get("hunger_metric", 0))
    imports = row.get("food_import_pct", 0)
    if hunger >= 35 or row.get("exposure_index", 0) >= 70:
        return "Preparedness package"
    if imports >= 25:
        return "Import-buffer monitoring"
    return "Watchlist"


def priority_table(exposure: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    table = exposure.copy()
    if "exposure_index" not in table and "vulnerability_score" in table:
        table["exposure_index"] = minmax_scale(table["vulnerability_score"]) * 100
    table["policy_action"] = table.apply(assign_policy_action, axis=1)
    score_col = "scenario_pressure_score" if "scenario_pressure_score" in table else "exposure_index"
    return (
        table.nlargest(top_n, score_col)[
            ["country_ghi", "ghi_2025", "food_import_pct", "exposure_index", "policy_action"]
        ]
        .round({"ghi_2025": 1, "food_import_pct": 1, "exposure_index": 1})
        .rename(
            columns={
                "country_ghi": "Country",
                "ghi_2025": "GHI 2025",
                "food_import_pct": "Food imports %",
                "exposure_index": "Exposure index",
                "policy_action": "Suggested policy use",
            }
        )
    )


def build_weight_sensitivity(ghi: pd.DataFrame, worldbank: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    rows = []
    for hunger_weight in [0.4, 0.5, 0.6, 0.7, 0.8]:
        exposure = build_corrected_vulnerability(ghi, worldbank, hunger_weight).copy()
        exposure["rank"] = exposure["exposure_index"].rank(ascending=False, method="min")
        for _, row in exposure.nsmallest(top_n, "rank").iterrows():
            rows.append(
                {
                    "country": row["country_ghi"],
                    "food_access_weight": hunger_weight,
                    "import_weight": 1 - hunger_weight,
                    "rank": int(row["rank"]),
                    "exposure_index": row["exposure_index"],
                }
            )
    sensitivity = pd.DataFrame(rows)
    if sensitivity.empty:
        return sensitivity
    summary = (
        sensitivity.groupby("country", as_index=False)
        .agg(
            appearances=("food_access_weight", "count"),
            best_rank=("rank", "min"),
            average_rank=("rank", "mean"),
            average_exposure=("exposure_index", "mean"),
        )
        .sort_values(["appearances", "best_rank", "average_rank"], ascending=[False, True, True])
    )
    return summary
