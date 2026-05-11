"""Streamlit dashboard for FAOSTAT food price shock analysis."""

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data_pipeline.faostat_client import FaostatApiError, get_domain_data

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
    "AUS": "#2f6f9f",
    "NZL": "#b8552f",
    "FFPI": "#4d4d4d",
    "risk": "#b2182b",
    "crisis": "#b2182b",
    "neutral": "#777777",
}

CHART_TEMPLATE = "plotly_white"
COUNTRY_COLORS = {
    "AUS": COLORS["AUS"],
    "NZL": COLORS["NZL"],
    "Australia": COLORS["AUS"],
    "New Zealand": COLORS["NZL"],
}
FFPI_COLORS = {
    "ffpi_food": "#4d4d4d",
    "ffpi_cereals": "#7b8f55",
    "ffpi_meat": "#b8552f",
    "ffpi_dairy": "#6f7f94",
    "ffpi_oils": "#8b6f8f",
    "ffpi_sugar": "#a75d4f",
}
RISK_SCALE = [
    [0.00, "#edf3f1"],
    [0.35, "#a8c5b5"],
    [0.70, "#c9955c"],
    [1.00, "#b2182b"],
]

EXPOSURE_WEIGHTS = {
    "ghi": 0.6,
    "import_dependency": 0.4,
}


