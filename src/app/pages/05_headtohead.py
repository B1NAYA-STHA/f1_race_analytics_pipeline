"""Head-to-Head — Teammate comparison within a team and season."""

import plotly.graph_objects as go
import streamlit as st

from db import load_constructors, load_race_results
from theme import F1_TEMPLATE, TEXT, team_color

st.set_page_config(page_title="Head-to-Head | F1 Analytics", page_icon="⚔️", layout="wide")

season = st.session_state.get("season")
if not season:
    st.warning("Select a season from the sidebar.")
    st.stop()

st.title(f"⚔️ Teammate Head-to-Head — {season}")

results = load_race_results(season)

if results.empty:
    st.info("No data for this season yet.")
    st.stop()

# -- Team selector -----------------------------------------------------------

teams = load_constructors(season)["constructor_name"].tolist()
team = st.selectbox("Select Team", teams, key="h2h_team")

if not team:
    st.stop()

team_results = results[results["constructor_name"] == team].copy()

drivers = team_results["driver_name"].unique().tolist()
if len(drivers) < 2:
    st.info(f"Only one driver found for {team} in {season}.")
    st.stop()

d1, d2 = drivers[0], drivers[1]

# -- Comparison cards --------------------------------------------------------

r1 = team_results[team_results["driver_name"] == d1]
r2 = team_results[team_results["driver_name"] == d2]

stats = {
    "Points": (r1["points"].sum(), r2["points"].sum()),
    "Wins": (r1["is_win"].sum(), r2["is_win"].sum()),
    "Podiums": (r1["is_podium"].sum(), r2["is_podium"].sum()),
    "Poles": (
        (r1["qualifying_position"] == 1).sum() if "qualifying_position" in r1.columns else 0,
        (r2["qualifying_position"] == 1).sum() if "qualifying_position" in r2.columns else 0,
    ),
    "DNFs": (r1["is_dnf"].sum(), r2["is_dnf"].sum()),
    "Avg Finish": (
        r1["finish_position"].dropna().mean() if r1["finish_position"].dropna().any() else 0,
        r2["finish_position"].dropna().mean() if r2["finish_position"].dropna().any() else 0,
    ),
}

st.markdown(f"### {d1} vs {d2} ({team})")

cols = st.columns(2)
with cols[0]:
    st.markdown(f"#### {d1}")
    for label, (v1, _) in stats.items():
        if label == "Avg Finish":
            st.metric(label, f"{v1:.1f}")
        else:
            st.metric(label, f"{int(v1)}")

with cols[1]:
    st.markdown(f"#### {d2}")
    for label, (_, v2) in stats.items():
        if label == "Avg Finish":
            st.metric(label, f"{v2:.1f}")
        else:
            st.metric(label, f"{int(v2)}")

# -- Head-to-head bar comparison ----------------------------------------------

st.markdown("---")
st.header("Head-to-Head Comparison")

labels = list(stats.keys())
v1_vals = [stats[k][0] for k in labels]
v2_vals = [stats[k][1] for k in labels]

fig = go.Figure()
fig.add_trace(go.Bar(
    name=d1, x=labels, y=v1_vals,
    marker_color=team_color(team),
    text=[f"{v:.0f}" if k != "Avg Finish" else f"{v:.1f}" for v, k in zip(v1_vals, labels)],
    textposition="outside",
    textfont=dict(color=TEXT),
))
fig.add_trace(go.Bar(
    name=d2, x=labels, y=v2_vals,
    marker_color="#A0A0B0",
    text=[f"{v:.0f}" if k != "Avg Finish" else f"{v:.1f}" for v, k in zip(v2_vals, labels)],
    textposition="outside",
    textfont=dict(color=TEXT),
))

fig.update_layout(
    template=F1_TEMPLATE,
    barmode="group",
    height=400,
    yaxis=dict(title="Count"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=20, t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# -- Race-by-race finishes ---------------------------------------------------

st.markdown("---")
st.header("Race-by-Race Finishes")

merged = team_results[["race_name", "round", "driver_name", "finish_position", "points"]].copy()
merged = merged.sort_values("round")

fig_races = go.Figure()
for d in [d1, d2]:
    dd = merged[merged["driver_name"] == d].sort_values("round")
    fig_races.add_trace(go.Scatter(
        x=dd["race_name"],
        y=dd["finish_position"],
        mode="lines+markers",
        name=d,
        line=dict(color=team_color(team) if d == d1 else "#A0A0B0", width=2),
        marker=dict(size=8),
        hovertemplate=(
            f"<b>{d}</b><br>"
            "%{x}<br>"
            "Finish: P%{y}<br>"
            "<extra></extra>"
        ),
    ))

fig_races.update_layout(
    template=F1_TEMPLATE,
    height=400,
    xaxis=dict(title="", tickangle=45),
    yaxis=dict(title="Finish Position", autorange="reversed", dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=20, t=30, b=10),
)
st.plotly_chart(fig_races, use_container_width=True)

# -- Detailed race results table ---------------------------------------------

st.markdown("---")
st.header("Detailed Results")

detail_cols = ["race_name", "driver_name", "grid_position", "finish_position", "points", "status_category"]
detail_names = {
    "race_name": "Race",
    "driver_name": "Driver",
    "grid_position": "Grid",
    "finish_position": "Finish",
    "points": "Points",
    "status_category": "Status",
}
detail = team_results.sort_values("round")[detail_cols].rename(columns=detail_names)
st.dataframe(detail, use_container_width=True, hide_index=True)
