"""Producer signal tab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.analysis import build_ffpi_correlation
from app.config import CHART_TEMPLATE, COLORS, COUNTRY_COLORS
from app.style import add_crisis_bands, apply_chart_style, story_insight


def slide_producer_signal(data: dict[str, pd.DataFrame], controls: dict[str, object]) -> None:
    master = data["master_usd"]
    master_idx = data["master_idx"]
    ffpi = data["ffpi_annual"]
    selected_item = str(controls["selected_item"])
    selected_countries = list(controls["selected_countries"])
    year_range = controls["year_range"]
    master_filtered = master[
        master["year"].between(year_range[0], year_range[1]) & master["country"].isin(selected_countries)
    ]
    ffpi_filtered = ffpi[ffpi["year"].between(year_range[0], year_range[1])]
    item_signal = master_filtered[master_filtered["item"].eq(selected_item)].merge(
        ffpi_filtered[["year", "ffpi_food"]], on="year", how="left", suffixes=("", "_annual")
    )
    if "ffpi_food_annual" in item_signal.columns:
        item_signal["ffpi_food"] = item_signal["ffpi_food_annual"].fillna(item_signal["ffpi_food"])
    item_signal = item_signal.sort_values(["country", "year"])

    st.title("Australia and New Zealand Producer Price Signal")
    st.caption("Commodity, country, and time range respond to the global analysis scope.")
    story_insight(
        "Producer prices provide the supply-side signal",
        f"{selected_item} is shown against the global FFPI to test whether the selected commodity moves through shock periods.",
        "Compare producer-price movement with global food-price pressure.",
    )
    if selected_item == "Wheat":
        st.caption(
            "Wheat is the default signal because it is a globally traded staple, appears in the AUS/NZ producer-price data, "
            "and provides an intuitive bridge between producer prices and food-security risk."
        )

    st.subheader(f"{selected_item} Producer Prices vs Global FFPI")
    if item_signal.empty:
        st.warning("The selected commodity/country/time combination is not available in the current producer-price file.")
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for country, color in [("Australia", COLORS["AUS"]), ("New Zealand", COLORS["NZL"])]:
            country_df = item_signal[item_signal["country"] == country]
            if country_df.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=country_df["year"],
                    y=country_df["value"],
                    mode="lines+markers",
                    name=f"{country} {selected_item}",
                    line={"color": color, "width": 3},
                    hovertemplate="<b>%{fullData.name}</b><br>Year %{x}<br>USD/tonne: $%{y:,.0f}<extra></extra>",
                ),
                secondary_y=False,
            )
        ffpi_plot = ffpi_filtered[["year", "ffpi_food"]].dropna()
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
        fig.update_layout(title=f"AUS/NZ {selected_item} Producer Prices vs Global Food Price Index")
        fig.update_yaxes(title_text=f"{selected_item} producer price (USD/tonne)", secondary_y=False)
        fig.update_yaxes(title_text="FFPI food index", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Supporting Evidence")
    corr = build_ffpi_correlation(
        master_idx[master_idx["year"].between(year_range[0], year_range[1])],
        ffpi_filtered,
    )
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
    st.plotly_chart(fig_corr, use_container_width=True)
