"""Streamlit dashboard for FAOSTAT food price shock analysis."""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from openpyxl import load_workbook
from plotly.subplots import make_subplots


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
    "AUS": "#8c2981",
    "NZL": "#de4968",
    "FFPI": "#3b0f70",
    "risk": "#f66e5b",
    "crisis": "#de4968",
    "neutral": "#6b7280",
    "low": "#221150",
    "mid": "#b73779",
    "high": "#fe9f6d",
    "highlight": "#fcfdbf",
}

CHART_TEMPLATE = "plotly_white"
COUNTRY_COLORS = {
    "AUS": COLORS["AUS"],
    "NZL": COLORS["NZL"],
    "Australia": COLORS["AUS"],
    "New Zealand": COLORS["NZL"],
}
FFPI_COLORS = {
    "ffpi_food": "#3b0f70",
    "ffpi_cereals": "#8c2981",
    "ffpi_meat": "#de4968",
    "ffpi_dairy": "#f66e5b",
    "ffpi_oils": "#fe9f6d",
    "ffpi_sugar": "#fcfdbf",
}
RISK_SCALE = [
    [0.00, "#000004"],
    [0.25, "#3b0f70"],
    [0.50, "#8c2981"],
    [0.75, "#de4968"],
    [1.00, "#fcfdbf"],
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


def apply_chart_style(fig: go.Figure, height: int | None = None, show_legend: bool | None = None) -> go.Figure:
    layout = {
        "template": CHART_TEMPLATE,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 30, "r": 30, "t": 70, "b": 40},
        "legend_title_text": "",
    }
    if height is not None:
        layout["height"] = height
    if show_legend is not None:
        layout["showlegend"] = show_legend
    fig.update_layout(**layout)
    fig.update_xaxes(gridcolor="rgba(127,127,127,0.22)", zerolinecolor="rgba(127,127,127,0.25)")
    fig.update_yaxes(gridcolor="rgba(127,127,127,0.22)", zerolinecolor="rgba(127,127,127,0.25)")
    return fig


def story_insight(step: str, insight: str, action: str | None = None) -> None:
    text = f"**{step}.** {insight}"
    if action:
        text += f"\n\n**So what:** {action}"
    st.info(text)


def data_path(filename: str) -> Path:
    """Prefer cleaned data, but support the earlier raw-folder layout."""
    for folder in (PROCESSED_DIR, LEGACY_RAW_DIR):
        candidate = folder / filename
        if candidate.exists():
            return candidate
    return PROCESSED_DIR / filename


@st.cache_data(show_spinner=False)
def load_csv(filename: str, parse_dates: tuple[str, ...] = ()) -> pd.DataFrame:
    path = data_path(filename)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=list(parse_dates))


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def coerce_boolean(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)
    return df


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    data = {
        "master_usd": load_csv(DATA_FILES["master_usd"]),
        "master_idx": load_csv(DATA_FILES["master_idx"]),
        "ffpi_monthly": load_csv(DATA_FILES["ffpi_monthly"], ("date",)),
        "ffpi_annual": load_csv(DATA_FILES["ffpi_annual"]),
        "ghi": load_csv(DATA_FILES["ghi"]),
        "worldbank": load_csv(DATA_FILES["worldbank"]),
    }

    numeric_columns = [
        "year",
        "value",
        "ffpi_food",
        "ffpi_meat",
        "ffpi_dairy",
        "ffpi_cereals",
        "ffpi_oils",
        "ffpi_sugar",
        "food_import_pct",
        "ghi_2000",
        "ghi_2008",
        "ghi_2016",
        "ghi_2025",
    ]
    for key, df in data.items():
        df = coerce_numeric(df, numeric_columns)
        data[key] = coerce_boolean(df, ["is_imputed", "is_outlier"])
    return data


def require_data(data: dict[str, pd.DataFrame]) -> bool:
    missing = [name for name, df in data.items() if df.empty]
    if missing:
        st.error(
            "Missing local data files: "
            + ", ".join(DATA_FILES[name] for name in missing)
            + f". Expected them under {PROCESSED_DIR}."
        )
        return False
    return True


def add_crisis_bands(fig: go.Figure, yref: str = "paper") -> None:
    for start, end, label in CRISIS_PERIODS:
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=COLORS["crisis"],
            opacity=0.08,
            line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation_font_size=10,
            yref=yref,
        )


def minmax_scale(series: pd.Series) -> pd.Series:
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(0.0, index=series.index)
    return (series - min_value) / (max_value - min_value)


def safe_float(value: object) -> float | None:
    if isinstance(value, str):
        value = value.replace("<", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@st.cache_data(show_spinner=False)
def load_ghi_indicators() -> pd.DataFrame:
    path = data_path("global_hunger_index.xlsx")
    if not path.exists():
        return pd.DataFrame()

    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook["GHI Indicator Values 2025"]
    rows = []
    for row in sheet.iter_rows(min_row=4, values_only=True):
        country = row[0]
        if country is None or len(str(country)) > 60:
            continue
        rows.append(
            {
                "country_ghi": country,
                "undernourishment_2024": safe_float(row[4]),
                "child_wasting_2024": safe_float(row[11]),
                "child_stunting_2024": safe_float(row[16]),
                "child_mortality_2023": safe_float(row[20]),
            }
        )
    return pd.DataFrame(rows)


def build_vulnerability(ghi: pd.DataFrame, worldbank: pd.DataFrame) -> pd.DataFrame:
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
        EXPOSURE_WEIGHTS["ghi"] * vuln["ghi_norm"] + EXPOSURE_WEIGHTS["import_dependency"] * vuln["import_dependency_norm"]
    ) * 100
    return vuln.sort_values("exposure_index", ascending=False)


def build_undernourishment_exposure(ghi: pd.DataFrame, worldbank: pd.DataFrame) -> pd.DataFrame:
    indicators = load_ghi_indicators()
    if indicators.empty:
        return build_vulnerability(ghi, worldbank)

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
        EXPOSURE_WEIGHTS["ghi"] * exposure["hunger_norm"]
        + EXPOSURE_WEIGHTS["import_dependency"] * exposure["import_dependency_norm"]
    ) * 100
    return exposure.sort_values("exposure_index", ascending=False)


def zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def build_corrected_vulnerability(ghi: pd.DataFrame, worldbank: pd.DataFrame) -> pd.DataFrame:
    exposure = build_undernourishment_exposure(ghi, worldbank).copy()
    hunger = exposure["undernourishment_2024"] if "undernourishment_2024" in exposure else exposure["hunger_metric"]
    exposure["undernourishment_2024"] = hunger.fillna(hunger.median())
    exposure["food_import_pct"] = exposure["food_import_pct"].fillna(exposure["food_import_pct"].median())
    exposure["z_undernourishment"] = zscore(exposure["undernourishment_2024"])
    exposure["z_food_import"] = zscore(exposure["food_import_pct"])
    exposure["vulnerability_score_v2"] = (
        EXPOSURE_WEIGHTS["ghi"] * exposure["z_undernourishment"]
        + EXPOSURE_WEIGHTS["import_dependency"] * exposure["z_food_import"]
    )
    exposure["vulnerability_display_score"] = minmax_scale(exposure["vulnerability_score_v2"]) * 100
    return exposure.sort_values("vulnerability_score_v2", ascending=False)


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


def build_scenario(exposure: pd.DataFrame, shock_pct: int | float) -> tuple[pd.DataFrame, float]:
    scenario = exposure.copy()
    effective_global_pressure_pct = (
        shock_pct
        * SCENARIO_ASSUMPTIONS["basket_share"]
        * SCENARIO_ASSUMPTIONS["transmission_coeff"]
        * SCENARIO_ASSUMPTIONS["pass_through_rate"]
    )
    scenario["implied_import_cost_pressure_pct"] = (
        scenario["food_import_pct"] * effective_global_pressure_pct / 100
    )
    scenario["scenario_pressure_score"] = (
        scenario["vulnerability_display_score"] * scenario["implied_import_cost_pressure_pct"] / 100
        if "vulnerability_display_score" in scenario
        else scenario["exposure_index"] * scenario["implied_import_cost_pressure_pct"] / 100
    )
    return scenario.sort_values("implied_import_cost_pressure_pct", ascending=False), effective_global_pressure_pct


def slide_context(data: dict[str, pd.DataFrame]) -> None:
    ffpi = data["ffpi_annual"]
    ffpi_m = data["ffpi_monthly"]

    st.title("Why Food Price Shocks Matter")
    st.caption("Global food-price pressure has surged repeatedly; the question is who has the least capacity to absorb it.")
    story_insight(
        "Food price shocks are global, but vulnerability is not evenly shared",
        "The FFPI shows repeated global stress events across the last three decades.",
        "Use this tab to establish the problem before narrowing to Australia and New Zealand.",
    )

    st.subheader("Global Food Price Shock Timeline")
    fig = px.line(
        ffpi[ffpi["year"] >= 1991],
        x="year",
        y=["ffpi_food", "ffpi_cereals", "ffpi_meat", "ffpi_sugar"],
        color_discrete_map=FFPI_COLORS,
        labels={"value": "Index (2014-2016 = 100)", "variable": "Index"},
        title="When the World's Food Got Expensive",
        template=CHART_TEMPLATE,
    )
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    add_crisis_bands(fig)
    apply_chart_style(fig, height=560)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Supporting Evidence")
    c1, c2, c3 = st.columns(3)
    crisis_years = [2008, 2011, 2022]
    crisis = ffpi[ffpi["year"].isin(crisis_years)].set_index("year")
    for col, year in zip([c1, c2, c3], crisis_years):
        if year in crisis.index:
            col.metric(f"{year} FFPI food", f"{crisis.loc[year, 'ffpi_food']:.1f}")

    monthly = ffpi_m[ffpi_m["year"] >= 2000].copy()
    fig_monthly = px.area(
        monthly,
        x="date",
        y="ffpi_food",
        labels={"date": "Date", "ffpi_food": "FFPI food"},
        title="Monthly Food Price Shock Timeline",
        template=CHART_TEMPLATE,
    )
    fig_monthly.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    fig_monthly.update_traces(line_color=COLORS["FFPI"], fillcolor="rgba(222, 73, 104, 0.16)")
    apply_chart_style(fig_monthly, height=390)
    st.plotly_chart(fig_monthly, width="stretch")


def slide_producer_signal(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    master_idx = data["master_idx"]
    ffpi = data["ffpi_annual"]
    wheat = build_wheat_signal(master, ffpi)

    st.title("Australia and New Zealand Producer Price Signal")
    st.caption("Wheat is used as the indicator commodity because it is globally recognisable and visibly moves through food-price shock periods.")
    story_insight(
        "Wheat makes the global shock visible",
        "Wheat is a globally important staple and a clear way to connect AUS/NZ producer prices to the FFPI story.",
        "Use this tab to show why the project uses producer prices as a supply-side signal.",
    )

    st.subheader("Wheat Producer Prices vs Global FFPI")
    if wheat.empty:
        st.warning("Wheat is not available in the current producer-price file.")
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for country, color in [("Australia", COLORS["AUS"]), ("New Zealand", COLORS["NZL"])]:
            country_df = wheat[wheat["country"] == country]
            if country_df.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=country_df["year"],
                    y=country_df["value"],
                    mode="lines+markers",
                    name=f"{country} wheat",
                    line={"color": color, "width": 3},
                    hovertemplate="<b>%{fullData.name}</b><br>Year %{x}<br>USD/tonne: $%{y:,.0f}<extra></extra>",
                ),
                secondary_y=False,
            )
        ffpi_plot = ffpi[["year", "ffpi_food"]].dropna()
        fig.add_trace(
            go.Scatter(
                x=ffpi_plot["year"],
                y=ffpi_plot["ffpi_food"],
                mode="lines",
                name="Global FFPI",
                line={"color": COLORS["FFPI"], "width": 2, "dash": "dot"},
            ),
            secondary_y=True,
        )
        add_crisis_bands(fig)
        apply_chart_style(fig, height=560)
        fig.update_layout(title="AUS/NZ Wheat Producer Prices vs Global Food Price Index")
        fig.update_yaxes(title_text="Wheat producer price (USD/tonne)", secondary_y=False)
        fig.update_yaxes(title_text="FFPI food index", secondary_y=True)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Supporting Evidence")
    corr = build_ffpi_correlation(master_idx, ffpi)
    fig_corr = px.bar(
        corr.sort_values(["country", "correlation"]),
        x="correlation",
        y="ffpi_index",
        color="country",
        barmode="group",
        orientation="h",
        color_discrete_map=COUNTRY_COLORS,
        labels={"correlation": "Pearson correlation", "ffpi_index": "FFPI sub-index"},
        title="AUS/NZ Producer Price Index Alignment with FFPI",
        template=CHART_TEMPLATE,
    )
    fig_corr.add_vline(x=0, line_color=COLORS["neutral"])
    apply_chart_style(fig_corr, height=390)
    st.plotly_chart(fig_corr, width="stretch")

    items = [item for item in ["Barley", "Maize (corn)", "Rice", "Soya beans", "Raw milk of cattle"] if item in master["item"].values]
    if items:
        selected_item = st.selectbox("Commodity check", items)
        filtered = master[master["item"].eq(selected_item)].sort_values("year")
        fig_item = px.line(
            filtered,
            x="year",
            y="value",
            color="country",
            markers=True,
            color_discrete_map=COUNTRY_COLORS,
            labels={"value": "USD/tonne", "country": ""},
            title=f"{selected_item} Producer Prices",
            template=CHART_TEMPLATE,
        )
        add_crisis_bands(fig_item)
        apply_chart_style(fig_item, height=390)
        st.plotly_chart(fig_item, width="stretch")


