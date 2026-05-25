"""Executive brief tab."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.analysis import build_vulnerability, priority_table
from app.style import story_insight


def executive_brief(data: dict[str, pd.DataFrame], controls: dict[str, object]) -> None:
    master = data["master_usd"]
    ffpi = data["ffpi_annual"]
    exposure = build_vulnerability(data["ghi"], data["worldbank"], float(controls["hunger_weight"]))

    st.title("Food Price Shock Early-Warning Portfolio")
    st.caption("Built for a UN Food Systems Summit Panel or regional food-security policy board.")
    story_insight(
        "Decision problem",
        "Producer-price and global food-price shocks become policy priorities when they meet countries with high hunger severity and high food-import dependency.",
        "Prioritise monitoring, preparedness funding, and import-buffer planning where exposure is highest.",
    )

    year_min = int(master["year"].min())
    year_max = int(master["year"].max())
    latest_ffpi = ffpi.dropna(subset=["ffpi_food"]).sort_values("year").iloc[-1]
    top_country = exposure.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Producer-price coverage", f"{year_min}-{year_max}")
    c2.metric("AUS/NZ commodities", f"{master['item'].nunique():,}")
    c3.metric(f"Latest FFPI food ({int(latest_ffpi['year'])})", f"{latest_ffpi['ffpi_food']:.1f}")
    c4.metric("Highest exposure", top_country["country_ghi"], f"{top_country['exposure_index']:.1f}/100")

    st.caption(
        f"Current scope: {controls['year_range'][0]}-{controls['year_range'][1]}, "
        f"{controls['selected_item']}, {', '.join(controls['selected_countries'])}."
    )

    left, right = st.columns([0.54, 0.46])
    with left:
        st.subheader("Policy Watchlist")
        st.dataframe(priority_table(exposure, 10), width="stretch", hide_index=True)
        st.caption(
            "Suggested policy use is a triage label for discussion; it does not replace country-level field assessment."
        )

    with right:
        st.subheader("Narrative Route")
        st.markdown(
            """
            1. **Shock Context:** confirm global food-price stress periods.
            2. **Producer Signal:** inspect AUS/NZ commodity-price movement.
            3. **Vulnerability:** identify hunger-import exposure.
            4. **What-If Action:** stress-test scenario assumptions.
            5. **Evidence Base:** inspect cleaned data and volatility.
            """
        )
        st.warning(
            "Key boundary: this is an early-warning and prioritisation tool, not a bilateral trade-flow or causal import-price forecast."
        )
