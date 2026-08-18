import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path for imports to work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.constants import (
    JOLPICA_DIR,
    API_START_YEAR,
    RAW_DIR,
    GLOBAL_ENDPOINTS,
    SEASON_ENDPOINTS,
    ROUND_ENDPOINTS,
    HISTORICAL_EXPECTED_LAST_YEAR,
    HISTORICAL_TABLES,
)
from src.utils import races_last_year

# File sets derived from endpoint lists so they stay in sync
GLOBAL_FILES = {f"{ep}.json" for ep in GLOBAL_ENDPOINTS}
YEAR_FILES = (
    {"races.json"}
    | {f"{ep}.json" for ep in SEASON_ENDPOINTS}
    | {f"{ep}.json" for ep in ROUND_ENDPOINTS}
)


def is_year_complete(year: int) -> bool:
    year_dir = JOLPICA_DIR / str(year)
    if not year_dir.is_dir():
        return False
    existing = {f.name for f in year_dir.iterdir() if f.is_file()}
    return YEAR_FILES.issubset(existing)


def is_historical_complete() -> bool:
    if not RAW_DIR.is_dir():
        return False
    existing = {f.name for f in RAW_DIR.glob("*.csv") if f.stat().st_size > 0}
    if not {f"{t}.csv" for t in HISTORICAL_TABLES}.issubset(existing):
        return False
    # Content check: races.csv must reach the expected last year
    last_year = races_last_year(RAW_DIR / "races.csv")
    return last_year is not None and last_year >= HISTORICAL_EXPECTED_LAST_YEAR


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate F1 data ingestion (historical CSVs + Jolpica API)."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"Specific year to fetch (default: {API_START_YEAR}-{datetime.now().year})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch all data even if cached/complete",
    )
    args = parser.parse_args()

    JOLPICA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  F1 Data Ingestion Pipeline")
    print("=" * 60)

    # Historical CSVs: one-time download, skip if already present
    if is_historical_complete() and not args.force:
        print("[historical] CSVs already downloaded (use --force to re-download)")
    else:
        print("[historical] Downloading historical CSVs...")
        import ingest_historical

        ingest_historical.download_historical_csvs()

    from ingest_jolpica import fetch_global_endpoints, ingest_year

    # Global endpoints: always re-fetch (tiny, keeps data current)
    print("[global] Fetching global endpoints...")
    fetch_global_endpoints(force=True)

    # Determine which years to process
    if args.year:
        years = [args.year]
    else:
        years = range(API_START_YEAR, datetime.now().year + 1)

    t0 = time.time()
    failed = []
    for year in years:
        complete = is_year_complete(year)
        is_current = year == datetime.now().year

        # Skip past years that are already complete (unless --force)
        if complete and not is_current and not args.force:
            print(f"[{year}] Complete, skipping (use --force to re-fetch)")
            continue

        if is_current:
            print(f"[{year}] Current year, re-fetching...")
        else:
            print(f"[{year}] Incomplete or --force, fetching...")

        try:
            # Current year: full season endpoints + incremental round updates
            ingest_year(
                year,
                force=args.force or is_current,
                incremental_rounds=is_current and not args.force,
            )
        except Exception as e:
            print(f"[{year}] FAILED: {e}")
            failed.append(year)

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Done in {elapsed:.0f}s")
    print(f"{'=' * 60}")
    print()
    for year in years:
        status = "complete" if is_year_complete(year) else "INCOMPLETE"
        print(f"  {year}: {status}")
    if failed:
        print(f"\n  Failed years: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
