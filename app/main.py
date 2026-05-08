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
    "AUS": "#2166ac",
    "NZL": "#b8552f",
    "FFPI": "#4d4d4d",
    "risk": "#b2182b",
}


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
            fillcolor="#d6604d",
            opacity=0.11,
            line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation_font_size=10,
            yref=yref,
        )


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
    vuln["vulnerability_score"] = vuln["ghi_2025"] * vuln["food_import_pct"]
    return vuln.sort_values("vulnerability_score", ascending=False)


def overview(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]
    vuln = build_vulnerability(data["ghi"], data["worldbank"])

    st.title("FAOSTAT Producer Prices: Shock Exposure Dashboard")
    st.caption("Australia and New Zealand producer prices, global food price shocks, and import-dependent hunger risk.")

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
        color_discrete_map=COLORS,
        labels={"avg_usd_per_tonne": "Average producer price (USD/tonne)", "country": ""},
        title="Average Producer Price by Country",
    )
    fig.update_traces(texttemplate="%{text} commodities", textposition="outside")
    fig.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Highest Vulnerability Scores")
    st.dataframe(
        vuln.head(10)[["country_ghi", "ghi_2025", "food_import_pct", "vulnerability_score"]].round(2),
        width="stretch",
        hide_index=True,
    )


def price_trends(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]

    st.title("Producer Price Trends")
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
    fig.update_layout(title=f"{selected_item}: AUS/NZ Producer Price vs Global FFPI", height=580)
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Producer price (USD/tonne)", secondary_y=False)
    fig.update_yaxes(title_text="FFPI food index", secondary_y=True)
    st.plotly_chart(fig, width="stretch")

    outliers = filtered[filtered["is_outlier"].astype(str).str.lower() == "true"]
    if not outliers.empty:
        st.subheader("Flagged Outlier Observations")
        st.dataframe(
            outliers[["country", "item", "year", "value", "flag_description"]].sort_values("year"),
            width="stretch",
            hide_index=True,
        )


def volatility(data: dict[str, pd.DataFrame]) -> None:
    master = data["master_usd"]
    st.title("Commodity Volatility")

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
        color_continuous_scale="RdYlGn_r",
        labels={"cv_pct": "Coefficient of variation (%)", "item": ""},
        hover_data={"mean": ":,.0f", "std": ":,.0f", "count": True},
        title=f"{country}: Most Volatile Producer Prices",
    )
    fig.add_vline(x=50, line_dash="dash", line_color=COLORS["risk"], annotation_text="50% CV")
    fig.update_layout(height=max(500, top_n * 28), coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")


def global_context(data: dict[str, pd.DataFrame]) -> None:
    ffpi_a = data["ffpi_annual"]
    ffpi_m = data["ffpi_monthly"]
    ghi = data["ghi"]

    st.title("Global Shock and Hunger Context")
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
        labels={"value": "Index (2014-2016 = 100)", "year": "Year", "variable": "Index"},
        title="FAO Food Price Index Sub-Indices",
    )
    fig.add_hline(y=100, line_dash="dash", line_color="#555555")
    add_crisis_bands(fig)
    fig.update_layout(height=520)
    st.plotly_chart(fig, width="stretch")

    monthly = ffpi_m[ffpi_m["year"] >= 2000].copy()
    fig_monthly = px.area(
        monthly,
        x="date",
        y="ffpi_food",
        labels={"date": "Date", "ffpi_food": "FFPI food"},
        title="Monthly Food Price Shock Timeline",
    )
    fig_monthly.add_hline(y=100, line_dash="dash", line_color="#555555")
    fig_monthly.update_traces(line_color="#2b2b2b", fillcolor="rgba(178, 24, 43, 0.22)")
    fig_monthly.update_layout(height=420)
    st.plotly_chart(fig_monthly, width="stretch")

    ghi_valid = ghi.dropna(subset=["iso3", "ghi_2025"])
    fig_map = px.choropleth(
        ghi_valid,
        locations="iso3",
        color="ghi_2025",
        hover_name="country_ghi",
        color_continuous_scale="YlOrRd",
        labels={"ghi_2025": "GHI 2025"},
        title="Global Hunger Index 2025",
    )
    fig_map.update_layout(height=520, geo_showframe=False, geo_showcoastlines=True)
    st.plotly_chart(fig_map, width="stretch")


