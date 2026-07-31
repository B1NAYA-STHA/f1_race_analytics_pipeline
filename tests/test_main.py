from pathlib import Path
from unittest.mock import patch

import ingest_main


def test_is_year_complete_returns_false_for_missing_dir():
    with patch("ingest_main.JOLPICA_DIR", new=Path("/nonexistent")):
        assert ingest_main.is_year_complete(2025) is False


def test_is_year_complete_returns_false_for_partial_year(tmp_path):
    jolpica_dir = tmp_path / "jolpica"
    year_dir = jolpica_dir / "2025"
    year_dir.mkdir(parents=True)
    (year_dir / "races.json").write_text("{}")

    with patch("ingest_main.JOLPICA_DIR", new=jolpica_dir):
        assert ingest_main.is_year_complete(2025) is False


def test_is_year_complete_returns_true_when_all_files_present(tmp_path):
    jolpica_dir = tmp_path / "jolpica"
    year_dir = jolpica_dir / "2025"
    year_dir.mkdir(parents=True)
    for fname in ingest_main.YEAR_FILES:
        (year_dir / fname).write_text("{}")

    with patch("ingest_main.JOLPICA_DIR", new=jolpica_dir):
        assert ingest_main.is_year_complete(2025) is True


def _write_all_historical(tmp_path):
    for table in ingest_main.HISTORICAL_TABLES:
        (tmp_path / f"{table}.csv").write_text("a,b,c")


def test_is_historical_complete_returns_true_with_csvs(tmp_path):
    _write_all_historical(tmp_path)

    with patch("ingest_main.RAW_DIR", new=tmp_path):
        assert ingest_main.is_historical_complete() is True


def test_is_historical_complete_returns_false_without_csvs(tmp_path):
    with patch("ingest_main.RAW_DIR", new=tmp_path):
        assert ingest_main.is_historical_complete() is False


def test_is_historical_complete_returns_false_for_partial_csvs(tmp_path):
    (tmp_path / "drivers.csv").write_text("a,b,c")
    (tmp_path / "races.csv").write_text("a,b,c")

    with patch("ingest_main.RAW_DIR", new=tmp_path):
        assert ingest_main.is_historical_complete() is False


def test_is_historical_complete_ignores_empty_files(tmp_path):
    _write_all_historical(tmp_path)
    (tmp_path / "results.csv").write_text("")

    with patch("ingest_main.RAW_DIR", new=tmp_path):
        assert ingest_main.is_historical_complete() is False
