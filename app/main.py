"""Streamlit entrypoint for the FAOSTAT food price shock dashboard."""

from __future__ import annotations

import streamlit as st

from app.controls import sidebar_controls
from app.data import load_data, require_data
from app.tabs import (
    appendix,
    executive_brief,
    slide_context,
    slide_producer_signal,
    slide_vulnerability,
    slide_what_if,
)


def main() -> None:
    st.set_page_config(page_title="Food Price Shock Early Warning", layout="wide")
    data = load_data()

    if not require_data(data):
        return

    controls = sidebar_controls(data)

    tabs = st.tabs(
        [
            "Executive Brief",
            "1. Shock Context",
            "2. Producer Signal",
            "3. Vulnerability",
            "4. What-If Action",
            "5. Evidence Base",
        ]
    )
    with tabs[0]:
        executive_brief(data, controls)
    with tabs[1]:
        slide_context(data, controls)
    with tabs[2]:
        slide_producer_signal(data, controls)
    with tabs[3]:
        slide_vulnerability(data, controls)
    with tabs[4]:
        slide_what_if(data, controls)
    with tabs[5]:
        appendix(data, controls)


if __name__ == "__main__":
    main()
