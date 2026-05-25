"""Evidence base tab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.config import CHART_TEMPLATE, COLORS, RISK_SCALE
from app.style import apply_chart_style


def appendix(data: dict[str, pd.DataFrame], controls: dict[str, object]) -> None:
    st.title("Evidence Base")
    st.caption("Transparent source tables and volatility checks supporting the policy narrative.")

    st.subheader("Dataset Explorer")
    label_to_key = {
        "Producer prices, USD": "master_usd",
        "Producer price index": "master_idx",
        "FFPI annual": "ffpi_annual",
        "FFPI monthly": "ffpi_monthly",
        "Global Hunger Index": "ghi",
        "World Bank food imports": "worldbank",
    }
    label = str(controls["dataset_label"])
    df = data[label_to_key[label]]
    st.caption(f"{len(df):,} rows x {df.shape[1]:,} columns")
    st.dataframe(df, width="stretch", hide_index=True)

    st.subheader("Commodity Volatility")
    country = str(controls["volatility_country"])
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
    st.plotly_chart(fig_vol, use_container_width=True)
