from unittest.mock import patch

import ingest_jolpica


PAGE_1_LAP_1 = {
    "number": "1",
    "Timings": [
        {"driverId": "hamilton", "position": "1"},
        {"driverId": "verstappen", "position": "2"},
    ],
}

PAGE_2_LAP_1 = {
    "number": "1",
    "Timings": [
        {"driverId": "leclerc", "position": "3"},
        {"driverId": "norris", "position": "4"},
    ],
}

PAGE_3_LAP_2 = {
    "number": "2",
    "Timings": [
        {"driverId": "hamilton", "position": "1"},
        {"driverId": "verstappen", "position": "2"},
    ],
}


def _make_page(laps, total):
    return {
        "MRData": {
            "total": str(total),
            "RaceTable": {"Races": [{"Laps": laps}]},
        }
    }


def mock_req(url):
    if "offset=0" in url:
        return _make_page([PAGE_1_LAP_1], total=6)
    if "offset=2" in url:
        return _make_page([PAGE_2_LAP_1], total=6)
    if "offset=4" in url:
        return _make_page([PAGE_3_LAP_2], total=6)
    return _make_page([], total=0)


@patch("ingest_jolpica.PAGE_LIMIT", 2)
def test_lap_merge_combines_timings_across_pages():
    with patch("ingest_jolpica.req", side_effect=mock_req):
        result = ingest_jolpica.fetch_round_data(2025, "1", "laps")

    assert len(result) == 2

    lap1 = next(lap for lap in result if lap["number"] == "1")
    assert len(lap1["Timings"]) == 4
    assert lap1["Timings"] == [
        {"driverId": "hamilton", "position": "1"},
        {"driverId": "verstappen", "position": "2"},
        {"driverId": "leclerc", "position": "3"},
        {"driverId": "norris", "position": "4"},
    ]

    lap2 = next(lap for lap in result if lap["number"] == "2")
    assert len(lap2["Timings"]) == 2


@patch("ingest_jolpica.PAGE_LIMIT", 2)
def test_lap_merge_returns_sorted_by_lap_number():
    with patch("ingest_jolpica.req", side_effect=mock_req):
        result = ingest_jolpica.fetch_round_data(2025, "1", "laps")

    assert [lap["number"] for lap in result] == ["1", "2"]


def test_lap_merge_empty_round():
    def mock_empty(url):
        return {"MRData": {"total": "0", "RaceTable": {"Races": [{"Laps": []}]}}}

    with patch("ingest_jolpica.req", side_effect=mock_empty):
        result = ingest_jolpica.fetch_round_data(2025, "99", "laps")

    assert result == []