def slide_vulnerability(data: dict[str, pd.DataFrame]) -> None:
    exposure = build_corrected_vulnerability(data["ghi"], data["worldbank"])
    ghi = data["ghi"]
    worldbank = data["worldbank"]

    st.title("Who Is Most Vulnerable?")
    st.caption("The corrected vulnerability score combines undernourishment and food-import dependency using a transparent z-score weighted method.")
    story_insight(
        "Hunger severity needs an exposure channel",
        "Countries become priority cases when food-access stress and import dependency combine.",
        "Use this tab to explain why raw multiplication was replaced by a normalized weighted exposure score.",
    )

    st.subheader("Corrected Vulnerability Matrix")
    x_label = exposure["hunger_metric_label"].iloc[0] if "hunger_metric_label" in exposure else "GHI score 2025"
    fig = px.scatter(
        exposure,
        x="hunger_metric" if "hunger_metric" in exposure else "ghi_2025",
        y="food_import_pct",
        color="vulnerability_display_score",
        size="vulnerability_display_score",
        size_max=28,
        hover_name="country_ghi",
        hover_data={
            "food_import_pct": ":.1f",
            "vulnerability_score_v2": ":.2f",
            "vulnerability_display_score": ":.1f",
            "ghi_2025": ":.1f",
        },
        color_continuous_scale=RISK_SCALE,
        labels={
            "hunger_metric": x_label,
            "food_import_pct": "Food imports (% of merchandise imports)",
            "vulnerability_display_score": "Vulnerability score",
            "vulnerability_score_v2": "Z-score vulnerability",
        },
        title="Hunger/Food-Access Stress x Food Import Dependency",
        template=CHART_TEMPLATE,
    )
    for _, row in exposure.nlargest(8, "vulnerability_score_v2").iterrows():
        fig.add_annotation(
            x=row["hunger_metric"] if "hunger_metric" in row else row["ghi_2025"],
            y=row["food_import_pct"],
            text=row["country_ghi"],
            showarrow=False,
            xshift=8,
            yshift=4,
            font={"size": 10},
        )
    fig.add_vline(x=exposure["hunger_metric"].median(), line_dash="dash", line_color=COLORS["neutral"])
    fig.add_hline(y=exposure["food_import_pct"].median(), line_dash="dash", line_color=COLORS["neutral"])
    apply_chart_style(fig, height=610)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Supporting Evidence")
    col1, col2 = st.columns(2)
    with col1:
        ghi_valid = ghi.dropna(subset=["iso3", "ghi_2025"])
        fig_map = px.choropleth(
            ghi_valid,
            locations="iso3",
            color="ghi_2025",
            hover_name="country_ghi",
            color_continuous_scale=RISK_SCALE,
            labels={"ghi_2025": "GHI 2025"},
            title="Global Hunger Index 2025",
            template=CHART_TEMPLATE,
        )
        apply_chart_style(fig_map, height=420)
        fig_map.update_layout(geo_showframe=False, geo_showcoastlines=True, geo_coastlinecolor=COLORS["neutral"])
        st.plotly_chart(fig_map, width="stretch")
    with col2:
        latest_imports = (
            worldbank.dropna(subset=["food_import_pct"])
            .sort_values("year", ascending=False)
            .groupby("iso3", as_index=False)
            .first()
        )
        fig_hist = px.histogram(
            latest_imports,
            x="food_import_pct",
            nbins=35,
            color_discrete_sequence=[COLORS["AUS"]],
            labels={"food_import_pct": "Food imports (% of merchandise imports)"},
            title="Distribution of Food Import Dependency",
            template=CHART_TEMPLATE,
        )
        fig_hist.add_vline(x=latest_imports["food_import_pct"].median(), line_dash="dash", line_color=COLORS["neutral"])
        apply_chart_style(fig_hist, height=420, show_legend=False)
        st.plotly_chart(fig_hist, width="stretch")


