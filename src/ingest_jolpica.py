import json
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
    GLOBAL_ENDPOINTS,
    SEASON_ENDPOINTS,
    ROUND_ENDPOINTS,
    ROUND_ITEMS_KEY,
)

_last_request = 0.0


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
            backoff = 3 * (2**attempt)
            print(f"    429  backing off {backoff}s...")
            time.sleep(backoff)
            _last_request = time.perf_counter()
            continue

        resp.raise_for_status()

    raise Exception(f"Failed after 5 attempts: {url}")


def req(url: str) -> dict:
    return rate_limited_request(url)


def fetch_global_endpoints(force: bool = False):
    for ep in GLOBAL_ENDPOINTS:
        out = JOLPICA_DIR / f"{ep}.json"
        if out.exists() and not force:
            print(f"  [SKIP] {ep}.json exists (use --force to re-fetch)")
            continue
        print(f"  Fetching {ep}...", end=" ")
        data = req(f"{JOLPICA_BASE}/{ep}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            json.dump(data, f, indent=2)
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
    races = data["MRData"]["RaceTable"]["Races"]
    if not races:
        return []
    return races[0].get(items_key, [])


def build_year_endpoint(year: int, endpoint: str, races: list) -> dict:
    items_key = ROUND_ITEMS_KEY[endpoint]
    is_sprint = endpoint == "sprint"
    all_races = []
    grand_total = 0

    print(f"  {endpoint}: ", end="")
    for race in races:
        rn = race["round"]
        if is_sprint and "Sprint" not in race:
            continue
        print(f"r{rn} ", end="")
        items = fetch_round_data(year, rn, endpoint)
        entry = dict(race)
        entry[items_key] = items
        all_races.append(entry)
        grand_total += len(items)
    print(f" done (total={grand_total})")

    return {
        "MRData": {
            "xmlns": "",
            "series": "f1",
            "url": f"{JOLPICA_BASE}/{year}/{endpoint}.json",
            "limit": str(grand_total),
            "offset": "0",
            "total": str(grand_total),
            "RaceTable": {"season": str(year), "Races": all_races},
        }
    }


def ingest_year(year: int):
    year_dir = JOLPICA_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'-' * 60}")
    print(f"  {year}")
    print(f"{'-' * 60}")

    races = req(f"{JOLPICA_BASE}/{year}/races.json")
    races_list = races["MRData"]["RaceTable"]["Races"]
    print(f"  races: {len(races_list)} rounds")
    (year_dir / "races.json").write_text(json.dumps(races, indent=2))

    for ep in SEASON_ENDPOINTS:
        url = f"{JOLPICA_BASE}/{year}/{ep}.json"
        print(f"  {ep}: ", end="")
        data = req(url)
        tot = data["MRData"]["total"]
        print(f"saved (total={tot})")
        (year_dir / f"{ep}.json").write_text(json.dumps(data, indent=2))

    for ep in ROUND_ENDPOINTS:
        payload = build_year_endpoint(year, ep, races_list)
        (year_dir / f"{ep}.json").write_text(json.dumps(payload, indent=2))


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
        ingest_year(year)
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Complete in {elapsed:.0f}s. Data: {JOLPICA_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
