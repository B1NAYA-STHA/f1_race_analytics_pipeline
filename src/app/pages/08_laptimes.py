"""Race-level lap pace analysis."""

import plotly.express as px
import streamlit as st

from db import load_lap_analysis, load_lap_races
from theme import F1_TEMPLATE, team_color

season = st.session_state.get("season")
st.title(f"⏱️ Lap Time Analysis — {season}")
races = load_lap_races(season)
if races.empty:
    st.info("No lap-time data is available for this season yet.")
    st.stop()

race_label = st.selectbox(
    "Race",
    races.apply(lambda row: f"Round {row['round']}: {row['race_name']}", axis=1),
)
race = races.iloc[races.apply(lambda row: f"Round {row['round']}: {row['race_name']}", axis=1).tolist().index(race_label)]
laps = load_lap_analysis(race["race_id"])

best_lap = laps["lap_ms"].min()
best_driver = laps.loc[laps["lap_ms"].idxmin(), "driver_name"]
cards = st.columns(3)
cards[0].metric("Fastest recorded lap", f"{best_lap / 1000:.3f}s")
cards[1].metric("Driver", best_driver)
cards[2].metric("Average lap", f"{laps['lap_ms'].mean() / 1000:.3f}s")

drivers = laps.groupby("driver_name")["lap_number"].count().nlargest(6).index.tolist()
selected_drivers = st.multiselect("Drivers", drivers, default=drivers[:4])
chart_data = laps[laps["driver_name"].isin(selected_drivers)].copy()
chart_data["lap_seconds"] = chart_data["lap_ms"] / 1000
fig = px.line(
    chart_data,
    x="lap_number",
    y="lap_seconds",
    color="driver_name",
    markers=False,
    hover_data=["constructor_name", "lap_position"],
    labels={"lap_number": "Lap", "lap_seconds": "Lap time (s)", "driver_name": "Driver"},
    color_discrete_map={driver: team_color(chart_data.loc[chart_data["driver_name"] == driver, "constructor_name"].iloc[0]) for driver in selected_drivers},
)
fig.update_layout(template=F1_TEMPLATE, height=520)
st.plotly_chart(fig, use_container_width=True)

pace = (
    laps.groupby(["driver_name", "constructor_name"], as_index=False)
    .agg(delta_to_race_best_ms=("delta_to_race_best_ms", "mean"), laps=("lap_number", "count"))
    .sort_values("delta_to_race_best_ms")
)
st.subheader("Average delta to race-best pace")
st.dataframe(pace.rename(columns={
    "driver_name": "Driver",
    "constructor_name": "Team",
    "delta_to_race_best_ms": "Average delta (ms)",
    "laps": "Laps",
}), use_container_width=True, hide_index=True)