"""Championship Progression — How the title race evolves race by race."""

import plotly.graph_objects as go
import streamlit as st

from db import load_championship_standings
from theme import F1_TEMPLATE, team_color

season = st.session_state.get("season")
if not season:
    st.warning("Select a season from the sidebar.")
    st.stop()

st.title(f"📈 Championship Progression — {season}")

standings = load_championship_standings(season)

if standings.empty:
    st.info("No data for this season yet.")
    st.stop()

# -- Driver Championship Progression -----------------------------------------

st.header("Drivers' Championship")

all_drivers = standings["driver_name"].unique().tolist()
top_drivers = standings[standings["championship_position"] <= 5]["driver_name"].unique().tolist()

selected_drivers = st.multiselect(
    "Select drivers",
    all_drivers,
    default=top_drivers[:8],
    key="prog_drivers",
)

if selected_drivers:
    fig = go.Figure()
    for driver in selected_drivers:
        d = standings[standings["driver_name"] == driver].sort_values("round")
        team = d["team"].iloc[0] if "team" in d.columns else None
        fig.add_trace(go.Scatter(
            x=d["round"],
            y=d["cumulative_points"],
            mode="lines+markers",
            name=driver,
            line=dict(color=team_color(team) if team else None, width=2),
            marker=dict(size=6),
            hovertemplate=(
                f"<b>{driver}</b><br>"
                "Round %{x}<br>"
                "Points: %{y:.0f}<br>"
                "Position: %{customdata[0]}<br>"
                "Behind leader: %{customdata[1]:.0f} pts"
                "<extra></extra>"
            ),
            customdata=d[["championship_position", "points_behind_leader"]].values,
        ))

    fig.update_layout(
        template=F1_TEMPLATE,
        height=550,
        xaxis=dict(title="Round", dtick=1),
        yaxis=dict(title="Cumulative Points"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=20, t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one driver to see the progression.")

# -- Constructor Championship Progression ------------------------------------

st.header("Constructors' Championship")

# Build constructor standings from race_results_detail via championship_standings
# We need to sum points per team per round
if not standings.empty and "team" in standings.columns:
    con_prog = (
        standings.groupby(["round", "team"], as_index=False)
        .agg(cumulative_points=("cumulative_points", "sum"))
    )

    all_teams = con_prog["team"].unique().tolist()
    default_teams = (
        con_prog.groupby("team")["cumulative_points"]
        .max()
        .nlargest(5)
        .index
        .tolist()
    )
    selected_teams = st.multiselect(
        "Select constructors",
        all_teams,
        default=default_teams,
        key="prog_teams",
    )

    fig_con = go.Figure()
    for team in selected_teams:
        t = con_prog[con_prog["team"] == team].sort_values("round")
        fig_con.add_trace(go.Scatter(
            x=t["round"],
            y=t["cumulative_points"],
            mode="lines+markers",
            name=team,
            line=dict(color=team_color(team), width=2),
            marker=dict(size=5),
        ))

    fig_con.update_layout(
        template=F1_TEMPLATE,
        height=450,
        xaxis=dict(title="Round", dtick=1),
        yaxis=dict(title="Cumulative Points"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=20, t=30, b=10),
    )
    st.plotly_chart(fig_con, use_container_width=True)
