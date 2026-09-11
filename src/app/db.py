"""PostgreSQL connection and cached data loaders for the Streamlit app."""

import os
from functools import lru_cache

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'postgres_password')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'f1_warehouse')}"
)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(_DB_URL)


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ---------------------------------------------------------------------------
# Cached loaders (TTL = 1 hour, refreshed manually via sidebar button)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_seasons() -> list[int]:
    df = query("SELECT DISTINCT season FROM marts.championship_standings ORDER BY season")
    return sorted(df["season"].tolist())


@st.cache_data(ttl=3600)
def load_championship_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.championship_standings WHERE season = :season ORDER BY round, championship_position",
        {"season": season},
    )


@st.cache_data(ttl=3600)
def load_driver_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.driver_season_summary WHERE season = :season ORDER BY championship_position",
        {"season": season},
    )


@st.cache_data(ttl=3600)
def load_constructor_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.constructor_season_summary WHERE season = :season ORDER BY championship_position",
        {"season": season},
    )


@st.cache_data(ttl=3600)
def load_race_results(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.race_results_detail WHERE season = :season ORDER BY round, finish_position",
        {"season": season},
    )


@st.cache_data(ttl=3600)
def load_qualifying(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.qualifying_vs_race WHERE season = :season ORDER BY round, finish_position",
        {"season": season},
    )


@st.cache_data(ttl=3600)
def load_drivers() -> pd.DataFrame:
    return query(
        "SELECT DISTINCT driver_name, driver_code, driver_nationality "
        "FROM marts.race_results_detail ORDER BY driver_name"
    )


@st.cache_data(ttl=3600)
def load_constructors(season: int | None = None) -> pd.DataFrame:
    if season:
        return query(
            "SELECT DISTINCT constructor_name FROM marts.race_results_detail "
            "WHERE season = :season ORDER BY constructor_name",
            {"season": season},
        )
    return query(
        "SELECT DISTINCT constructor_name FROM marts.race_results_detail ORDER BY constructor_name"
    )


@st.cache_data(ttl=3600)
def load_all_results() -> pd.DataFrame:
    return query("SELECT * FROM marts.race_results_detail ORDER BY season DESC, round")
