"""Reusable Streamlit and Plotly presentation helpers."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.config import CHART_TEMPLATE, COLORS, CRISIS_PERIODS


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
        text += f"\n\n**Policy use:** {action}"
    st.info(text)


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
