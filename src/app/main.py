"""F1 Analytics Streamlit App - Entry Point.

Run with:
    streamlit run src/app/main.py
"""

import streamlit as st

from db import load_seasons
from theme import F1_CSS

st.set_page_config(
    page_title="F1 Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(F1_CSS, unsafe_allow_html=True)

# -- Sidebar -----------------------------------------------------------------

with st.sidebar:
    st.markdown("# 🏎️ F1 Analytics")
    st.markdown("---")

    seasons = load_seasons()
    selected_season = st.selectbox("Season", seasons[::-1], index=0)
    st.session_state["season"] = selected_season

    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Data: Ergast / Jolpica F1 APIs")
    st.caption("Pipeline: Airflow → dbt → PostgreSQL")

# -- Home Page ---------------------------------------------------------------

st.title("🏎️ F1 Analytics Dashboard")
st.markdown(f"### Season {st.session_state['season']}")

st.markdown(
    """
    Navigate to a page using the sidebar on the left.

    **Available pages:**
    - **Standings** — Current season points tally for drivers and constructors
    - **Progression** — How the championship evolves race by race
    - **Results** — Race-by-race finishing positions matrix
    - **Qualifying** — Qualifying vs race performance analysis
    - **Head-to-Head** — Teammate comparison within a team
    """
)