def slide_what_if(data: dict[str, pd.DataFrame]) -> None:
    exposure = build_corrected_vulnerability(data["ghi"], data["worldbank"])

    st.title("What-If Scenario and Priority Ranking")
    st.caption(
        "Estimate how an AUS/NZ producer-price shock could translate into import-cost pressure for structurally exposed countries."
    )
    story_insight(
        "The scenario converts insight into action",
        "The ranking shows where early-warning monitoring should focus under an illustrative AUS/NZ producer-price shock.",
        "Use this as an action layer, not an exact import-bill forecast.",
    )

    shock_pct = st.slider("Producer price shock", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
    scenario, effective_global_pressure_pct = build_scenario(exposure, shock_pct)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Producer shock", f"+{shock_pct}%")
    c2.metric("Basket share", f"{SCENARIO_ASSUMPTIONS['basket_share']:.0%}")
    c3.metric("Transmission x pass-through", f"{SCENARIO_ASSUMPTIONS['transmission_coeff']:.3f} x {SCENARIO_ASSUMPTIONS['pass_through_rate']:.0%}")
    c4.metric("Effective global pressure", f"{effective_global_pressure_pct:.2f}%")

    st.subheader("Scenario Priority Ranking")
    top = scenario.nlargest(12, "implied_import_cost_pressure_pct")
    max_scenario, _ = build_scenario(exposure, 60)
    max_import_pressure = max(max_scenario["implied_import_cost_pressure_pct"].max(), 0.01)
    max_pressure_score = max(max_scenario["scenario_pressure_score"].max(), 0.01)
    fig = px.bar(
        top,
        x="implied_import_cost_pressure_pct",
        y="country_ghi",
        orientation="h",
        color="implied_import_cost_pressure_pct",
        color_continuous_scale=RISK_SCALE,
        range_color=[0, max_import_pressure],
        hover_data={
            "hunger_metric": ":.1f",
            "food_import_pct": ":.1f",
            "vulnerability_score_v2": ":.2f",
            "implied_import_cost_pressure_pct": ":.2f",
        },
        labels={"country_ghi": "", "implied_import_cost_pressure_pct": "Implied import-cost pressure (%)"},
        title=f"Priority Countries under +{shock_pct}% Producer Shock",
        template=CHART_TEMPLATE,
    )
    apply_chart_style(fig, height=560)
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(range=[0, max_import_pressure * 1.08])
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, width="stretch")

    st.subheader("Method and Sensitivity")
    fig_scatter = px.scatter(
        scenario,
        x="vulnerability_display_score",
        y="implied_import_cost_pressure_pct",
        color="scenario_pressure_score",
        size="scenario_pressure_score",
        size_max=24,
        hover_name="country_ghi",
        color_continuous_scale=RISK_SCALE,
        range_color=[0, max_pressure_score],
        labels={
            "vulnerability_display_score": "Vulnerability score",
            "implied_import_cost_pressure_pct": "Implied import-cost pressure (%)",
            "scenario_pressure_score": "Scenario pressure score",
        },
        title="Vulnerability x Implied Import-Cost Pressure",
        template=CHART_TEMPLATE,
    )
    apply_chart_style(fig_scatter, height=420)
    fig_scatter.update_xaxes(range=[0, 105])
    fig_scatter.update_yaxes(range=[0, max_import_pressure * 1.08])
    st.plotly_chart(fig_scatter, width="stretch")

    with st.expander("Scenario assumptions and honest boundaries", expanded=True):
        st.markdown(
            f"""
            **Formula**

            `effective_global_pressure = producer_shock x basket_share x transmission_coeff x pass_through_rate`

            **Current assumptions**

            - Basket share: `{SCENARIO_ASSUMPTIONS['basket_share']:.2f}`
            - Transmission coefficient: `{SCENARIO_ASSUMPTIONS['transmission_coeff']:.3f}`
            - Pass-through rate: `{SCENARIO_ASSUMPTIONS['pass_through_rate']:.2f}`

            This remains an illustrative prioritisation model. It does not include bilateral trade flows,
            exchange rates, freight costs, tariffs, subsidies, trade margins, or supplier substitution.
            """
        )


def appendix(data: dict[str, pd.DataFrame]) -> None:
    st.title("Appendix")
    st.caption("Reference views for Q&A, data inspection, and technical validation.")

    st.subheader("Dataset Explorer")
    label_to_key = {
        "Producer prices, USD": "master_usd",
        "Producer price index": "master_idx",
        "FFPI annual": "ffpi_annual",
        "FFPI monthly": "ffpi_monthly",
        "Global Hunger Index": "ghi",
        "World Bank food imports": "worldbank",
    }
    label = st.selectbox("Dataset", list(label_to_key))
    df = data[label_to_key[label]]
    st.caption(f"{len(df):,} rows x {df.shape[1]:,} columns")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Commodity Volatility")
    country = st.radio("Country", ["Australia", "New Zealand"], horizontal=True)
    subset = data["master_usd"][data["master_usd"]["country"] == country]
    vol = subset.groupby("item")["value"].agg(["mean", "std", "count"]).reset_index()
    vol = vol[vol["count"] >= 5]
    vol["cv_pct"] = vol["std"] / vol["mean"] * 100
    vol = vol.sort_values("cv_pct", ascending=False).head(15)
    fig_vol = px.bar(
        vol.sort_values("cv_pct"),
        x="cv_pct",
        y="item",
        orientation="h",
        color="cv_pct",
        color_continuous_scale=RISK_SCALE,
        labels={"cv_pct": "Coefficient of variation (%)", "item": ""},
        title=f"{country}: Most Volatile Producer Prices",
        template=CHART_TEMPLATE,
    )
    fig_vol.add_vline(x=50, line_dash="dash", line_color=COLORS["risk"], annotation_text="50% CV")
    apply_chart_style(fig_vol, height=520)
    fig_vol.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_vol, width="stretch")


