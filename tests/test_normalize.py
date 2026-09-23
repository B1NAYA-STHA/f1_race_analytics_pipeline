import csv
import json

from src.normalize.normalize import normalize
from src.bronze_schemas import SCHEMAS
from src.utils import time_str_to_millis, write_csv


def test_time_str_to_millis():
    cases = {
        "1:38.109": "98109",
        "1:42:06.304": "6126304",
        "13.341": "13341",
        "16:44.718": "1004718",
        "1:00.000": "60000",
        "1:00:00.000": "3600000",
    }
    for value, expected in cases.items():
        assert time_str_to_millis(value) == expected
    assert time_str_to_millis(None) == "NULL"
    assert time_str_to_millis("garbage") == "NULL"


def _write_csv(path, columns, rows):
    write_csv(path, columns, rows)


def _write_json(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


def _make_historical(raw_dir):
    for table, columns in SCHEMAS.items():
        _write_csv(raw_dir / f"{table}.csv", columns, [])
    _write_csv(
        raw_dir / "seasons.csv", SCHEMAS["seasons"], [{"year": "2024", "url": "x"}]
    )
    _write_csv(
        raw_dir / "status.csv",
        SCHEMAS["status"],
        [{"statusId": "1", "status": "Finished"}],
    )
    _write_csv(
        raw_dir / "circuits.csv",
        SCHEMAS["circuits"],
        [{"circuitId": "1", "circuitRef": "monza", "name": "Monza"}],
    )
    _write_csv(
        raw_dir / "drivers.csv",
        SCHEMAS["drivers"],
        [{"driverId": "1", "driverRef": "hamilton", "code": "HAM"}],
    )
    _write_csv(
        raw_dir / "constructors.csv",
        SCHEMAS["constructors"],
        [{"constructorId": "1", "constructorRef": "mercedes", "name": "Mercedes"}],
    )
    _write_csv(
        raw_dir / "races.csv",
        SCHEMAS["races"],
        [
            {
                "raceId": "1",
                "year": "2024",
                "round": "1",
                "circuitId": "1",
                "name": "Test GP",
                "date": "2024-03-10",
                "time": "13:00:00",
            }
        ],
    )
    _write_csv(
        raw_dir / "results.csv",
        SCHEMAS["results"],
        [
            {
                "resultId": "1",
                "raceId": "1",
                "driverId": "1",
                "constructorId": "1",
                "position": "1",
                "positionText": "1",
                "statusId": "1",
            }
        ],
    )
    _write_csv(
        raw_dir / "driver_standings.csv",
        SCHEMAS["driver_standings"],
        [
            {
                "driverStandingsId": "1",
                "raceId": "1",
                "driverId": "1",
                "points": "25",
                "position": "1",
            }
        ],
    )


def _make_jolpica(jolpica_dir):
    jolpica_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        jolpica_dir / "seasons.json",
        {"MRData": {"SeasonTable": {"Seasons": [{"season": "2025", "url": "y"}]}}},
    )
    _write_json(
        jolpica_dir / "status.json",
        {
            "MRData": {
                "StatusTable": {
                    "Status": [
                        {"statusId": "1", "status": "Finished"},
                        {"statusId": "2", "status": "Accident"},
                    ]
                }
            }
        },
    )

    year_dir = jolpica_dir / "2026"
    year_dir.mkdir(parents=True)
    _write_json(
        year_dir / "drivers.json",
        {
            "MRData": {
                "DriverTable": {
                    "Drivers": [
                        {
                            "driverId": "rookie1",
                            "permanentNumber": "88",
                            "code": "ROO",
                            "givenName": "Roo",
                            "familyName": "Kie",
                            "dateOfBirth": "2000-01-01",
                            "nationality": "AU",
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "circuits.json",
        {
            "MRData": {
                "CircuitTable": {
                    "Circuits": [
                        {
                            "circuitId": "madring",
                            "circuitName": "Madring",
                            "Location": {
                                "lat": "40.4",
                                "long": "-3.6",
                                "locality": "Madrid",
                                "country": "Spain",
                            },
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "constructors.json",
        {
            "MRData": {
                "ConstructorTable": {
                    "Constructors": [
                        {
                            "constructorId": "audi",
                            "name": "Audi",
                            "nationality": "German",
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "races.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "raceName": "Spanish Grand Prix",
                            "date": "2026-05-08",
                            "time": "14:00:00Z",
                            "url": "u",
                            "Circuit": {"circuitId": "madring"},
                            "FirstPractice": {
                                "date": "2026-05-08",
                                "time": "09:30:00Z",
                            },
                            "Qualifying": {"date": "2026-05-09", "time": "13:00:00Z"},
                        }
                    ]
                }
            }
        },
    )
    hamilton = {"driverId": "hamilton"}
    mercedes = {"constructorId": "mercedes"}
    rookie1 = {"driverId": "rookie1"}
    audi = {"constructorId": "audi"}
    _write_json(
        year_dir / "results.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "Results": [
                                {
                                    "number": "44",
                                    "position": "1",
                                    "positionText": "1",
                                    "points": "25",
                                    "Driver": hamilton,
                                    "Constructor": mercedes,
                                    "grid": "2",
                                    "laps": "57",
                                    "status": "Finished",
                                    "Time": {
                                        "millis": "6126304",
                                        "time": "1:42:06.304",
                                    },
                                    "FastestLap": {
                                        "rank": "1",
                                        "lap": "43",
                                        "Time": {"time": "1:22.167"},
                                    },
                                },
                                {
                                    "number": "88",
                                    "position": "2",
                                    "positionText": "2",
                                    "points": "18",
                                    "Driver": rookie1,
                                    "Constructor": audi,
                                    "grid": "1",
                                    "laps": "57",
                                    "status": "Finished",
                                    "Time": {
                                        "millis": "6130000",
                                        "time": "1:42:10.000",
                                    },
                                },
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "qualifying.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "QualifyingResults": [
                                {
                                    "number": "88",
                                    "position": "1",
                                    "Driver": rookie1,
                                    "Constructor": audi,
                                    "Q1": "1:19.9",
                                },
                                {
                                    "number": "44",
                                    "position": "2",
                                    "Driver": hamilton,
                                    "Constructor": mercedes,
                                    "Q1": "1:20.1",
                                },
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "sprint.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "SprintResults": [
                                {
                                    "number": "44",
                                    "position": "1",
                                    "positionText": "1",
                                    "points": "8",
                                    "Driver": hamilton,
                                    "Constructor": mercedes,
                                    "grid": "3",
                                    "laps": "15",
                                    "status": "Finished",
                                }
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "pitstops.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "PitStops": [
                                {
                                    "driverId": "hamilton",
                                    "lap": "20",
                                    "stop": "1",
                                    "time": "15:22:58",
                                    "duration": "13.341",
                                },
                                {
                                    "driverId": "rookie1",
                                    "lap": "30",
                                    "stop": "1",
                                    "time": "16:00:00",
                                    "duration": "1:13.341",
                                },
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "laps.json",
        {
            "MRData": {
                "RaceTable": {
                    "Races": [
                        {
                            "season": "2026",
                            "round": "1",
                            "Laps": [
                                {
                                    "number": "1",
                                    "Timings": [
                                        {
                                            "driverId": "hamilton",
                                            "time": "1:38.109",
                                            "position": "1",
                                        },
                                        {
                                            "driverId": "rookie1",
                                            "time": "1:39.000",
                                            "position": "2",
                                        },
                                    ],
                                }
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "driverstandings.json",
        {
            "MRData": {
                "StandingsTable": {
                    "StandingsLists": [
                        {
                            "season": "2026",
                            "round": "1",
                            "DriverStandings": [
                                {
                                    "position": "1",
                                    "positionText": "1",
                                    "points": "25",
                                    "wins": "1",
                                    "Driver": hamilton,
                                    "Constructors": [mercedes],
                                }
                            ],
                        }
                    ]
                }
            }
        },
    )
    _write_json(
        year_dir / "constructorstandings.json",
        {
            "MRData": {
                "StandingsTable": {
                    "StandingsLists": [
                        {
                            "season": "2026",
                            "round": "1",
                            "ConstructorStandings": [
                                {
                                    "position": "1",
                                    "positionText": "1",
                                    "points": "25",
                                    "wins": "1",
                                    "Constructor": mercedes,
                                }
                            ],
                        }
                    ]
                }
            }
        },
    )


def _load(bronze_dir, table):
    with open(bronze_dir / f"{table}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_normalize_unifies_historical_and_api(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    jolpica_dir = raw_dir / "jolpica"
    bronze_dir = tmp_path / "bronze"

    _make_historical(raw_dir)
    _make_jolpica(jolpica_dir)
    normalize(
        raw_dir=raw_dir, jolpica_dir=jolpica_dir, bronze_dir=bronze_dir, start_year=2026
    )

    drivers = _load(bronze_dir, "drivers")
    by_ref = {r["driverRef"]: r for r in drivers}
    assert set(by_ref) == {"hamilton", "rookie1"}
    assert by_ref["hamilton"]["driverId"] == "1"
    assert by_ref["hamilton"]["source"] == "historical"
    assert by_ref["rookie1"]["driverId"] == "2"
    assert by_ref["rookie1"]["source"] == "api"
    assert by_ref["rookie1"]["number"] == "88"

    circuits = {r["circuitRef"]: r for r in _load(bronze_dir, "circuits")}
    assert circuits["monza"]["circuitId"] == "1"
    assert circuits["madring"]["circuitId"] == "2"
    assert circuits["madring"]["country"] == "Spain"

    statuses = {r["status"]: r for r in _load(bronze_dir, "status")}
    assert statuses["Finished"]["statusId"] == "1"
    assert statuses["Accident"]["statusId"] == "2"
    assert statuses["Accident"]["source"] == "api"

    seasons = _load(bronze_dir, "seasons")
    assert {r["year"] for r in seasons} == {"2024", "2025"}

    races = {r["year"]: r for r in _load(bronze_dir, "races")}
    assert races["2024"]["raceId"] == "1"
    r26 = races["2026"]
    assert r26["raceId"] == "2"
    assert r26["source"] == "api"
    assert r26["circuitId"] == "2"
    assert r26["time"] == "14:00:00"
    assert r26["sprint_date"] == "NULL"

    results = _load(bronze_dir, "results")
    assert len(results) == 3
    hist, r_ham, r_rook = results
    assert hist["resultId"] == "1" and hist["source"] == "historical"
    assert r_ham["raceId"] == "2" and r_ham["driverId"] == "1"
    assert r_ham["positionOrder"] == "1"
    assert r_ham["milliseconds"] == "6126304"
    assert r_ham["fastestLapTime"] == "1:22.167"
    assert r_ham["fastestLapSpeed"] == "NULL"
    assert r_rook["driverId"] == "2" and r_rook["constructorId"] == "2"

    laps = _load(bronze_dir, "lap_times")
    assert {r["milliseconds"] for r in laps} == {"98109", "99000"}
    assert all(r["source"] == "api" for r in laps)

    pit = _load(bronze_dir, "pit_stops")
    assert {r["milliseconds"] for r in pit} == {"13341", "73341"}
    assert all(r["source"] == "api" for r in pit)

    qualifying = _load(bronze_dir, "qualifying")
    assert len(qualifying) == 2
    assert qualifying[0]["qualifyId"] == "1"

    sprint = _load(bronze_dir, "sprint_results")
    assert len(sprint) == 1
    assert sprint[0]["sprintResultId"] == "1"

    ds = _load(bronze_dir, "driver_standings")
    assert len(ds) == 2
    assert ds[1]["driverStandingsId"] == "2"
    assert ds[1]["raceId"] == "2"
    assert ds[1]["driverId"] == "1"

    cs = _load(bronze_dir, "constructor_standings")
    assert len(cs) == 1
    assert cs[0]["constructorStandingsId"] == "1"
    assert cs[0]["constructorId"] == "1"

    # headers include trailing source column
    with open(bronze_dir / "results.csv", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header[-1] == "source"


def test_normalize_is_deterministic(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    jolpica_dir = raw_dir / "jolpica"
    _make_historical(raw_dir)
    _make_jolpica(jolpica_dir)

    bronze_a = tmp_path / "bronze_a"
    bronze_b = tmp_path / "bronze_b"
    normalize(
        raw_dir=raw_dir, jolpica_dir=jolpica_dir, bronze_dir=bronze_a, start_year=2026
    )
    normalize(
        raw_dir=raw_dir, jolpica_dir=jolpica_dir, bronze_dir=bronze_b, start_year=2026
    )

    for table in SCHEMAS:
        assert (bronze_a / f"{table}.csv").read_bytes() == (
            bronze_b / f"{table}.csv"
        ).read_bytes()
