from unittest.mock import patch

import ingest_jolpica


def _page(items, total, offset):
    return {
        "MRData": {
            "total": str(total),
            "limit": str(len(items)),
            "offset": str(offset),
            "DriverTable": {"Drivers": items},
        }
    }


def test_fetch_paginated_merges_all_pages():
    pages = [
        _page([{"driverId": "a"}, {"driverId": "b"}], 4, 0),
        _page([{"driverId": "c"}, {"driverId": "d"}], 4, 2),
    ]
    calls = {"n": 0}

    def mock_req(url):
        i = calls["n"]
        calls["n"] += 1
        return pages[i]

    with patch("ingest_jolpica.req", side_effect=mock_req):
        data = ingest_jolpica.fetch_paginated(
            "https://api.jolpi.ca/ergast/f1/2026/drivers.json"
        )

    drivers = data["MRData"]["DriverTable"]["Drivers"]
    assert [d["driverId"] for d in drivers] == ["a", "b", "c", "d"]
    assert calls["n"] == 2
    assert data["MRData"]["limit"] == "4"


def test_fetch_paginated_single_page():
    with patch(
        "ingest_jolpica.req",
        return_value=_page([{"driverId": "a"}], 1, 0),
    ):
        data = ingest_jolpica.fetch_paginated(
            "https://api.jolpi.ca/ergast/f1/2026/circuits.json"
        )

    assert len(data["MRData"]["DriverTable"]["Drivers"]) == 1
