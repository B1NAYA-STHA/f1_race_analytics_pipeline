"""Circuit explorer with global circuit locations and historical records."""

import plotly.express as px
import pandas as pd
import streamlit as st

from db import load_circuit_stats
from theme import F1_TEMPLATE

st.title("🌍 Circuit Explorer")
circuits = load_circuit_stats()

if circuits.empty:
    st.info("No circuit data is available yet.")
    st.stop()

map_data = circuits.copy()
map_data["latitude"] = pd.to_numeric(map_data["latitude"], errors="coerce")
map_data["longitude"] = pd.to_numeric(map_data["longitude"], errors="coerce")
map_data = map_data.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

map_fig = px.scatter_geo(
    map_data,
    lat="latitude",
    lon="longitude",
    hover_name="circuit_name",
    hover_data={"circuit_country": True, "races_hosted": True, "latitude": False, "longitude": False},
    size="races_hosted",
    color="last_season",
    projection="natural earth",
    labels={"last_season": "Last season", "circuit_country": "Country", "races_hosted": "Races"},
)
map_fig.update_geos(showland=True, landcolor="#24242e", showcountries=True, countrycolor="#555566")
map_fig.update_layout(template=F1_TEMPLATE, height=560, margin=dict(l=0, r=0, t=10, b=0))

map_event = st.plotly_chart(
    map_fig,
    use_container_width=True,
    key="circuit_map",
    on_select="rerun",
    selection_mode="points",
)

selected_points = map_event.selection.point_indices
if selected_points:
    st.session_state["circuit_selector"] = map_data.iloc[selected_points[0]]["circuit_name"]

selected_name = st.selectbox(
    "Explore a circuit",
    circuits["circuit_name"].tolist(),
    key="circuit_selector",
)
circuit = circuits[circuits["circuit_name"] == selected_name].iloc[0]


def display_value(value) -> str:
    return "N/A" if pd.isna(value) else str(value)

metrics = st.columns(5)
metrics[0].metric("Country", display_value(circuit["circuit_country"]))
metrics[1].metric("Races hosted", int(circuit["races_hosted"]))
metrics[2].metric("Seasons", int(circuit["seasons_hosted"]))
metrics[3].metric("First season", int(circuit["first_season"]))
metrics[4].metric("Last season", int(circuit["last_season"]))

st.subheader(f"{selected_name} records")
records = st.columns(3)
records[0].metric("Most wins", display_value(circuit["most_wins_driver"]))
records[1].metric("Most podiums", display_value(circuit["most_podiums_driver"]))
records[2].metric("Most poles", display_value(circuit["most_poles_driver"]))

st.subheader("Latest race at this circuit")
latest = st.columns(3)
latest[0].metric("Race", display_value(circuit["latest_race_name"]))
latest[1].metric("Season", display_value(circuit["latest_season"]))
latest[2].metric("Winner", display_value(circuit["latest_winner"]))

st.dataframe(
    circuits[["circuit_name", "circuit_country", "races_hosted", "seasons_hosted", "first_season", "last_season"]]
    .rename(columns={
        "circuit_name": "Circuit",
        "circuit_country": "Country",
        "races_hosted": "Races",
        "seasons_hosted": "Seasons",
        "first_season": "First Season",
        "last_season": "Last Season",
    }),
    use_container_width=True,
    hide_index=True,
)