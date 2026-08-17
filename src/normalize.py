"""Merge raw historical CSVs and Jolpica API JSON into unified bronze CSVs.

Historical rows keep their original integer IDs. API rows resolve references
(drivers/constructors/circuits/status by slug, races by year+round) against the
historical tables and allocate new integer IDs for anything new. A trailing
``source`` column marks each row as 'historical' or 'api'.
"""

import json
import sys

from bronze_schemas import ID_TABLES, SCHEMAS, SLUG_TABLES
from constants import API_START_YEAR, BRONZE_DIR, JOLPICA_DIR, RAW_DIR
from utils import NULL, read_csv, strip_z, time_str_to_millis, write_csv


class Context:
    def __init__(self):
        self.bronze = {}
        self.next_id = {}
        self.slug_id = {}
        self.race_id = {}

    def ensure_entity(self, table, slug, attrs):
        """Resolve a slug to its ID, adding a new bronze row for unknown slugs."""
        slug = str(slug)
        mapping = self.slug_id[table]
        if slug in mapping:
            return mapping[slug]
        idcol = ID_TABLES[table]
        new_id = str(self.next_id[table])
        self.next_id[table] += 1
        mapping[slug] = new_id
        row = dict(attrs)
        row[idcol] = new_id
        row["source"] = "api"
        self.bronze[table].append(row)
        return new_id


def load_historical(raw_dir, ctx):
    for table in SCHEMAS:
        rows = read_csv(raw_dir / f"{table}.csv")
        for row in rows:
            row["source"] = "historical"
        ctx.bronze[table] = rows

    for table, idcol in ID_TABLES.items():
        max_id = max((int(row[idcol]) for row in ctx.bronze[table]), default=0)
        ctx.next_id[table] = max_id + 1

    for table, (refcol, idcol) in SLUG_TABLES.items():
        ctx.slug_id[table] = {row[refcol]: row[idcol] for row in ctx.bronze[table]}

    ctx.race_id = {
        (int(row["year"]), int(row["round"])): row["raceId"]
        for row in ctx.bronze["races"]
    }


def process_global(ctx, jolpica_dir):
    data = json.loads((jolpica_dir / "seasons.json").read_text(encoding="utf-8"))
    existing = {row["year"] for row in ctx.bronze["seasons"]}
    for s in data["MRData"]["SeasonTable"]["Seasons"]:
        if s["season"] not in existing:
            ctx.bronze["seasons"].append(
                {"year": s["season"], "url": s.get("url"), "source": "api"}
            )

    data = json.loads((jolpica_dir / "status.json").read_text(encoding="utf-8"))
    for s in data["MRData"]["StatusTable"]["Status"]:
        ctx.ensure_entity("status", s["status"], {"status": s["status"]})


def add_api_race(ctx, race):
    year, rnd = int(race["season"]), int(race["round"])
    key = (year, rnd)
    if key in ctx.race_id:
        return ctx.race_id[key]
    circuit = race["Circuit"]
    circuit_id = ctx.ensure_entity(
        "circuits",
        circuit["circuitId"],
        api_circuit_attrs(circuit),
    )
    row = {
        "year": str(year),
        "round": str(rnd),
        "circuitId": circuit_id,
        "name": race.get("raceName"),
        "date": race.get("date"),
        "time": strip_z(race.get("time")),
        "url": race.get("url"),
        "fp1_date": _session_date(race, "FirstPractice"),
        "fp1_time": _session_time(race, "FirstPractice"),
        "fp2_date": _session_date(race, "SecondPractice"),
        "fp2_time": _session_time(race, "SecondPractice"),
        "fp3_date": _session_date(race, "ThirdPractice"),
        "fp3_time": _session_time(race, "ThirdPractice"),
        "quali_date": _session_date(race, "Qualifying"),
        "quali_time": _session_time(race, "Qualifying"),
        "sprint_date": _session_date(race, "Sprint"),
        "sprint_time": _session_time(race, "Sprint"),
    }
    race_id = str(ctx.next_id["races"])
    ctx.next_id["races"] += 1
    row["raceId"] = race_id
    row["source"] = "api"
    ctx.race_id[key] = race_id
    ctx.bronze["races"].append(row)
    return race_id


def _session_date(race, key):
    session = race.get(key)
    return session.get("date") if session else NULL


def _session_time(race, key):
    session = race.get(key)
    return strip_z(session.get("time")) if session else NULL


def api_circuit_attrs(circuit):
    loc = circuit.get("Location") or {}
    return {
        "circuitRef": circuit["circuitId"],
        "name": circuit.get("circuitName"),
        "location": loc.get("locality"),
        "country": loc.get("country"),
        "lat": loc.get("lat"),
        "lng": loc.get("long"),
        "alt": NULL,
        "url": circuit.get("url"),
    }