def pitch_brief(data: dict[str, pd.DataFrame]) -> None:
    st.title("Part 2 Pitch Brief")
    st.caption("A presentation-ready path through the dashboard: what changed, who is exposed, and what to do next.")

    ffpi = data["ffpi_annual"]
    wheat = build_wheat_signal(data["master_usd"], ffpi)
    exposure = build_undernourishment_exposure(data["ghi"], data["worldbank"])

    st.subheader("1. The Shock Context: Three Global Price Surges")
    st.write(
        "This visual supports the opening claim: food price shocks are global, but their consequences are uneven."
    )
    fig_ffpi = px.line(
        ffpi[ffpi["year"] >= 1991],
        x="year",
        y=["ffpi_food", "ffpi_cereals", "ffpi_oils", "ffpi_sugar"],
        color_discrete_map=FFPI_COLORS,
        labels={"value": "Index (2014-2016 = 100)", "variable": "Index"},
        title="FAO Food Price Index: shock periods since 1991",
        template=CHART_TEMPLATE,
    )
    fig_ffpi.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    add_crisis_bands(fig_ffpi)
    apply_chart_style(fig_ffpi, height=430)
    st.plotly_chart(fig_ffpi, width="stretch")

    st.subheader("2. The Local Signal: Wheat Connects AUS/NZ to the Global Story")
    st.write(
        "We added this as a pitch visual because wheat is easy to understand, globally important, and visible in the crisis periods."
    )
    if not wheat.empty:
        fig_wheat = make_subplots(specs=[[{"secondary_y": True}]])
        for country, color in [("Australia", COLORS["AUS"]), ("New Zealand", COLORS["NZL"])]:
            country_df = wheat[wheat["country"] == country]
            if country_df.empty:
                continue
            fig_wheat.add_trace(
                go.Scatter(
                    x=country_df["year"],
                    y=country_df["value"],
                    mode="lines+markers",
                    name=f"{country} wheat",
                    line={"color": color, "width": 3},
                    hovertemplate="<b>%{fullData.name}</b><br>Year %{x}<br>USD/tonne: $%{y:,.0f}<extra></extra>",
                ),
                secondary_y=False,
            )
        ffpi_plot = ffpi[["year", "ffpi_food"]].dropna()
        fig_wheat.add_trace(
            go.Scatter(
                x=ffpi_plot["year"],
                y=ffpi_plot["ffpi_food"],
                mode="lines",
                name="Global FFPI",
                line={"color": COLORS["FFPI"], "width": 2, "dash": "dot"},
            ),
            secondary_y=True,
        )
        add_crisis_bands(fig_wheat)
        apply_chart_style(fig_wheat, height=470)
        fig_wheat.update_layout(title="Wheat Producer Prices vs Global Food Price Index")
        fig_wheat.update_yaxes(title_text="Wheat producer price (USD/tonne)", secondary_y=False)
        fig_wheat.update_yaxes(title_text="FFPI food index", secondary_y=True)
        st.plotly_chart(fig_wheat, width="stretch")
    else:
        st.info("Wheat is not available in the current producer-price file.")

    st.subheader("3. The Human Lens: Hunger-Import Exposure")
    st.write(
        "This improves the deck's vulnerability argument by using undernourishment where available, not just the broad GHI score."
    )
    x_label = exposure["hunger_metric_label"].iloc[0] if "hunger_metric_label" in exposure else "GHI score 2025"
    fig_exposure = px.scatter(
        exposure,
        x="hunger_metric" if "hunger_metric" in exposure else "ghi_2025",
        y="food_import_pct",
        color="exposure_index",
        size="exposure_index",
        size_max=24,
        hover_name="country_ghi",
        hover_data={"food_import_pct": ":.1f", "exposure_index": ":.1f", "ghi_2025": ":.1f"},
        color_continuous_scale=RISK_SCALE,
        labels={
            "hunger_metric": x_label,
            "food_import_pct": "Food imports (% of merchandise imports)",
            "exposure_index": "Exposure index",
        },
        title="Countries Facing Both Food-Access Stress and Import Exposure",
        template=CHART_TEMPLATE,
    )
    top_labels = exposure.nlargest(8, "exposure_index")
    for _, row in top_labels.iterrows():
        fig_exposure.add_annotation(
            x=row["hunger_metric"] if "hunger_metric" in row else row["ghi_2025"],
            y=row["food_import_pct"],
            text=row["country_ghi"],
            showarrow=False,
            xshift=8,
            yshift=4,
            font={"size": 10},
        )
    apply_chart_style(fig_exposure, height=560)
    st.plotly_chart(fig_exposure, width="stretch")

    st.subheader("4. The Action: Scenario Priority List")
    shock_pct = st.slider("Presentation shock scenario", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
    pass_through_pct = st.slider("Presentation pass-through assumption", 0, 100, 25, step=5, format="%d%%")
    scenario = exposure.copy()
    global_pressure = shock_pct * pass_through_pct / 100
    scenario["implied_import_cost_pressure_pct"] = scenario["food_import_pct"] * global_pressure / 100
    scenario["scenario_pressure_score"] = scenario["exposure_index"] * scenario["implied_import_cost_pressure_pct"] / 100
    top = scenario.nlargest(12, "scenario_pressure_score").sort_values("scenario_pressure_score")
    fig_priority = px.bar(
        top,
        x="scenario_pressure_score",
        y="country_ghi",
        orientation="h",
        color="scenario_pressure_score",
        color_continuous_scale=RISK_SCALE,
        labels={"country_ghi": "", "scenario_pressure_score": "Scenario pressure score"},
        title=f"Priority Countries under +{shock_pct}% Producer Shock x {pass_through_pct}% Pass-through",
        template=CHART_TEMPLATE,
    )
    apply_chart_style(fig_priority, height=470)
    fig_priority.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_priority, width="stretch")

    with st.expander("Why these visuals were added for Part 2"):
        st.markdown(
            """
            - **FFPI shock context** gives the audience the global problem in one screen.
            - **Wheat signal** turns AUS/NZ producer prices into a memorable indicator commodity.
            - **Undernourishment exposure** makes the human-centred design stronger than a generic risk score.
            - **Scenario priority list** converts the analysis into an action: who should be monitored first.
            """
        )


