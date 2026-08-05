import json
import os
import time
import argparse
from datetime import datetime

import requests
from constants import (
    JOLPICA_BASE,
    JOLPICA_DIR,
    API_START_YEAR,
    RATE_LIMIT_INTERVAL,
    PAGE_LIMIT,
    MAX_RETRIES,
    BACKOFF_BASE,
    MAX_BACKOFF,
    GLOBAL_ENDPOINTS,
    SEASON_ENDPOINTS,
    ROUND_ENDPOINTS,
    STANDINGS_ENDPOINTS,
    ROUND_ITEMS_KEY,
)

_last_request = 0.0


def calc_backoff(attempt: int) -> int:
    return min(BACKOFF_BASE * (2**attempt), MAX_BACKOFF)


def rate_limited_request(url: str) -> dict:
    global _last_request
    for attempt in range(MAX_RETRIES):
        now = time.perf_counter()
        wait = RATE_LIMIT_INTERVAL - (now - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.perf_counter()

        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 429:
            backoff = calc_backoff(attempt)
            print(f"    429  backing off {backoff}s...")
            time.sleep(backoff)
            _last_request = time.perf_counter()
            continue

        resp.raise_for_status()

    raise Exception(f"Failed after {MAX_RETRIES} attempts: {url}")


def req(url: str) -> dict:
    return rate_limited_request(url)


def fetch_paginated(url: str) -> dict:
    """Fetch an endpoint, following pagination until all rows are collected."""
    data = req(url)
    mrd = data["MRData"]
    table = next(v for k, v in mrd.items() if isinstance(v, dict))
    list_key = next(k for k, v in table.items() if isinstance(v, list))
    offset = len(table[list_key])
    while offset < int(mrd["total"]):
        page = req(f"{url}?limit={PAGE_LIMIT}&offset={offset}")
        pm = page["MRData"]
        ptable = next(v for k, v in pm.items() if isinstance(v, dict))
        plist_key = next(k for k, v in ptable.items() if isinstance(v, list))
        table[list_key].extend(ptable[plist_key])
        offset = len(table[list_key])
    mrd["limit"] = str(len(table[list_key]))
    return data


def write_json_atomic(path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    os.replace(tmp, path)


def fetch_global_endpoints(force: bool = False):
    for ep in GLOBAL_ENDPOINTS:
        out = JOLPICA_DIR / f"{ep}.json"
        if out.exists() and not force:
            print(f"  [SKIP] {ep}.json exists (use --force to re-fetch)")
            continue
        print(f"  Fetching {ep}...", end=" ")
        data = fetch_paginated(f"{JOLPICA_BASE}/{ep}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out, data)
        print(f"saved (total={data['MRData']['total']})")


def fetch_round_data(year: int, round_num: str, endpoint: str) -> list:
    items_key = ROUND_ITEMS_KEY[endpoint]
    base_url = f"{JOLPICA_BASE}/{year}/{round_num}/{endpoint}.json"

    # Laps: pagination splits driver timings across pages, merge by lap number
    if endpoint == "laps":
        laps_by_number = {}
        offset = 0
        total = None
        page = 0
        while total is None or offset < int(total):
            url = f"{base_url}?limit={PAGE_LIMIT}&offset={offset}"
            data = req(url)
            mrd = data["MRData"]
            if total is None:
                total = mrd["total"]
                pages_expected = max(1, (int(total) + PAGE_LIMIT - 1) // PAGE_LIMIT)
                print(f"({pages_expected}p) ", end="")
            for lap in (
                mrd["RaceTable"]["Races"][0].get("Laps", [])
                if mrd["RaceTable"]["Races"]
                else []
            ):
                num = lap["number"]
                if num not in laps_by_number:
                    laps_by_number[num] = dict(lap)
                else:
                    laps_by_number[num]["Timings"] = laps_by_number[num].get(
                        "Timings", []
                    ) + lap.get("Timings", [])
            offset += PAGE_LIMIT
            page += 1
        merged = [laps_by_number[k] for k in sorted(laps_by_number, key=int)]
        laps_count = len(merged)
        timings_count = sum(len(l.get("Timings", [])) for l in merged)
        print(f"({page} pages, {laps_count} laps, {timings_count} timings)", end="")
        return merged

    if endpoint == "pitstops":
        all_items = []
        offset = 0
        total = None
        pages = 0
        while total is None or offset < int(total):
            url = f"{base_url}?limit={PAGE_LIMIT}&offset={offset}"
            data = req(url)
            mrd = data["MRData"]
            if total is None:
                total = mrd["total"]
            if mrd["RaceTable"]["Races"]:
                all_items.extend(mrd["RaceTable"]["Races"][0].get("PitStops", []))
            offset += PAGE_LIMIT
            pages += 1
        print(f"({pages} page, {len(all_items)} stops)", end="")
        return all_items

    data = req(base_url)
    mrd = data["MRData"]

    # Standings responses use StandingsTable instead of RaceTable
    if "StandingsTable" in mrd:
        lists = mrd["StandingsTable"].get("StandingsLists", [])
        return lists[0].get(items_key, []) if lists else []

    races = mrd["RaceTable"]["Races"]
    if not races:
        return []
    return races[0].get(items_key, [])


def build_round_payload(year: int, endpoint: str, entries: list) -> dict:
    items_key = ROUND_ITEMS_KEY[endpoint]
    is_standings = endpoint in STANDINGS_ENDPOINTS
    grand_total = sum(len(e.get(items_key, [])) for e in entries)

    if is_standings:
        table = {"season": str(year), "StandingsLists": entries}
    else:
        table = {"season": str(year), "Races": entries}

    return {
        "MRData": {
            "xmlns": "",
            "series": "f1",
            "url": f"{JOLPICA_BASE}/{year}/{endpoint}.json",
            "limit": str(grand_total),
            "offset": "0",
            "total": str(grand_total),
            "StandingsTable" if is_standings else "RaceTable": table,
        }
    }


def build_year_endpoint(year: int, endpoint: str, races: list) -> dict:
    items_key = ROUND_ITEMS_KEY[endpoint]
    is_sprint = endpoint == "sprint"
    is_standings = endpoint in STANDINGS_ENDPOINTS
    entries = []

    print(f"  {endpoint}: ", end="")
    for race in races:
        rn = race["round"]
        if is_sprint and "Sprint" not in race:
            continue
        print(f"r{rn} ", end="")
        items = fetch_round_data(year, rn, endpoint)
        if is_standings:
            entry = {"season": str(year), "round": rn, items_key: items}
        else:
            entry = dict(race)
            entry[items_key] = items
        entries.append(entry)
    print(f" done (total={sum(len(e.get(items_key, [])) for e in entries)})")

    return build_round_payload(year, endpoint, entries)


def compute_rounds_to_fetch(races_list: list, existing: dict, endpoint: str) -> set:
    """Rounds to fetch: missing/empty due rounds plus the latest data round."""
    items_key = ROUND_ITEMS_KEY[endpoint]
    today = datetime.now().strftime("%Y-%m-%d")
    api_rounds = {r["round"] for r in races_list}

    due = [r for r in races_list if r.get("date", "") <= today]
    if endpoint == "sprint":
        due = [r for r in due if "Sprint" in r]

    to_fetch = set()
    for race in due:
        rn = race["round"]
        entry = existing.get(rn)
        if entry is None or not entry.get(items_key):
            to_fetch.add(rn)

    data_rounds = [
        rn
        for rn, entry in existing.items()
        if rn in api_rounds and entry.get(items_key)
    ]
    if data_rounds:
        to_fetch.add(max(data_rounds, key=int))

    return to_fetch


def update_round_endpoint(year: int, endpoint: str, races_list: list) -> None:
    items_key = ROUND_ITEMS_KEY[endpoint]
    is_standings = endpoint in STANDINGS_ENDPOINTS
    out = JOLPICA_DIR / str(year) / f"{endpoint}.json"

    existing = {}
    if out.exists():
        try:
            table_key = "StandingsLists" if is_standings else "Races"
            payload = json.loads(out.read_text())
            for entry in payload["MRData"][
                "StandingsTable" if is_standings else "RaceTable"
            ][table_key]:
                existing[entry["round"]] = entry
        except Exception:
            print(f"  {endpoint}: corrupt file, rebuilding")

    to_fetch = compute_rounds_to_fetch(races_list, existing, endpoint)

    entries = dict(existing)
    races_by_round = {r["round"]: r for r in races_list}
    print(f"  {endpoint}: ", end="")
    for rn in sorted(to_fetch, key=int):
        print(f"r{rn} ", end="")
        items = fetch_round_data(year, rn, endpoint)
        if is_standings:
            entry = {"season": str(year), "round": rn, items_key: items}
        else:
            entry = dict(races_by_round[rn])
            entry[items_key] = items
        entries[rn] = entry
    print(f" done (total={sum(len(e.get(items_key, [])) for e in entries.values())})")

    ordered = [entries[rn] for rn in sorted(entries, key=int)]
    write_json_atomic(out, build_round_payload(year, endpoint, ordered))


def ingest_year(year: int, force: bool = False, incremental_rounds: bool = False):
    year_dir = JOLPICA_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'-' * 60}")
    print(f"  {year}")
    print(f"{'-' * 60}")

    def skip_if_exists(filename: str) -> bool:
        out = year_dir / filename
        if out.exists() and not force:
            print(f"  {filename} exists, skipping (use --force to re-fetch)")
            return True
        return False

    def fetch_season_endpoint(ep: str):
        url = f"{JOLPICA_BASE}/{year}/{ep}.json"
        print(f"  {ep}: ", end="")
        data = fetch_paginated(url)
        print(f"saved (total={data['MRData']['total']})")
        write_json_atomic(year_dir / f"{ep}.json", data)

    if incremental_rounds:
        # Season endpoints always re-fetched; round endpoints updated incrementally
        races = req(f"{JOLPICA_BASE}/{year}/races.json")
        races_list = races["MRData"]["RaceTable"]["Races"]
        print(f"  races: {len(races_list)} rounds")
        write_json_atomic(year_dir / "races.json", races)

        for ep in SEASON_ENDPOINTS:
            fetch_season_endpoint(ep)

        for ep in ROUND_ENDPOINTS:
            update_round_endpoint(year, ep, races_list)
        return

    if skip_if_exists("races.json"):
        races_list = None
    else:
        races = req(f"{JOLPICA_BASE}/{year}/races.json")
        races_list = races["MRData"]["RaceTable"]["Races"]
        print(f"  races: {len(races_list)} rounds")
        write_json_atomic(year_dir / "races.json", races)

    for ep in SEASON_ENDPOINTS:
        if skip_if_exists(f"{ep}.json"):
            continue
        fetch_season_endpoint(ep)

    if races_list is None:
        races_list = json.loads((year_dir / "races.json").read_text())["MRData"][
            "RaceTable"
        ]["Races"]

    for ep in ROUND_ENDPOINTS:
        if skip_if_exists(f"{ep}.json"):
            continue
        payload = build_year_endpoint(year, ep, races_list)
        write_json_atomic(year_dir / f"{ep}.json", payload)


def main():
    parser = argparse.ArgumentParser(description="Fetch F1 data from Jolpica API.")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"Year to fetch (default: {API_START_YEAR}-{datetime.now().year})",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-fetch global endpoints even if cached"
    )
    args = parser.parse_args()

    JOLPICA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Jolpica F1 Data Ingestion")
    print(f"  Rate limit: {RATE_LIMIT_INTERVAL}s between requests")
    print("=" * 60)

    print("\n[Global]")
    fetch_global_endpoints(force=args.force)

    if args.year:
        years = [args.year]
    else:
        years = range(API_START_YEAR, datetime.now().year + 1)

    t0 = time.time()
    for year in years:
        is_current = year == datetime.now().year
        # Current year: full season endpoints + incremental round updates
        ingest_year(
            year,
            force=args.force or is_current,
            incremental_rounds=is_current and not args.force,
        )
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Complete in {elapsed:.0f}s. Data: {JOLPICA_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
