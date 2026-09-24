"""PostgreSQL connection and cached data loaders for the Streamlit app."""

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

_DB_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres_password"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "f1_warehouse"),
    query={"sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")},
)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(_DB_URL)


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    normalized_params = {
        key: value.item() if hasattr(value, "item") else value
        for key, value in (params or {}).items()
    }
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=normalized_params)


# ---------------------------------------------------------------------------
# Cached loaders (TTL = 15 minutes, refreshed manually via sidebar button)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def load_seasons() -> list[int]:
    df = query("SELECT DISTINCT season FROM marts.championship_standings ORDER BY season")
    return sorted(df["season"].tolist())


@st.cache_data(ttl=900)
def load_championship_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.championship_standings WHERE season = :season ORDER BY round, championship_position",
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_driver_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.driver_season_summary WHERE season = :season ORDER BY championship_position",
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_constructor_standings(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.constructor_season_summary WHERE season = :season ORDER BY championship_position",
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_race_results(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.race_results_detail WHERE season = :season ORDER BY round, finish_position",
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_qualifying(season: int) -> pd.DataFrame:
    return query(
        "SELECT * FROM marts.qualifying_vs_race WHERE season = :season ORDER BY round, finish_position",
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_season_race_summary(season: int) -> pd.DataFrame:
    return query(
        """
        SELECT
            race_id,
            round,
            race_name,
            race_date,
            MAX(driver_name) FILTER (WHERE is_win) AS winner,
            MAX(constructor_name) FILTER (WHERE is_win) AS winning_team,
            COUNT(DISTINCT driver_id) AS classified_drivers,
            COUNT(*) FILTER (WHERE is_dnf) AS dnfs
        FROM marts.race_results_detail
        WHERE season = :season
        GROUP BY race_id, round, race_name, race_date
        ORDER BY round
        """,
        {"season": season},
    )


@st.cache_data(ttl=900)
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


@st.cache_data(ttl=900)
def load_driver_career() -> pd.DataFrame:
    return query("SELECT * FROM marts.driver_career ORDER BY total_points DESC")


@st.cache_data(ttl=900)
def load_constructor_career() -> pd.DataFrame:
    return query("SELECT * FROM marts.constructor_career ORDER BY total_points DESC")


@st.cache_data(ttl=900)
def load_circuit_stats() -> pd.DataFrame:
    return query("SELECT * FROM marts.circuit_stats ORDER BY races_hosted DESC, circuit_name")


@st.cache_data(ttl=900)
def load_lap_races(season: int) -> pd.DataFrame:
    return query(
        """
        SELECT DISTINCT race_id, round, race_name, circuit_name, race_date
        FROM marts.lap_time_analysis
        WHERE season = :season
        ORDER BY round
        """,
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_lap_analysis(race_id: int | str) -> pd.DataFrame:
    return query(
        """
        SELECT *
        FROM marts.lap_time_analysis
        WHERE race_id = :race_id
        ORDER BY lap_number, driver_name
        """,
        {"race_id": race_id},
    )


@st.cache_data(ttl=900)
def load_pit_races(season: int) -> pd.DataFrame:
    return query(
        """
        SELECT DISTINCT race_id, round, race_name, circuit_name, race_date
        FROM marts.pit_stop_analysis
        WHERE season = :season
        ORDER BY round
        """,
        {"season": season},
    )


@st.cache_data(ttl=900)
def load_pit_analysis(race_id: int | str) -> pd.DataFrame:
    return query(
        """
        SELECT *
        FROM marts.pit_stop_analysis
        WHERE race_id = :race_id
        ORDER BY stop_number, constructor_name, driver_name
        """,
        {"race_id": race_id},
    )
