"""Race-level pit-stop analysis."""

import plotly.express as px
import streamlit as st

from db import load_pit_analysis, load_pit_races
from theme import F1_TEMPLATE, team_color

season = st.session_state.get("season")
st.title(f"🔧 Pit Stop Analysis — {season}")
races = load_pit_races(season)
if races.empty:
    st.info("No pit-stop data is available for this season yet.")
    st.stop()

race_labels = races.apply(lambda row: f"Round {row['round']}: {row['race_name']}", axis=1).tolist()
race_label = st.selectbox("Race", race_labels)
race = races.iloc[race_labels.index(race_label)]
stops = load_pit_analysis(race["race_id"])

cards = st.columns(4)
cards[0].metric("Total stops", f"{len(stops):,}")
cards[1].metric("Average stop", f"{stops['stop_ms'].mean() / 1000:.3f}s")
cards[2].metric("Fastest stop", f"{stops['stop_ms'].min() / 1000:.3f}s")
cards[3].metric("Slowest stop", f"{stops['stop_ms'].max() / 1000:.3f}s")

fig = px.box(
    stops,
    x="constructor_name",
    y=stops["stop_ms"] / 1000,
    color="constructor_name",
    points="outliers",
    labels={"y": "Stop duration (s)", "constructor_name": "Team"},
    color_discrete_map={team: team_color(team) for team in stops["constructor_name"].unique()},
)
fig.update_layout(template=F1_TEMPLATE, height=500, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

slow = stops.sort_values("stop_ms", ascending=False).head(20).copy()
slow["duration_seconds"] = slow["stop_ms"] / 1000
st.subheader("Slowest stops")
st.dataframe(
    slow[["driver_name", "constructor_name", "stop_number", "lap_number", "duration_seconds"]]
    .rename(columns={
        "driver_name": "Driver",
        "constructor_name": "Team",
        "stop_number": "Stop",
        "lap_number": "Lap",
        "duration_seconds": "Duration (s)",
    }),
    use_container_width=True,
    hide_index=True,
)