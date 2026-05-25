"""Global shock context tab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.config import CHART_TEMPLATE, COLORS, FFPI_COLORS
from app.style import add_crisis_bands, apply_chart_style, story_insight


def slide_context(data: dict[str, pd.DataFrame], controls: dict[str, object]) -> None:
    ffpi = data["ffpi_annual"]
    ffpi_m = data["ffpi_monthly"]

    st.title("Why Food Price Shocks Matter")
    st.caption("Global food-price pressure has surged repeatedly; the question is who has the least capacity to absorb it.")
    story_insight(
        "Food price shocks are global, but vulnerability is not evenly shared",
        "The FFPI shows repeated global stress events across the last three decades.",
        "Use shock periods as context for interpreting producer-price signals and exposure priorities.",
    )

    selected_indices = list(controls["selected_indices"])
    year_range = controls["year_range"]

    ffpi_filtered = ffpi[ffpi["year"].between(year_range[0], year_range[1])]
    ffpi_m_filtered = ffpi_m[ffpi_m["year"].between(year_range[0], year_range[1])]

    st.subheader("Global Food Price Shock Timeline")
    fig = px.line(
        ffpi_filtered,
        x="year",
        y=selected_indices,
        color_discrete_map=FFPI_COLORS,
        labels={"value": "Index (2014-2016 = 100)", "variable": "Index"},
        title="When the World's Food Got Expensive",
        template=CHART_TEMPLATE,
    )
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    add_crisis_bands(fig)
    apply_chart_style(fig, height=560)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Supporting Evidence")
    c1, c2, c3 = st.columns(3)
    crisis_years = [2008, 2011, 2022]
    crisis = ffpi_filtered[ffpi_filtered["year"].isin(crisis_years)].set_index("year")
    for col, year in zip([c1, c2, c3], crisis_years):
        if year in crisis.index:
            col.metric(f"{year} FFPI food", f"{crisis.loc[year, 'ffpi_food']:.1f}")
        else:
            col.metric(f"{year} FFPI food", "outside range")

    fig_monthly = px.area(
        ffpi_m_filtered,
        x="date",
        y="ffpi_food",
        labels={"date": "Date", "ffpi_food": "FFPI food"},
        title="Monthly Food Price Shock Timeline",
        template=CHART_TEMPLATE,
    )
    fig_monthly.add_hline(y=100, line_dash="dash", line_color=COLORS["neutral"])
    fig_monthly.update_traces(line_color=COLORS["FFPI"], fillcolor="rgba(222, 73, 104, 0.16)")
    apply_chart_style(fig_monthly, height=390)
    st.plotly_chart(fig_monthly, use_container_width=True)
