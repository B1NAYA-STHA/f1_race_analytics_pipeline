import json
from unittest.mock import patch

import ingest_jolpica


def test_compute_rounds_to_fetch_missing_empty_and_latest():
    races_list = [
        {"round": "1", "date": "2026-03-08"},
        {"round": "2", "date": "2026-03-22"},
        {"round": "3", "date": "2026-04-05"},
        {"round": "4", "date": "2026-09-01"},
    ]
    existing = {
        "1": {"round": "1", "Results": [{"driverId": "a"}]},
        "3": {"round": "3", "Results": []},
        "4": {"round": "4", "Results": []},
    }
    result = ingest_jolpica.compute_rounds_to_fetch(races_list, existing, "results")
    assert result == {"1", "2", "3"}


def test_compute_rounds_to_fetch_skips_non_sprint_rounds():
    races_list = [
        {"round": "1", "date": "2026-03-08"},
        {"round": "2", "date": "2026-03-22", "Sprint": {}},
        {"round": "3", "date": "2026-04-05"},
    ]
    existing = {"2": {"round": "2", "SprintResults": [{"driverId": "a"}]}}
    result = ingest_jolpica.compute_rounds_to_fetch(races_list, existing, "sprint")
    assert result == {"2"}


def test_update_round_endpoint_merges_new_rounds_and_refreshes_latest(tmp_path):
    jolpica_dir = tmp_path / "jolpica"
    year_dir = jolpica_dir / "2026"
    year_dir.mkdir(parents=True)

    existing = [
        {"season": "2026", "round": "1", "Results": [{"position": "1"}]},
        {"season": "2026", "round": "2", "Results": []},
        {"season": "2026", "round": "3", "Results": []},
    ]
    (year_dir / "results.json").write_text(
        json.dumps(
            {
                "MRData": {
                    "total": "1",
                    "RaceTable": {"season": "2026", "Races": existing},
                }
            }
        )
    )

    races_list = [
        {"round": "1", "date": "2026-03-08"},
        {"round": "2", "date": "2026-03-22"},
        {"round": "3", "date": "2026-09-15"},
    ]

    def mock_fetch_round_data(year, rn, endpoint):
        if rn == "1":
            return [{"position": "1", "driverId": "refreshed"}]
        if rn == "2":
            return [{"position": "1", "driverId": "new"}]
        return []

    with (
        patch("ingest_jolpica.JOLPICA_DIR", new=jolpica_dir),
        patch("ingest_jolpica.fetch_round_data", side_effect=mock_fetch_round_data),
    ):
        ingest_jolpica.update_round_endpoint(2026, "results", races_list)

    payload = json.loads((year_dir / "results.json").read_text())
    rounds = {r["round"]: r for r in payload["MRData"]["RaceTable"]["Races"]}
    assert set(rounds) == {"1", "2", "3"}
    assert rounds["1"]["Results"] == [{"position": "1", "driverId": "refreshed"}]
    assert rounds["2"]["Results"] == [{"position": "1", "driverId": "new"}]
    assert rounds["3"]["Results"] == []
    assert payload["MRData"]["total"] == "2"


def test_update_round_endpoint_creates_file_from_scratch(tmp_path):
    jolpica_dir = tmp_path / "jolpica"
    year_dir = jolpica_dir / "2026"
    year_dir.mkdir(parents=True)

    races_list = [
        {"round": "1", "date": "2026-03-08"},
        {"round": "2", "date": "2026-03-22"},
        {"round": "3", "date": "2026-09-15"},
    ]

    def mock_fetch_round_data(year, rn, endpoint):
        return [{"driverId": rn}]

    with (
        patch("ingest_jolpica.JOLPICA_DIR", new=jolpica_dir),
        patch("ingest_jolpica.fetch_round_data", side_effect=mock_fetch_round_data),
    ):
        ingest_jolpica.update_round_endpoint(2026, "results", races_list)

    payload = json.loads((year_dir / "results.json").read_text())
    rounds = payload["MRData"]["RaceTable"]["Races"]
    assert [r["round"] for r in rounds] == ["1", "2"]
    assert payload["MRData"]["total"] == "2"