def apply_chart_style(fig: go.Figure, height: int | None = None, show_legend: bool | None = None) -> go.Figure:
    layout = {
        "template": CHART_TEMPLATE,
        "font": {"family": "Source Sans Pro, Arial, sans-serif"},
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

    year_min = int(master["year"].min())
    year_max = int(master["year"].max())
    latest_ffpi = ffpi.dropna(subset=["ffpi_food"]).sort_values("year").iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coverage", f"{year_min}-{year_max}")
    c2.metric("Commodities", f"{master['item'].nunique():,}")
    c3.metric("Producer price rows", f"{len(master):,}")
    c4.metric("Latest FFPI food", f"{latest_ffpi['ffpi_food']:.1f}", f"{int(latest_ffpi['year'])}")

    country_summary = (
        master.groupby(["iso3", "country"], as_index=False)
        .agg(avg_usd_per_tonne=("value", "mean"), commodities=("item", "nunique"), outliers=("is_outlier", "sum"))
        .sort_values("iso3")
    )
    fig = px.bar(
        country_summary,
        x="country",
        y="avg_usd_per_tonne",
        color="iso3",
        text="commodities",
        color_discrete_map=COUNTRY_COLORS,
        labels={"avg_usd_per_tonne": "Average producer price (USD/tonne)", "country": ""},
        title="Average Producer Price by Country",
        template=CHART_TEMPLATE,
    )
    fig.update_traces(
        marker_line_color="rgba(255,255,255,0.24)",
        marker_line_width=1,
        textfont_color=COLORS["neutral"],
        texttemplate="%{text} commodities",
        textposition="outside",
    )
    apply_chart_style(fig, height=420, show_legend=False)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Highest Hunger-Import Exposure")
    st.dataframe(
        vuln.head(10)[["country_ghi", "ghi_2025", "food_import_pct", "exposure_index"]].round(2),
        use_container_width=True,
        hide_index=True,
    )


def price_trends(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]

    st.title("Producer Price Trends")
    st.caption("Start with the supply-side signal: how AUS/NZ commodity prices move through time.")
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
    fig_monthly.update_traces(line_color=COLORS["FFPI"], fillcolor="rgba(178, 24, 43, 0.16)")
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
    fig_map.update_layout(geo_showframe=False, geo_showcoastlines=True, geo_coastlinecolor="#b8c3c9")
    st.plotly_chart(fig_map, width="stretch")


def vulnerability(data: dict[str, pd.DataFrame]) -> None:
    vuln = build_vulnerability(data["ghi"], data["worldbank"])
    st.title("Hunger-Import Exposure Matrix")

    shock_pct = st.slider("Producer price shock", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
    pass_through_pct = st.slider(
        "Producer-to-import price pass-through",
        min_value=0,
        max_value=100,
        value=25,
        step=5,
        format="%d%%",
        help="Illustrative assumption: only part of a producer-price shock reaches import prices.",
    )
    vuln = vuln.copy()
    global_price_pressure_pct = shock_pct * pass_through_pct / 100
    vuln["implied_import_cost_pressure_pct"] = vuln["food_import_pct"] * global_price_pressure_pct / 100
    vuln["scenario_pressure_score"] = vuln["exposure_index"] * vuln["implied_import_cost_pressure_pct"] / 100

    highest = vuln.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Highest exposure", highest["country_ghi"], f"{highest['exposure_index']:.1f}/100")
    c2.metric("Producer shock", f"+{shock_pct}%")
    c3.metric("Pass-through", f"{pass_through_pct}%")
    c4.metric("Global pressure assumption", f"{global_price_pressure_pct:.1f}%")

    st.caption(
        "This is an exposure index, not a bilateral AUS/NZ trade-flow model. "
        "Dots stay in the same x/y position because GHI and food import dependency are baseline indicators; "
        "the sliders change the illustrative scenario pressure shown by bubble size, colour, and bar length. "
        "The country order may stay similar because the shock is applied as a shared global multiplier."
    )

    with st.expander("Methodology and caveats", expanded=False):
        st.markdown(
            """
            **Exposure index**

            `exposure_index = (0.60 x minmax(GHI 2025) + 0.40 x minmax(food import dependency)) x 100`

            **Scenario pressure**

            `global_price_pressure = producer_price_shock x pass_through_rate`

            `scenario_pressure_score = exposure_index x implied_import_cost_pressure / 100`

            This is not a bilateral AUS/NZ trade-flow model. It does not estimate exchange-rate effects,
            freight costs, tariffs, subsidies, or supplier substitution. It is a prioritisation tool for
            identifying countries structurally exposed to global food-price stress.
            """
        )

    x_med = vuln["ghi_2025"].median()
    y_med = vuln["food_import_pct"].median()
    max_possible_global_pressure_pct = 60
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
            f"under +{shock_pct}% Producer Shock and {pass_through_pct}% Pass-through"
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
            f"+{shock_pct}% Producer Shock x {pass_through_pct}% Pass-through"
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


@st.cache_data(show_spinner=False, ttl=3600)
def load_live_faostat_pp(params: tuple[tuple[str, str], ...], access_token: str | None) -> pd.DataFrame:
    return get_domain_data("PP", list(params), access_token=access_token)


def live_faostat(data: dict[str, pd.DataFrame]) -> None:
    st.title("Live FAOSTAT Preview")
    st.caption(
        "This page calls the FAOSTAT Producer Prices API directly. "
        "The main dashboard still uses cleaned local files in data/processed."
    )
    st.info("Paste a temporary FAOSTAT token here for demos, or leave it blank to use `FAOSTAT_ACCESS_TOKEN` from `.env`.")
    st.markdown(
        "Get a token from the [FAOSTAT Developer Portal](https://www.fao.org/faostat/en/#developer-portal). "
        "Tokens are short-lived, so refresh it if a request starts failing."
    )

    access_token = st.text_input(
        "FAOSTAT access token",
        type="password",
        placeholder="Bearer token from FAOSTAT Developer Portal",
        help="Stored only in the current Streamlit session. Do not paste tokens into code, README, or commits.",
    ).strip()
    token_for_request = access_token or None

    col1, col2 = st.columns(2)
    with col1:
        area = st.text_input("Area code/filter", value="5501>")
        item = st.text_input("Item code", value="809")
        month = st.text_input("Month code", value="7021")
    with col2:
        years = st.multiselect("Years", ["2025", "2024", "2023", "2022", "2021"], default=["2025", "2024", "2023"])
        elements = st.multiselect(
            "Elements",
            ["5530", "5532", "5539"],
            default=["5530", "5532", "5539"],
            help="5530 LCU/tonne, 5532 USD/tonne, 5539 Producer Price Index.",
        )

    params = (
        ("area", area),
        ("element", ",".join(elements)),
        ("item", item),
        ("year", ",".join(years)),
        ("month", month),
        ("output_type", "csv"),
    )
    st.code(
        "https://faostatservices.fao.org/api/v1/en/data/PP?"
        + "&".join(f"{key}={value}" for key, value in params),
        language="text",
    )

    if st.button("Fetch Live FAOSTAT Data", type="primary"):
        try:
            live_df = load_live_faostat_pp(params, token_for_request)
        except FaostatApiError as exc:
            st.error(str(exc))
            st.info("Paste a current token above or set FAOSTAT_ACCESS_TOKEN in your local .env file.")
            return
        except Exception as exc:
            st.error(f"Could not fetch FAOSTAT data: {exc}")
            return

        st.success(f"Fetched {len(live_df):,} rows from FAOSTAT.")
        st.dataframe(live_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="FAOSTAT Food Price Shocks", layout="wide")
    data = load_data()

    with st.sidebar:
        st.title("FAOSTAT Viz")
        page = st.radio(
            "View",
            [
                "Overview",
                "Price Trends",
                "Volatility",
                "Global Context",
                "Exposure Matrix",
                "Live FAOSTAT",
                "Data Explorer",
            ],
        )
        st.divider()
        st.caption(f"Local data: {PROCESSED_DIR}")

    if not require_data(data):
        return

    pages = {
        "Overview": overview,
        "Price Trends": price_trends,
        "Volatility": volatility,
        "Global Context": global_context,
        "Exposure Matrix": vulnerability,
        "Live FAOSTAT": live_faostat,
        "Data Explorer": data_explorer,
    }
    pages[page](data)


if __name__ == "__main__":
    main()
