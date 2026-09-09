"""Qualifying Analysis — Qualifying vs race performance."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db import load_qualifying
from theme import F1_TEMPLATE, TEXT_DIM, team_color

st.set_page_config(page_title="Qualifying | F1 Analytics", page_icon="⏱️", layout="wide")

season = st.session_state.get("season")
if not season:
    st.warning("Select a season from the sidebar.")
    st.stop()

st.title(f"⏱️ Qualifying Analysis — {season}")

quali = load_qualifying(season)

if quali.empty:
    st.info("No qualifying data for this season yet.")
    st.stop()

# -- Metric cards ------------------------------------------------------------
total_poles = quali["is_pole"].sum()
pole_wins = quali[quali["is_pole"]]["is_win"].sum()
pole_conv = (pole_wins / total_poles * 100) if total_poles > 0 else 0

c1, c2, c3 = c1, c2, c3 = st.columns(3)
c1.metric("Pole Positions", f"{total_poles}")
c2.metric("Pole to Win", f"{pole_wins}")
c3.metric("Conversion Rate", f"{pole_conv:.0f}%")

st.markdown("---")

# -- Qualifying Position vs Finish Position Scatter --------------------------

st.header("Qualifying vs Race Finish")

fig_scatter = px.scatter(
    quali,
    x="qualifying_position",
    y="finish_position",
    color="constructor_name",
    hover_name="driver_name",
    hover_data={
        "race_name": True,
        "grid_position": True,
        "positions_gained_lost": True,
        "points": ":.0f",
        "constructor_name": False,
        "qualifying_position": True,
        "finish_position": True,
    },
    labels={
        "qualifying_position": "Qualifying Position",
        "finish_position": "Finish Position",
        "constructor_name": "Team",
    },
    color_discrete_map={t: team_color(t) for t in quali["constructor_name"].unique()},
)

# Diagonal reference line (no positions gained/lost)
fig_scatter.add_trace(go.Scatter(
    x=[1, 20],
    y=[1, 20],
    mode="lines",
    line=dict(color="#E10600", dash="dash", width=1),
    name="Equal line",
    showlegend=False,
))

fig_scatter.update_layout(
    template=F1_TEMPLATE,
    height=550,
    xaxis=dict(title="Qualifying Position", autorange="reversed", dtick=1),
    yaxis=dict(title="Finish Position", autorange="reversed", dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=20, t=30, b=10),
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    f"""
    <div style="color:{TEXT_DIM};font-size:0.85em;margin-top:-10px;">
    Points <b>below</b> the red line = gained positions from qualifying.
    Points <b>above</b> = lost positions.
    </div>
    """,
    unsafe_allow_html=True,
)

# -- Positions Gained/Lost Distribution --------------------------------------

st.header("Positions Gained/Lost Distribution")

fig_hist = px.histogram(
    quali,
    x="positions_gained_lost",
    color="constructor_name",
    barmode="group",
    color_discrete_map={t: team_color(t) for t in quali["constructor_name"].unique()},
    labels={"positions_gained_lost": "Positions Gained (+) / Lost (-)", "count": "Count"},
)

fig_hist.update_layout(
    template=F1_TEMPLATE,
    height=400,
    xaxis=dict(dtick=5, title="Positions Gained (+) / Lost (-)"),
    yaxis=dict(title="Count"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=20, t=30, b=10),
    bargap=0.1,
)
st.plotly_chart(fig_hist, use_container_width=True)

# -- Driver Qualifying Performance Table -------------------------------------

st.header("Driver Qualifying Performance")

driver_quali = (
    quali.groupby(["driver_name", "constructor_name"])
    .agg(
        avg_quali=("qualifying_position", "mean"),
        avg_finish=("finish_position", "mean"),
        poles=("is_pole", "sum"),
        top3=("qualifying_position", lambda x: (x <= 3).sum()),
        races=("race_name", "count"),
        avg_positions_gained=("positions_gained_lost", "mean"),
    )
    .reset_index()
)
driver_quali["avg_quali"] = driver_quali["avg_quali"].round(1)
driver_quali["avg_finish"] = driver_quali["avg_finish"].round(1)
driver_quali["avg_positions_gained"] = driver_quali["avg_positions_gained"].round(1)
driver_quali = driver_quali.sort_values("avg_quali")

display = driver_quali.rename(columns={
    "driver_name": "Driver",
    "constructor_name": "Team",
    "avg_quali": "Avg Quali Pos",
    "avg_finish": "Avg Finish",
    "poles": "Poles",
    "top3": "Top 3 Starts",
    "races": "Races",
    "avg_positions_gained": "Avg Pos Δ",
})

st.dataframe(display, use_container_width=True, hide_index=True)
