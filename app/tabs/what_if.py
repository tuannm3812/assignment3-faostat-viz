"""What-if scenario tab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.analysis import build_corrected_vulnerability, build_scenario, build_weight_sensitivity, priority_table
from app.config import CHART_TEMPLATE, RISK_SCALE
from app.style import apply_chart_style, story_insight


def slide_what_if(data: dict[str, pd.DataFrame], controls: dict[str, object]) -> None:
    exposure = build_corrected_vulnerability(data["ghi"], data["worldbank"], float(controls["hunger_weight"]))

    st.title("What-If Scenario and Priority Ranking")
    st.caption(
        "Stress-test how an AUS/NZ producer-price shock could translate into priority monitoring for structurally exposed countries."
    )
    story_insight(
        "The scenario converts insight into action",
        "The ranking shows where early-warning monitoring should focus under an illustrative AUS/NZ producer-price shock.",
        "Assumptions are adjustable so the ranking can be stress-tested, not treated as a single-point forecast.",
    )

    shock_pct = float(controls["shock_pct"])
    basket_share = float(controls["basket_share"])
    transmission_coeff = float(controls["transmission_coeff"])
    pass_through_rate = float(controls["pass_through_rate"])
    scenario, effective_global_pressure_pct = build_scenario(
        exposure,
        shock_pct,
        pass_through_rate,
        basket_share,
        transmission_coeff,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Producer shock", f"+{shock_pct}%")
    c2.metric("Basket share", f"{basket_share:.0%}")
    c3.metric("Transmission x pass-through", f"{transmission_coeff:.0%} x {pass_through_rate:.0%}")
    c4.metric("Effective global pressure", f"{effective_global_pressure_pct:.2f}%")

    st.subheader("Scenario Priority Ranking")
    top = scenario.nlargest(12, "scenario_pressure_score")
    max_scenario, _ = build_scenario(exposure, 60, 1.0, 1.0, 1.0)
    max_scenario_score = max(max_scenario["scenario_pressure_score"].max(), 0.01)
    fig = px.bar(
        top,
        x="scenario_pressure_score",
        y="country_ghi",
        orientation="h",
        color="scenario_pressure_score",
        color_continuous_scale=RISK_SCALE,
        range_color=[0, max_scenario_score],
        hover_data={
            "hunger_metric": ":.1f",
            "food_import_pct": ":.1f",
            "vulnerability_score": ":.2f",
            "implied_import_cost_pressure_pct": ":.2f",
            "scenario_pressure_score": ":.2f",
        },
        labels={"country_ghi": "", "scenario_pressure_score": "Scenario pressure score"},
        title=f"Priority Countries under +{shock_pct}% Producer Shock",
        template=CHART_TEMPLATE,
    )
    apply_chart_style(fig, height=560)
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(range=[0, max_scenario_score * 1.08])
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recommended Policy Use")
    st.dataframe(priority_table(scenario, 10), width="stretch", hide_index=True)

    st.subheader("Robustness Check")
    st.caption("Tests whether priority countries remain high-risk when food-access and import-dependency weights change.")
    sensitivity = build_weight_sensitivity(data["ghi"], data["worldbank"])
    if not sensitivity.empty:
        c1, c2 = st.columns([0.46, 0.54])
        with c1:
            st.dataframe(
                sensitivity.head(10).round({"average_rank": 1, "average_exposure": 1}).rename(
                    columns={
                        "country": "Country",
                        "appearances": "Top-10 appearances",
                        "best_rank": "Best rank",
                        "average_rank": "Average rank",
                        "average_exposure": "Average exposure",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
        with c2:
            stability_plot = sensitivity.head(10).sort_values(
                ["appearances", "average_exposure"],
                ascending=[False, False],
            )
            fig_stability = px.bar(
                stability_plot,
                x="appearances",
                y="country",
                orientation="h",
                color="average_exposure",
                color_continuous_scale=RISK_SCALE,
                labels={
                    "appearances": "Top-10 appearances across tested weights",
                    "country": "",
                    "average_exposure": "Average exposure",
                },
                title="Priority Robustness across Food-Access Weights 0.40-0.80",
                template=CHART_TEMPLATE,
            )
            apply_chart_style(fig_stability, height=390)
            fig_stability.update_yaxes(
                categoryorder="array",
                categoryarray=stability_plot["country"].tolist()[::-1],
            )
            st.plotly_chart(fig_stability, use_container_width=True)

    with st.expander("Scenario assumptions and boundaries", expanded=False):
        st.markdown(
            f"""
            **Formula**

            `effective_global_pressure = producer_shock x basket_share x transmission_coeff x pass_through_rate`

            **Current assumptions**

            - Relevant import basket share: `{basket_share:.2f}`
            - Transmission coefficient: `{transmission_coeff:.2f}`
            - Pass-through rate: `{pass_through_rate:.2f}` from the slider

            This remains an illustrative prioritisation model. It does not include bilateral trade flows,
            exchange rates, freight costs, tariffs, subsidies, trade margins, or supplier substitution.
            """
        )