def _driver_id(ctx, slug):
    return ctx.ensure_entity("drivers", slug, {"driverRef": str(slug)})


def _constructor_id(ctx, slug):
    return ctx.ensure_entity("constructors", slug, {"constructorRef": str(slug)})


def _status_id(ctx, status):
    return ctx.ensure_entity("status", status, {"status": str(status)})


def _race_id(ctx, year, rnd):
    key = (int(year), int(rnd))
    if key not in ctx.race_id:
        raise KeyError(f"No race registered for {key}")
    return ctx.race_id[key]


def _alloc(ctx, table):
    new_id = str(ctx.next_id[table])
    ctx.next_id[table] += 1
    return new_id


def process_results(ctx, year_dir, year):
    data = json.loads((year_dir / "results.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        race_id = _race_id(ctx, race["season"], race["round"])
        for i, res in enumerate(race.get("Results") or []):
            time = res.get("Time") or {}
            fl = res.get("FastestLap") or {}
            fl_time = (fl.get("Time") or {}).get("time")
            row = {
                "raceId": race_id,
                "driverId": _driver_id(ctx, res["Driver"]["driverId"]),
                "constructorId": _constructor_id(
                    ctx, res["Constructor"]["constructorId"]
                ),
                "number": res.get("number"),
                "grid": res.get("grid"),
                "position": res.get("position"),
                "positionText": res.get("positionText"),
                "positionOrder": str(i + 1),
                "points": res.get("points"),
                "laps": res.get("laps"),
                "time": time.get("time"),
                "milliseconds": time.get("millis"),
                "fastestLap": fl.get("lap"),
                "rank": fl.get("rank"),
                "fastestLapTime": fl_time,
                "fastestLapSpeed": NULL,
                "statusId": _status_id(ctx, res.get("status")),
            }
            row["resultId"] = _alloc(ctx, "results")
            row["source"] = "api"
            ctx.bronze["results"].append(row)


def process_qualifying(ctx, year_dir, year):
    data = json.loads((year_dir / "qualifying.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        race_id = _race_id(ctx, race["season"], race["round"])
        for q in race.get("QualifyingResults") or []:
            row = {
                "raceId": race_id,
                "driverId": _driver_id(ctx, q["Driver"]["driverId"]),
                "constructorId": _constructor_id(
                    ctx, q["Constructor"]["constructorId"]
                ),
                "number": q.get("number"),
                "position": q.get("position"),
                "q1": q.get("Q1"),
                "q2": q.get("Q2"),
                "q3": q.get("Q3"),
            }
            row["qualifyId"] = _alloc(ctx, "qualifying")
            row["source"] = "api"
            ctx.bronze["qualifying"].append(row)


def process_sprint(ctx, year_dir, year):
    data = json.loads((year_dir / "sprint.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        race_id = _race_id(ctx, race["season"], race["round"])
        for i, res in enumerate(race.get("SprintResults") or []):
            time = res.get("Time") or {}
            fl = res.get("FastestLap") or {}
            fl_time = (fl.get("Time") or {}).get("time")
            row = {
                "raceId": race_id,
                "driverId": _driver_id(ctx, res["Driver"]["driverId"]),
                "constructorId": _constructor_id(
                    ctx, res["Constructor"]["constructorId"]
                ),
                "number": res.get("number"),
                "grid": res.get("grid"),
                "position": res.get("position"),
                "positionText": res.get("positionText"),
                "positionOrder": str(i + 1),
                "points": res.get("points"),
                "laps": res.get("laps"),
                "time": time.get("time"),
                "milliseconds": time.get("millis"),
                "fastestLap": fl.get("lap"),
                "fastestLapTime": fl_time,
                "statusId": _status_id(ctx, res.get("status")),
            }
            row["sprintResultId"] = _alloc(ctx, "sprint_results")
            row["source"] = "api"
            ctx.bronze["sprint_results"].append(row)


def process_laps(ctx, year_dir, year):
    data = json.loads((year_dir / "laps.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        race_id = _race_id(ctx, race["season"], race["round"])
        for lap in race.get("Laps") or []:
            for t in lap.get("Timings") or []:
                row = {
                    "raceId": race_id,
                    "driverId": _driver_id(ctx, t["driverId"]),
                    "lap": lap.get("number"),
                    "position": t.get("position"),
                    "time": t.get("time"),
                    "milliseconds": time_str_to_millis(t.get("time")),
                    "source": "api",
                }
                ctx.bronze["lap_times"].append(row)


def process_pitstops(ctx, year_dir, year):
    data = json.loads((year_dir / "pitstops.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        race_id = _race_id(ctx, race["season"], race["round"])
        for ps in race.get("PitStops") or []:
            row = {
                "raceId": race_id,
                "driverId": _driver_id(ctx, ps["driverId"]),
                "stop": ps.get("stop"),
                "lap": ps.get("lap"),
                "time": ps.get("time"),
                "duration": ps.get("duration"),
                "milliseconds": time_str_to_millis(ps.get("duration")),
                "source": "api",
            }
            ctx.bronze["pit_stops"].append(row)


def _process_standings(ctx, year_dir, year, endpoint, item_key, table, id_col):
    data = json.loads((year_dir / f"{endpoint}.json").read_text(encoding="utf-8"))
    for standings_list in data["MRData"]["StandingsTable"]["StandingsLists"]:
        race_id = _race_id(ctx, standings_list["season"], standings_list["round"])
        for item in standings_list.get(item_key) or []:
            row = {
                "raceId": race_id,
                "points": item.get("points"),
                "position": item.get("position"),
                "positionText": item.get("positionText"),
                "wins": item.get("wins"),
            }
            if table == "driver_standings":
                row["driverId"] = _driver_id(ctx, item["Driver"]["driverId"])
            else:
                row["constructorId"] = _constructor_id(
                    ctx, item["Constructor"]["constructorId"]
                )
            row[id_col] = _alloc(ctx, table)
            row["source"] = "api"
            ctx.bronze[table].append(row)


def process_api_year(ctx, jolpica_dir, year):
    year_dir = jolpica_dir / str(year)

    data = json.loads((year_dir / "drivers.json").read_text(encoding="utf-8"))
    for d in data["MRData"]["DriverTable"]["Drivers"]:
        ctx.ensure_entity(
            "drivers",
            d["driverId"],
            {
                "driverRef": d["driverId"],
                "number": d.get("permanentNumber"),
                "code": d.get("code"),
                "forename": d.get("givenName"),
                "surname": d.get("familyName"),
                "dob": d.get("dateOfBirth"),
                "nationality": d.get("nationality"),
                "url": d.get("url"),
            },
        )

    data = json.loads((year_dir / "circuits.json").read_text(encoding="utf-8"))
    for c in data["MRData"]["CircuitTable"]["Circuits"]:
        ctx.ensure_entity("circuits", c["circuitId"], api_circuit_attrs(c))

    data = json.loads((year_dir / "constructors.json").read_text(encoding="utf-8"))
    for c in data["MRData"]["ConstructorTable"]["Constructors"]:
        ctx.ensure_entity(
            "constructors",
            c["constructorId"],
            {
                "constructorRef": c["constructorId"],
                "name": c.get("name"),
                "nationality": c.get("nationality"),
                "url": c.get("url"),
            },
        )

    data = json.loads((year_dir / "races.json").read_text(encoding="utf-8"))
    for race in data["MRData"]["RaceTable"]["Races"]:
        add_api_race(ctx, race)

    process_results(ctx, year_dir, year)
    process_qualifying(ctx, year_dir, year)
    process_sprint(ctx, year_dir, year)
    process_laps(ctx, year_dir, year)
    process_pitstops(ctx, year_dir, year)
    _process_standings(
        ctx,
        year_dir,
        year,
        "driverstandings",
        "DriverStandings",
        "driver_standings",
        "driverStandingsId",
    )
    _process_standings(
        ctx,
        year_dir,
        year,
        "constructorstandings",
        "ConstructorStandings",
        "constructor_standings",
        "constructorStandingsId",
    )


def normalize(
    raw_dir=RAW_DIR,
    jolpica_dir=JOLPICA_DIR,
    bronze_dir=BRONZE_DIR,
    start_year=API_START_YEAR,
):
    ctx = Context()
    load_historical(raw_dir, ctx)
    process_global(ctx, jolpica_dir)

    years = sorted(
        int(p.name)
        for p in jolpica_dir.iterdir()
        if p.is_dir() and p.name.isdigit() and int(p.name) >= start_year
    )
    for year in years:
        print(f"[normalize] {year}...")
        process_api_year(ctx, jolpica_dir, year)

    bronze_dir.mkdir(parents=True, exist_ok=True)
    for table, columns in SCHEMAS.items():
        write_csv(bronze_dir / f"{table}.csv", columns + ["source"], ctx.bronze[table])
        print(f"  {table}: {len(ctx.bronze[table])} rows")
    return ctx


if __name__ == "__main__":
    sys.exit(0 if normalize() else 1)
