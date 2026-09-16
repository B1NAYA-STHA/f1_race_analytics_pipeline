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

pages = {
    "Season": [
        st.Page("home.py", title="Overview", icon="🏎️"),
        st.Page("pages/01_standings.py", title="Standings", icon="🏆"),
        st.Page("pages/02_progression.py", title="Progression", icon="📈"),
        st.Page("pages/03_results.py", title="Race Results", icon="🏁"),
        st.Page("pages/04_qualifying.py", title="Qualifying", icon="⏱️"),
        st.Page("pages/05_headtohead.py", title="Head-to-Head", icon="⚔️"),
        st.Page("pages/08_laptimes.py", title="Lap Time", icon="⏱️"),
        st.Page("pages/09_pitstops.py", title="Pit Stops", icon="🔧"),
    ],
    "All-time & Explorer": [
        st.Page("pages/06_career.py", title="Career Records", icon="🏅"),
        st.Page("pages/07_circuits.py", title="Circuit Explorer", icon="🌍"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
