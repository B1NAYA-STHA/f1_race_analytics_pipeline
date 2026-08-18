import argparse
import io
import zipfile
from pathlib import Path
import sys

# Add project root to path for imports to work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from src.constants import (
    RAW_DIR,
    HISTORICAL_DB_URL,
    HISTORICAL_EXPECTED_LAST_YEAR,
    HISTORICAL_FILE_MAP,
)
from src.utils import races_last_year


def download_historical_csvs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(
        f"Downloading historical F1 database (1950-{HISTORICAL_EXPECTED_LAST_YEAR})..."
    )
    resp = requests.get(HISTORICAL_DB_URL, stream=True)
    if resp.status_code != 200:
        raise Exception(f"Historical DB download failed: HTTP {resp.status_code}")

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        names = set(z.namelist())
        missing = [src for src in HISTORICAL_FILE_MAP if src not in names]
        if missing:
            raise Exception(f"Zip missing expected files: {missing}")
        for src, dst in HISTORICAL_FILE_MAP.items():
            (RAW_DIR / dst).write_bytes(z.read(src))

    last_year = races_last_year(RAW_DIR / "races.csv")
    if last_year is None or last_year < HISTORICAL_EXPECTED_LAST_YEAR:
        raise Exception(
            f"Historical data only covers through {last_year}, "
            f"expected >= {HISTORICAL_EXPECTED_LAST_YEAR}"
        )
    print(f"Historical CSVs written to {RAW_DIR} (races through {last_year})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="One-time historical F1 data download (1950-2024)."
    )
    args = parser.parse_args()
    download_historical_csvs()
    print("Historical data ingestion complete.")
