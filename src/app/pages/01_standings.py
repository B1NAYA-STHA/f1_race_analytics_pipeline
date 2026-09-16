"""Standings — Current season points tally for drivers and constructors."""

import plotly.graph_objects as go
import streamlit as st

from db import load_constructor_standings, load_driver_standings
from theme import F1_TEMPLATE, TEXT, team_color

season = st.session_state.get("season")
if not season:
    st.warning("Select a season from the sidebar.")
    st.stop()

st.title(f"🏆 Season {season} Standings")

# -- Driver Standings --------------------------------------------------------

st.header("Drivers' Championship")
drivers = load_driver_standings(season)

if drivers.empty:
    st.info("No data for this season yet.")
    st.stop()

# Metric cards for top 3
top3 = drivers.head(3)
cols = st.columns(3)
for i, (_, row) in enumerate(top3.iterrows()):
    medal = ["🥇", "🥈", "🥉"][i]
    cols[i].metric(
        label=f"{medal} {row['driver_name']}",
        value=f"{row['points']:.0f} pts",
        delta=f"{row['wins']}W / {row['podiums']}P",
    )

st.markdown("")

# Points bar chart
fig_drivers = go.Figure()
for _, row in drivers.iterrows():
    fig_drivers.add_trace(go.Bar(
        y=[row["driver_name"]],
        x=[row["points"]],
        orientation="h",
        marker_color=team_color(row["team"]),
        name=row["team"],
        showlegend=False,
        text=f"{row['points']:.0f} pts",
        textposition="outside",
        textfont=dict(color=TEXT),
    ))

fig_drivers.update_layout(
    template=F1_TEMPLATE,
    height=max(400, len(drivers) * 35),
    xaxis_title="Points",
    yaxis=dict(autorange="reversed", title=""),
    margin=dict(l=0, r=40, t=10, b=10),
    bargap=0.3,
)
st.plotly_chart(fig_drivers, use_container_width=True)

# Standings table
st.markdown("### Full Standings")
display_cols = ["championship_position", "driver_name", "team", "points", "wins", "podiums", "dnfs", "avg_finish_position"]
display_names = {
    "championship_position": "Pos",
    "driver_name": "Driver",
    "team": "Team",
    "points": "Points",
    "wins": "Wins",
    "podiums": "Podiums",
    "dnfs": "DNFs",
    "avg_finish_position": "Avg Finish",
}
table = drivers[display_cols].copy()
table["avg_finish_position"] = table["avg_finish_position"].round(1)
table = table.rename(columns=display_names)
st.dataframe(table, use_container_width=True, hide_index=True)

st.markdown("---")

# -- Constructor Standings ---------------------------------------------------

st.header("Constructors' Championship")
constructors = load_constructor_standings(season)

if not constructors.empty:
    fig_cons = go.Figure()
    for _, row in constructors.iterrows():
        fig_cons.add_trace(go.Bar(
            y=[row["constructor_name"]],
            x=[row["points"]],
            orientation="h",
            marker_color=team_color(row["constructor_name"]),
            showlegend=False,
            text=f"{row['points']:.0f} pts",
            textposition="outside",
            textfont=dict(color=TEXT),
        ))

    fig_cons.update_layout(
        template=F1_TEMPLATE,
        height=max(300, len(constructors) * 45),
        xaxis_title="Points",
        yaxis=dict(autorange="reversed", title=""),
        margin=dict(l=0, r=40, t=10, b=10),
        bargap=0.3,
    )
    st.plotly_chart(fig_cons, use_container_width=True)

    con_display = {
        "championship_position": "Pos",
        "constructor_name": "Team",
        "points": "Points",
        "wins": "Wins",
        "podiums": "Podiums",
        "one_two_finishes": "1-2 Finishes",
        "dnfs": "DNFs",
    }
    ctable = constructors[list(con_display.keys())].rename(columns=con_display)
    st.dataframe(ctable, use_container_width=True, hide_index=True)
