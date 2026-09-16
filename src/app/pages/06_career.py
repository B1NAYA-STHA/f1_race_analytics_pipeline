"""All-time driver and constructor career leaderboards."""

import plotly.express as px
import streamlit as st

from db import load_constructor_career, load_driver_career
from theme import F1_TEMPLATE, TEAM_COLORS

st.title("🏅 All-Time Career")
st.caption("Career totals across every season in the warehouse.")

metric_options = {
    "Wins": "wins",
    "Podiums": "podiums",
    "Poles": "poles",
    "Fastest Laps": "fastest_laps",
    "Points": "total_points",
    "Championships": "championships_won",
    "DNFs": "dnfs",
}
metric_label = st.radio("Rank by", list(metric_options), horizontal=True, key="career_metric")
metric = metric_options[metric_label]

drivers_tab, constructors_tab = st.tabs(["Drivers", "Constructors"])

with drivers_tab:
    drivers = load_driver_career().sort_values(metric, ascending=False).head(15)
    fig = px.bar(
        drivers.sort_values(metric),
        x=metric,
        y="driver_name",
        orientation="h",
        text=metric,
        labels={metric: metric_label, "driver_name": ""},
    )
    fig.update_traces(marker_color="#E10600", textposition="outside")
    fig.update_layout(template=F1_TEMPLATE, height=560, margin=dict(l=0, r=40, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        load_driver_career().rename(columns={
            "driver_name": "Driver",
            "first_season": "First Season",
            "last_season": "Last Season",
            "races_entered": "Races",
            "total_points": "Points",
            "championships_won": "Championships",
        }),
        use_container_width=True,
        hide_index=True,
    )

with constructors_tab:
    constructors = load_constructor_career().sort_values(metric, ascending=False).head(15)
    fig = px.bar(
        constructors.sort_values(metric),
        x=metric,
        y="constructor_name",
        orientation="h",
        text=metric,
        labels={metric: metric_label, "constructor_name": ""},
    )
    fig.update_traces(
        marker_color=[TEAM_COLORS.get(name, "#E10600") for name in constructors["constructor_name"]],
        textposition="outside",
    )
    fig.update_layout(template=F1_TEMPLATE, height=560, margin=dict(l=0, r=40, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        load_constructor_career().rename(columns={
            "constructor_name": "Constructor",
            "first_season": "First Season",
            "last_season": "Last Season",
            "races_entered": "Races",
            "total_points": "Points",
            "championships_won": "Championships",
        }),
        use_container_width=True,
        hide_index=True,
    )