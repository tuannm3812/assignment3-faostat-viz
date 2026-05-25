"""Sidebar controls that define analysis scope and model assumptions."""

from __future__ import annotations

import streamlit as st

from app.config import EXPOSURE_WEIGHTS, SCENARIO_ASSUMPTIONS


def sidebar_controls(data: dict[str, pd.DataFrame]) -> dict[str, object]:
    ffpi_cols = ["ffpi_food", "ffpi_cereals", "ffpi_meat", "ffpi_dairy", "ffpi_oils", "ffpi_sugar"]
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]

    st.sidebar.title("Food Shock Early Warning")
    st.sidebar.caption("Analysis scope and model assumptions")

    with st.sidebar.expander("Global Analysis Scope", expanded=True):
        year_range = st.slider(
            "Year range",
            min_value=int(ffpi["year"].min()),
            max_value=int(ffpi["year"].max()),
            value=(max(1991, int(ffpi["year"].min())), int(ffpi["year"].max())),
            step=1,
        )
        selected_indices = st.multiselect(
            "FAO Food Price Index series",
            ffpi_cols,
            default=["ffpi_food", "ffpi_cereals", "ffpi_oils"],
            format_func=lambda value: value.replace("ffpi_", "").title(),
        )
        if not selected_indices:
            selected_indices = ["ffpi_food"]

    with st.sidebar.expander("Producer Signal Scope", expanded=True):
        items = sorted(master["item"].dropna().unique())
        default_item = "Wheat" if "Wheat" in items else items[0]
        selected_item = st.selectbox("Commodity", items, index=items.index(default_item))
        selected_countries = st.multiselect(
            "Producer countries",
            ["Australia", "New Zealand"],
            default=["Australia", "New Zealand"],
        )
        if not selected_countries:
            selected_countries = ["Australia", "New Zealand"]

    with st.sidebar.expander("Exposure Assumptions", expanded=True):
        hunger_weight = st.slider(
            "Food-access stress weight",
            min_value=0.0,
            max_value=1.0,
            value=EXPOSURE_WEIGHTS["ghi"],
            step=0.05,
            format="%.2f",
        )
        st.caption(f"Food import dependency weight: {1 - hunger_weight:.2f}")

    with st.sidebar.expander("Scenario Assumptions", expanded=True):
        shock_pct = st.slider("Producer price shock", min_value=0, max_value=60, value=20, step=5, format="+%d%%")
        basket_share_pct = st.slider(
            "Relevant import basket share",
            min_value=0,
            max_value=100,
            value=int(SCENARIO_ASSUMPTIONS["basket_share"] * 100),
            step=5,
            format="%d%%",
        )
        transmission_pct = st.slider(
            "Transmission coefficient",
            min_value=0,
            max_value=100,
            value=int(round(SCENARIO_ASSUMPTIONS["transmission_coeff"] * 100)),
            step=5,
            format="%d%%",
        )
        pass_through_pct = st.slider(
            "Producer-to-import pass-through",
            min_value=0,
            max_value=100,
            value=int(SCENARIO_ASSUMPTIONS["pass_through_rate"] * 100),
            step=5,
            format="%d%%",
        )

    with st.sidebar.expander("Evidence Options", expanded=False):
        dataset_label = st.selectbox(
            "Dataset",
            [
                "Producer prices, USD",
                "Producer price index",
                "FFPI annual",
                "FFPI monthly",
                "Global Hunger Index",
                "World Bank food imports",
            ],
        )
        volatility_country = st.radio("Volatility country", ["Australia", "New Zealand"], horizontal=True)

    return {
        "year_range": year_range,
        "selected_indices": selected_indices,
        "selected_item": selected_item,
        "selected_countries": selected_countries,
        "hunger_weight": hunger_weight,
        "shock_pct": shock_pct,
        "basket_share": basket_share_pct / 100,
        "transmission_coeff": transmission_pct / 100,
        "pass_through_rate": pass_through_pct / 100,
        "dataset_label": dataset_label,
        "volatility_country": volatility_country,
    }