def vulnerability(data: dict[str, pd.DataFrame]) -> None:
    vuln = build_vulnerability(data["ghi"], data["worldbank"])
    st.title("Vulnerability Matrix")

    shock_pct = st.slider("Producer price shock", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
    vuln = vuln.copy()
    vuln["implied_cost_increase_pct"] = vuln["food_import_pct"] * shock_pct / 100

    st.caption(
        "The dots stay in the same x/y position because GHI and food import dependency are baseline indicators. "
        "The slider changes the scenario impact, shown by dot colour and the what-if ranking below."
    )

    x_med = vuln["ghi_2025"].median()
    y_med = vuln["food_import_pct"].median()
    max_scenario_cost = data["worldbank"]["food_import_pct"].max() * 0.6
    fig = px.scatter(
        vuln,
        x="ghi_2025",
        y="food_import_pct",
        size="vulnerability_score",
        color="implied_cost_increase_pct",
        hover_name="country_ghi",
        hover_data={
            "ghi_2025": ":.1f",
            "food_import_pct": ":.1f",
            "vulnerability_score": ":.1f",
            "implied_cost_increase_pct": ":.1f",
        },
        color_continuous_scale="YlOrRd",
        range_color=[0, max_scenario_cost],
        labels={
            "ghi_2025": "GHI score 2025",
            "food_import_pct": "Food imports (% of merchandise imports)",
            "vulnerability_score": "Vulnerability score",
            "implied_cost_increase_pct": "Implied cost increase (%)",
        },
        title=f"Hunger Severity x Food Import Dependency under +{shock_pct}% Price Shock",
    )
    fig.add_vline(x=x_med, line_dash="dash", line_color="#777777")
    fig.add_hline(y=y_med, line_dash="dash", line_color="#777777")
    fig.update_layout(height=620)
    st.plotly_chart(fig, width="stretch")

    top = vuln.nlargest(15, "implied_cost_increase_pct").sort_values("implied_cost_increase_pct")
    fig_bar = px.bar(
        top,
        x="implied_cost_increase_pct",
        y="country_ghi",
        orientation="h",
        color="ghi_2025",
        color_continuous_scale="YlOrRd",
        labels={"implied_cost_increase_pct": "Implied food cost increase (%)", "country_ghi": ""},
        title=f"What-if Scenario: +{shock_pct}% AUS/NZ Producer Price Shock",
    )
    fig_bar.update_layout(height=560)
    st.plotly_chart(fig_bar, width="stretch")


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
    st.dataframe(df, width="stretch", hide_index=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_live_faostat_pp(params: tuple[tuple[str, str], ...]) -> pd.DataFrame:
    return get_domain_data("PP", list(params))


def live_faostat(data: dict[str, pd.DataFrame]) -> None:
    st.title("Live FAOSTAT Preview")
    st.caption(
        "This page calls the FAOSTAT Producer Prices API directly. "
        "The main dashboard still uses cleaned local files in data/processed."
    )

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
            live_df = load_live_faostat_pp(params)
        except FaostatApiError as exc:
            st.error(str(exc))
            st.info("Add a current FAOSTAT_ACCESS_TOKEN to your local .env file. Do not commit real tokens.")
            return
        except Exception as exc:
            st.error(f"Could not fetch FAOSTAT data: {exc}")
            return

        st.success(f"Fetched {len(live_df):,} rows from FAOSTAT.")
        st.dataframe(live_df, width="stretch", hide_index=True)


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
                "Vulnerability",
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
        "Vulnerability": vulnerability,
        "Live FAOSTAT": live_faostat,
        "Data Explorer": data_explorer,
    }
    pages[page](data)


if __name__ == "__main__":
    main()
