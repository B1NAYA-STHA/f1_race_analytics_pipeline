"""Season overview landing page."""

import streamlit as st

from db import load_constructor_standings, load_driver_standings, load_season_race_summary
from theme import F1_CSS

st.markdown(F1_CSS, unsafe_allow_html=True)

season = st.session_state.get("season")
st.title(f"🏎️ {season} Season Overview")
st.caption("A concise view of the championship, latest race, and season shape.")

drivers = load_driver_standings(season)
constructors = load_constructor_standings(season)
races = load_season_race_summary(season)

if drivers.empty:
    st.info("No data is available for this season yet.")
    st.stop()

leader = drivers.iloc[0]
constructor_leader = constructors.iloc[0] if not constructors.empty else None
latest = races.iloc[-1] if not races.empty else None

metrics = st.columns(5)
metrics[0].metric("Driver leader", leader["driver_name"], f"{leader['points']:.0f} pts")
metrics[1].metric(
    "Constructor leader",
    constructor_leader["constructor_name"] if constructor_leader is not None else "N/A",
)
metrics[2].metric("Races completed", f"{len(races)}")
metrics[3].metric("Latest winner", latest["winner"] if latest is not None else "N/A")
metrics[4].metric("Latest race", latest["race_name"] if latest is not None else "N/A")

st.markdown("---")
left, right = st.columns([1.35, 1])

with left:
    st.subheader("Championship leaders")
    leader_table = drivers.head(10)[
        ["championship_position", "driver_name", "team", "points", "wins", "podiums"]
    ].copy()
    leader_table.columns = ["Pos", "Driver", "Team", "Points", "Wins", "Podiums"]
    st.dataframe(leader_table, use_container_width=True, hide_index=True)

with right:
    st.subheader("Latest race")
    if latest is not None:
        st.markdown(f"### {latest['race_name']}")
        st.metric("Winner", latest["winner"] or "N/A", latest["winning_team"] or "")
        st.write(f"Round {int(latest['round'])} · {latest['race_date']}")
        st.write(f"{int(latest['classified_drivers'])} classified drivers · {int(latest['dnfs'])} DNFs")
    else:
        st.info("No completed race is available yet.")

st.subheader("Season race winners")
if not races.empty:
    display_races = races[["round", "race_name", "winner", "winning_team", "race_date"]].copy()
    display_races.columns = ["Round", "Race", "Winner", "Team", "Date"]
    st.dataframe(display_races, use_container_width=True, hide_index=True)

st.markdown(
    "<div class='f1-note'>Use the Season selector in the sidebar to move through seasons. "
    "Circuit Explorer and Career Records are all-time views.</div>",
    unsafe_allow_html=True,
)