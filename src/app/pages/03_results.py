"""Race Results — Heatmap matrix of finishing positions across races."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from db import load_race_results
from theme import F1_TEMPLATE, TEXT, TEXT_DIM

season = st.session_state.get("season")
if not season:
    st.warning("Select a season from the sidebar.")
    st.stop()

st.title(f"🏁 Race Results — {season}")

results = load_race_results(season)

if results.empty:
    st.info("No results for this season yet.")
    st.stop()

# -- Build the heatmap matrix ------------------------------------------------

races = results.sort_values("round")[["race_name", "round"]].drop_duplicates()
race_names = races["race_name"].tolist()

drivers = (
    results.groupby("driver_name")
    .agg(points=("points", "sum"))
    .sort_values("points", ascending=False)
    .index.tolist()
)

matrix = np.full((len(drivers), len(race_names)), np.nan)
custom = np.empty((len(drivers), len(race_names)), dtype=object)

for _, row in results.iterrows():
    d_idx = drivers.index(row["driver_name"]) if row["driver_name"] in drivers else -1
    r_idx = race_names.index(row["race_name"]) if row["race_name"] in race_names else -1
    if d_idx >= 0 and r_idx >= 0:
        pos = row["finish_position"]
        matrix[d_idx][r_idx] = pos if pos is not None else np.nan
        custom[d_idx][r_idx] = (
            f"<b>{row['driver_name']}</b><br>"
            f"{row['race_name']}<br>"
            f"Grid: {row['grid_position']} → Finish: {row.get('finish_position', 'DNF')}<br>"
            f"Points: {row['points']:.0f}<br>"
            f"Status: {row.get('status_category', 'N/A')}"
        )

colorscale = [
    [0.0, "#FFD700"],   # P1 gold
    [0.03, "#FFD700"],
    [0.03, "#2E7D32"],  # P2-P3 green
    [0.1, "#2E7D32"],
    [0.1, "#1A3A1A"],   # P4-P10 dark green
    [0.3, "#1A3A1A"],
    [0.3, "#3A1111"],   # P11+ dark red
    [1.0, "#3A1111"],
]

# Text annotations
text_matrix = []
for i in range(len(drivers)):
    row_text = []
    for j in range(len(race_names)):
        v = matrix[i][j]
        if np.isnan(v):
            row_text.append("DNF")
        else:
            row_text.append(str(int(v)))
    text_matrix.append(row_text)

fig = go.Figure(data=go.Heatmap(
    z=matrix,
    x=race_names,
    y=drivers,
    text=text_matrix,
    texttemplate="%{text}",
    textfont=dict(size=11, color=TEXT),
    colorscale=colorscale,
    showscale=False,
    hovertext=custom,
    hoverinfo="text",
    xgap=2,
    ygap=2,
))

fig.update_layout(
    template=F1_TEMPLATE,
    height=max(500, len(drivers) * 30),
    xaxis=dict(side="top", tickangle=45, title=""),
    yaxis=dict(autorange="reversed", title=""),
    margin=dict(l=10, r=10, t=60, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# -- Legend -------------------------------------------------------------------
st.markdown(
    f"""
    <div style="display:flex;gap:16px;font-size:0.85em;color:{TEXT_DIM};margin-top:-10px;">
        <span>🥇 P1</span>
        <span style="color:#2E7D32">■</span><span>Podium (P2-P3)</span>
        <span style="color:#1A3A1A">■</span><span>Points (P4-P10)</span>
        <span style="color:#3A1111">■</span><span>Outside points</span>
        <span style="color:#2A2A3A">■</span><span>DNF / DNS</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -- Race Summary Table ------------------------------------------------------

st.markdown("---")
st.header("Race-by-Race Summary")

summary = (
    results.groupby(["race_name", "round"])
    .agg(
        winner=("driver_name", "first"),
        total_finishers=("finish_position", "count"),
        total_dnfs=("is_dnf", "sum"),
    )
    .sort_values("round")
    .reset_index()
)
summary.columns = ["Race", "Round", "Winner", "Finishers", "DNFs"]
st.dataframe(summary, use_container_width=True, hide_index=True)
