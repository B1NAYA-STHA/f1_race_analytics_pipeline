"""F1 branded colors, Plotly template, and CSS for the Streamlit app."""

import plotly.graph_objects as go

# -- F1 Colors ---------------------------------------------------------------

BG = "#15151E"
SIDEBAR_BG = "#0D0D14"
CARD_BG = "#1E1E2E"
TEXT = "#FFFFFF"
TEXT_DIM = "#A0A0B0"
GRID = "#2A2A3A"
F1_RED = "#E10600"

TEAM_COLORS = {
    "McLaren": "#FF8000",
    "Ferrari": "#DC143C",
    "Mercedes": "#27F4D2",
    "Red Bull": "#3671C6",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Visa Cash App RB": "#6692FF",
    "Haas F1 Team": "#B6BABD",
    "Haas": "#B6BABD",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Stake F1 Team Kick Sauber": "#52E252",
    "Alfa Romeo": "#52E252",
}

POSITION_COLORS = {
    1: "#FFD700",  # gold
    2: "#C0C0C0",  # silver
    3: "#CD7F32",  # bronze
}


def team_color(name: str) -> str:
    return TEAM_COLORS.get(name, "#888888")


def position_bg(pos) -> str:
    if pos is None:
        return "#3A1111"
    try:
        p = int(pos)
    except (ValueError, TypeError):
        return "#3A1111"
    if p == 1:
        return "#2E7D32"
    if p <= 3:
        return "#1B5E20"
    if p <= 10:
        return "#1A3A1A"
    return "#3A1111"


# -- Plotly Template ---------------------------------------------------------

F1_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        title=dict(font=dict(color=TEXT, size=20)),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        colorway=list(TEAM_COLORS.values()),
    )
)

# -- Streamlit CSS -----------------------------------------------------------

F1_CSS = """
<style>
    /* General */
    .stApp { background-color: #15151E; }
    section[data-testid="stSidebar"] { background-color: #0D0D14; }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #FFFFFF; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #1E1E2E;
        border: 1px solid #2A2A3A;
        border-radius: 8px;
        padding: 12px 16px;
    }
    div[data-testid="stMetric"] label { color: #A0A0B0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #FFFFFF !important; }

    /* Tables */
    .dataframe { background-color: #1E1E2E !important; }
    .dataframe th { background-color: #2A2A3A !important; color: #FFFFFF !important; }
    .dataframe td { color: #FFFFFF !important; }

    /* Headings */
    h1 { color: #FFFFFF !important; }
    h2 { color: #FFFFFF !important; }
    h3 { color: #A0A0B0 !important; }

    /* Divider */
    hr { border-color: #2A2A3A; }
</style>
"""