def overview(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]
    vuln = build_vulnerability(data["ghi"], data["worldbank"])

    st.title("FAOSTAT Producer Prices: Shock Exposure Dashboard")
    st.caption("Australia and New Zealand producer prices, global food price shocks, and hunger-import exposure.")
    st.write(
        "Follow the story from supply-side producer prices, to global food price context, "
        "to countries least able to absorb price pressure."
    )
    story_insight(
        "Start with the map of evidence",
        "The dashboard joins producer prices, FFPI, hunger, and food-import dependency so the audience can move from prices to people.",
        "Use this page to establish scope before diving into the causal caveats.",
    )

    year_min = int(master["year"].min())
    year_max = int(master["year"].max())
    latest_ffpi = ffpi.dropna(subset=["ffpi_food"]).sort_values("year").iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coverage", f"{year_min}-{year_max}")
    c2.metric("Commodities", f"{master['item'].nunique():,}")
    c3.metric("Producer price rows", f"{len(master):,}")
    c4.metric(f"Latest FFPI food ({int(latest_ffpi['year'])})", f"{latest_ffpi['ffpi_food']:.1f}")

    country_summary = (
        master.groupby(["iso3", "country"], as_index=False)
        .agg(avg_usd_per_tonne=("value", "mean"), commodities=("item", "nunique"), outliers=("is_outlier", "sum"))
        .sort_values("iso3")
    )
    country_summary["outlier_pct"] = country_summary["outliers"] / country_summary["commodities"].clip(lower=1) * 100
    country_summary["avg_usd_per_tonne"] = country_summary["avg_usd_per_tonne"].round(0)

    left, right = st.columns([0.42, 0.58])
    with left:
        st.subheader("Country Coverage Snapshot")
        st.dataframe(
            country_summary[
                ["country", "commodities", "avg_usd_per_tonne", "outliers"]
            ].rename(
                columns={
                    "country": "Country",
                    "commodities": "Commodities",
                    "avg_usd_per_tonne": "Avg USD/tonne",
                    "outliers": "Flagged outliers",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Compact overview only. The detailed price story starts in `Price Trends` and `Volatility`.")

    with right:
        st.subheader("Highest Hunger-Import Exposure")
        st.dataframe(
            vuln.head(8)[["country_ghi", "ghi_2025", "food_import_pct", "exposure_index"]]
            .round(2)
            .rename(
                columns={
                    "country_ghi": "Country",
                    "ghi_2025": "GHI 2025",
                    "food_import_pct": "Food imports %",
                    "exposure_index": "Exposure index",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    st.caption(
        "This summary establishes dataset scope and priority exposure signals before the detailed analytical views."
    )


def price_trends(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]

    st.title("Producer Price Trends")
    st.caption("Start with the supply-side signal: how AUS/NZ commodity prices move through time.")
    story_insight(
        "What is changing?",
        "Producer prices show the supply-side signal, while the FFPI overlay shows whether the selected commodity moves with global food-price pressure.",
        "Start with Wheat for the clearest presentation example, then test other commodities interactively.",
    )
    items = sorted(master["item"].dropna().unique())
    default_item = "Wheat" if "Wheat" in items else items[0]
    selected_item = st.selectbox("Commodity", items, index=items.index(default_item))

    countries = st.multiselect(
        "Country",
        options=["Australia", "New Zealand"],
        default=["Australia", "New Zealand"],
    )

    filtered = master[(master["item"] == selected_item) & (master["country"].isin(countries))].sort_values("year")
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for country, color in [("Australia", COLORS["AUS"]), ("New Zealand", COLORS["NZL"])]:
        country_df = filtered[filtered["country"] == country]
        if country_df.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=country_df["year"],
                y=country_df["value"],
                mode="lines+markers",
                name=country,
                line={"color": color, "width": 3},
                customdata=country_df[["flag", "is_imputed", "is_outlier"]],
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>Year %{x}<br>"
                    "USD/tonne: $%{y:,.0f}<br>Flag: %{customdata[0]}<br>"
                    "Imputed: %{customdata[1]}<br>Outlier: %{customdata[2]}<extra></extra>"
                ),
            ),
            secondary_y=False,
        )

    ffpi_plot = ffpi[["year", "ffpi_food"]].dropna()
    fig.add_trace(
        go.Scatter(
            x=ffpi_plot["year"],
            y=ffpi_plot["ffpi_food"],
            mode="lines",
            name="FFPI food",
            line={"color": COLORS["FFPI"], "width": 2, "dash": "dot"},
        ),
        secondary_y=True,
    )
    add_crisis_bands(fig)
    apply_chart_style(fig, height=580)
    fig.update_layout(title=f"{selected_item}: AUS/NZ Producer Price vs Global FFPI")
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Producer price (USD/tonne)", secondary_y=False)
    fig.update_yaxes(title_text="FFPI food index", secondary_y=True)
    st.plotly_chart(fig, width="stretch")

    outliers = filtered[filtered["is_outlier"].astype(str).str.lower() == "true"]
    if not outliers.empty:
        st.subheader("Flagged Outlier Observations")
        st.dataframe(
            outliers[["country", "item", "year", "value", "flag_description"]].sort_values("year"),
            use_container_width=True,
            hide_index=True,
        )


def volatility(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    st.title("Commodity Volatility")
    st.caption("Volatility highlights which commodities have unstable producer prices and may deserve closer monitoring.")
    story_insight(
        "Which commodities deserve attention?",
        "Average price alone is not enough; coefficient of variation highlights commodities with unstable producer prices after normalising for scale.",
        "Use high-volatility commodities as candidates for early-warning monitoring.",
    )

    country = st.radio("Country", ["Australia", "New Zealand"], horizontal=True)
    top_n = st.slider("Number of commodities", min_value=5, max_value=30, value=15, step=5)
    subset = master[master["country"] == country]

    vol = subset.groupby("item")["value"].agg(["mean", "std", "count"]).reset_index()
    vol = vol[vol["count"] >= 5]
    vol["cv_pct"] = vol["std"] / vol["mean"] * 100
    vol = vol.sort_values("cv_pct", ascending=False).head(top_n)

    fig = px.bar(
        vol.sort_values("cv_pct"),
        x="cv_pct",
        y="item",
        orientation="h",
        color="cv_pct",
        color_continuous_scale=RISK_SCALE,
        labels={"cv_pct": "Coefficient of variation (%)", "item": ""},
        hover_data={"mean": ":,.0f", "std": ":,.0f", "count": True},
        title=f"{country}: Most Volatile Producer Prices",
        template=CHART_TEMPLATE,
    )
    fig.add_vline(x=50, line_dash="dash", line_color=COLORS["risk"], annotation_text="50% CV")
    apply_chart_style(fig, height=max(500, top_n * 28))
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")


def global_context(data: dict[str, pd.DataFrame]) -> None:
    ffpi_a = data["ffpi_annual"]
    ffpi_m = data["ffpi_monthly"]
    ghi = data["ghi"]
    master_idx = data["master_idx"]

    st.title("Global Shock and Hunger Context")
    st.caption("Connect local producer-price movement to global food price shock periods and hunger severity.")
    story_insight(
        "So what is the global context?",
        "FFPI sub-indices reveal the shock environment, while GHI shows why equal price pressure can create unequal human consequences.",
        "Use this tab to connect the producer-price signal to global food-security risk.",
    )
    ffpi_cols = ["ffpi_food", "ffpi_cereals", "ffpi_meat", "ffpi_dairy", "ffpi_oils", "ffpi_sugar"]
    selected = st.multiselect(
        "FFPI indices",
        ffpi_cols,
        default=["ffpi_food", "ffpi_cereals", "ffpi_oils"],
        format_func=lambda x: x.replace("ffpi_", "").title(),
    )
    if not selected:
        selected = ["ffpi_food"]

    fig = px.line(
        ffpi_a[ffpi_a["year"] >= 1991],
        x="year",
        y=selected,
        color_discrete_map=FFPI_COLORS,
        labels={"value": "Index (2014-2016 = 100)", "year": "Year", "variable": "Index"},
        title="FAO Food Price Index Sub-Indices",
        template=CHART_TEMPLATE,
    )
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    add_crisis_bands(fig)
    apply_chart_style(fig, height=520)
    st.plotly_chart(fig, width="stretch")

    st.subheader("AUS/NZ Price Index Alignment with FFPI")
    corr = build_ffpi_correlation(master_idx, ffpi_a)
    fig_corr = px.bar(
        corr.sort_values(["country", "correlation"]),
        x="correlation",
        y="ffpi_index",
        color="country",
        barmode="group",
        orientation="h",
        color_discrete_map=COUNTRY_COLORS,
        labels={"correlation": "Pearson correlation", "ffpi_index": "FFPI sub-index"},
        title="Correlation between AUS/NZ Producer Price Index and FFPI Sub-Indices",
        template=CHART_TEMPLATE,
    )
    fig_corr.add_vline(x=0, line_color=COLORS["neutral"])
    apply_chart_style(fig_corr, height=420)
    st.plotly_chart(fig_corr, width="stretch")

    crisis_years = [2008, 2011, 2022]
    crisis = ffpi_a[ffpi_a["year"].isin(crisis_years)].set_index("year")
    st.subheader("Crisis-Year Price Shock Markers")
    cols = st.columns(len(crisis_years))
    for col, year in zip(cols, crisis_years):
        if year in crisis.index:
            col.metric(f"{year} FFPI food", f"{crisis.loc[year, 'ffpi_food']:.1f}")

    monthly = ffpi_m[ffpi_m["year"] >= 2000].copy()
    fig_monthly = px.area(
        monthly,
        x="date",
        y="ffpi_food",
        labels={"date": "Date", "ffpi_food": "FFPI food"},
        title="Monthly Food Price Shock Timeline",
        template=CHART_TEMPLATE,
    )
    fig_monthly.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    fig_monthly.update_traces(line_color=COLORS["FFPI"], fillcolor="rgba(222, 73, 104, 0.16)")
    apply_chart_style(fig_monthly, height=420)
    st.plotly_chart(fig_monthly, width="stretch")

    ghi_valid = ghi.dropna(subset=["iso3", "ghi_2025"])
    fig_map = px.choropleth(
        ghi_valid,
        locations="iso3",
        color="ghi_2025",
        hover_name="country_ghi",
        color_continuous_scale=RISK_SCALE,
        labels={"ghi_2025": "GHI 2025"},
        title="Global Hunger Index 2025",
        template=CHART_TEMPLATE,
    )
    apply_chart_style(fig_map, height=520)
    fig_map.update_layout(geo_showframe=False, geo_showcoastlines=True, geo_coastlinecolor=COLORS["neutral"])
    st.plotly_chart(fig_map, width="stretch")


def vulnerability(data: dict[str, pd.DataFrame]) -> None:
    vuln = build_vulnerability(data["ghi"], data["worldbank"])
    st.title("Hunger-Import Exposure Matrix")
    story_insight(
        "Who is least able to absorb the shock?",
        "Countries become priority cases when hunger severity and food-import dependency combine; the sliders then translate that baseline exposure into a scenario ranking.",
        "This is a prioritisation tool, not a bilateral trade-flow forecast.",
    )

    shock_pct = st.slider("Producer price shock", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
    basket_share = SCENARIO_ASSUMPTIONS["basket_share"]
    transmission_coeff = SCENARIO_ASSUMPTIONS["transmission_coeff"]
    pass_through_rate = SCENARIO_ASSUMPTIONS["pass_through_rate"]
    vuln = vuln.copy()
    effective_global_pressure_pct = shock_pct * basket_share * transmission_coeff * pass_through_rate
    vuln["implied_import_cost_pressure_pct"] = vuln["food_import_pct"] * effective_global_pressure_pct / 100
    vuln["scenario_pressure_score"] = vuln["exposure_index"] * vuln["implied_import_cost_pressure_pct"] / 100

    highest = vuln.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Highest exposure country", highest["country_ghi"])
    c2.metric("Exposure index", f"{highest['exposure_index']:.1f}/100")
    c3.metric("Producer shock", f"+{shock_pct}%")
    c4.metric("Fixed pass-through", f"{pass_through_rate:.0%}")
    c5.metric("Effective global pressure", f"{effective_global_pressure_pct:.2f}%")

    st.caption(
        "This is an exposure index, not a bilateral AUS/NZ trade-flow model. "
        "Dots stay in the same x/y position because GHI and food import dependency are baseline indicators; "
        "the shock slider changes the illustrative scenario pressure shown by bubble size, colour, and bar length. "
        "The scenario uses the team draft assumptions: basket share 45%, transmission coefficient 0.429, "
        "and pass-through 50%."
    )

    with st.expander("Methodology and caveats", expanded=False):
        st.markdown(
            """
            **Exposure index**

            `exposure_index = (0.60 x minmax(GHI 2025) + 0.40 x minmax(food import dependency)) x 100`

            **Scenario pressure**

            `effective_global_pressure = producer_price_shock x basket_share x transmission_coeff x pass_through_rate`

            `scenario_pressure_score = exposure_index x implied_import_cost_pressure / 100`

            **Current assumptions**

            - `basket_share = 0.45`
            - `transmission_coeff = 0.429`
            - `pass_through_rate = 0.50`

            This is not a bilateral AUS/NZ trade-flow model. It does not estimate exchange-rate effects,
            freight costs, tariffs, subsidies, or supplier substitution. It is a prioritisation tool for
            identifying countries structurally exposed to global food-price stress.
            """
        )

    x_med = vuln["ghi_2025"].median()
    y_med = vuln["food_import_pct"].median()
    max_possible_global_pressure_pct = 60 * basket_share * transmission_coeff * 1.0
    max_scenario_pressure = max(data["worldbank"]["food_import_pct"].max() * max_possible_global_pressure_pct / 100, 1)
    vuln["scenario_bubble_size"] = vuln["scenario_pressure_score"].clip(lower=0.02)
    max_scenario_score = max(
        (vuln["exposure_index"] * vuln["food_import_pct"] * max_possible_global_pressure_pct / 10000).max(),
        1,
    )
    fig = px.scatter(
        vuln,
        x="ghi_2025",
        y="food_import_pct",
        size="scenario_bubble_size",
        size_max=28,
        color="implied_import_cost_pressure_pct",
        hover_name="country_ghi",
        hover_data={
            "ghi_2025": ":.1f",
            "food_import_pct": ":.1f",
            "exposure_index": ":.1f",
            "scenario_bubble_size": False,
            "implied_import_cost_pressure_pct": ":.2f",
            "scenario_pressure_score": ":.2f",
        },
        color_continuous_scale=RISK_SCALE,
        range_color=[0, max_scenario_pressure],
        labels={
            "ghi_2025": "GHI score 2025",
            "food_import_pct": "Food imports (% of merchandise imports)",
            "exposure_index": "Hunger-import exposure index",
            "scenario_bubble_size": "Scenario pressure score",
            "implied_import_cost_pressure_pct": "Implied import-cost pressure (%)",
            "scenario_pressure_score": "Scenario pressure score",
        },
        title=(
            "Hunger Severity x Food Import Dependency "
            f"under +{shock_pct}% Producer Shock and {effective_global_pressure_pct:.2f}% Effective Global Pressure"
        ),
        template=CHART_TEMPLATE,
    )
    fig.add_vline(x=x_med, line_dash="dash", line_color=COLORS["neutral"])
    fig.add_hline(y=y_med, line_dash="dash", line_color=COLORS["neutral"])
    fig.update_traces(marker={"line": {"color": "rgba(255,255,255,0.42)", "width": 0.8}, "opacity": 0.9})
    apply_chart_style(fig, height=620)
    st.plotly_chart(fig, width="stretch")

    top = vuln.nlargest(15, "scenario_pressure_score").sort_values("scenario_pressure_score")
    fig_bar = px.bar(
        top,
        x="scenario_pressure_score",
        y="country_ghi",
        orientation="h",
        color="scenario_pressure_score",
        color_continuous_scale=RISK_SCALE,
        range_color=[0, max_scenario_score],
        hover_data={
            "ghi_2025": ":.1f",
            "food_import_pct": ":.1f",
            "exposure_index": ":.1f",
            "implied_import_cost_pressure_pct": ":.2f",
        },
        labels={
            "scenario_pressure_score": "Scenario pressure score",
            "country_ghi": "",
            "exposure_index": "Exposure index",
        },
        title=(
            "Illustrative What-if Ranking: "
            f"+{shock_pct}% Producer Shock x Basket/Transmission/Pass-through Assumptions"
        ),
        template=CHART_TEMPLATE,
    )
    fig_bar.update_traces(marker_line_color="rgba(255,255,255,0.22)", marker_line_width=0.8)
    fig_bar.update_xaxes(range=[0, max_scenario_score])
    apply_chart_style(fig_bar, height=560)
    st.plotly_chart(fig_bar, width="stretch")

    st.subheader("Country Deep Dive")
    country = st.selectbox("Inspect a country", vuln["country_ghi"].tolist())
    selected = vuln[vuln["country_ghi"] == country].iloc[0]
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("GHI 2025", f"{selected['ghi_2025']:.1f}")
    d2.metric("Food import dependency", f"{selected['food_import_pct']:.1f}%")
    d3.metric("Exposure index", f"{selected['exposure_index']:.1f}/100")
    d4.metric("Scenario pressure", f"{selected['scenario_pressure_score']:.2f}")

    trend_cols = ["ghi_2000", "ghi_2008", "ghi_2016", "ghi_2025"]
    trend = pd.DataFrame(
        {
            "year": [2000, 2008, 2016, 2025],
            "ghi_score": [selected[col] for col in trend_cols],
        }
    ).dropna()
    fig_trend = px.line(
        trend,
        x="year",
        y="ghi_score",
        markers=True,
        labels={"year": "Year", "ghi_score": "GHI score"},
        title=f"{country}: Hunger Score Trend",
        template=CHART_TEMPLATE,
    )
    fig_trend.update_traces(line_color=COLORS["risk"], marker_color=COLORS["risk"])
    apply_chart_style(fig_trend, height=340)
    st.plotly_chart(fig_trend, width="stretch")


def data_explorer(data: dict[str, pd.DataFrame]) -> None:
    st.title("Data Explorer")
    story_insight(
        "Can the audience inspect the evidence?",
        "This tab exposes the cleaned source tables so the dashboard remains transparent and auditable.",
        "Use it during Q&A if someone asks where a number or variable came from.",
    )
    label_to_key = {
        "Producer prices, USD": "master_usd",
        "Producer price index": "master_idx",
        "FFPI annual": "ffpi_annual",
        "FFPI monthly": "ffpi_monthly",
        "Global Hunger Index": "ghi",
        "World Bank food imports": "worldbank",
    }
    label = st.selectbox("Dataset", list(label_to_key))
    df = data[label_to_key[label]]
    st.caption(f"{len(df):,} rows x {df.shape[1]:,} columns")
    st.dataframe(df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="FAOSTAT Food Price Shocks", layout="wide")
    data = load_data()

    with st.sidebar:
        st.title("FAOSTAT Viz")
        page = st.radio(
            "View",
            [
                "Context",
                "Producer Signal",
                "Vulnerability",
                "What-If Action",
                "Appendix",
            ],
        )
        st.divider()
        st.caption(f"Local data: {PROCESSED_DIR}")

    if not require_data(data):
        return

    pages = {
        "Context": slide_context,
        "Producer Signal": slide_producer_signal,
        "Vulnerability": slide_vulnerability,
        "What-If Action": slide_what_if,
        "Appendix": appendix,
    }
    pages[page](data)


if __name__ == "__main__":
    main()
