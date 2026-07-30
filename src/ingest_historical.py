import argparse
import requests
import zipfile
from constants import PROJECT_DIR, RAW_DIR, HISTORICAL_DB_URL

ZIP_PATH = PROJECT_DIR / "data" / "f1db_csv.zip"


def download_historical_csvs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading historical F1 database from {HISTORICAL_DB_URL}...")
    resp = requests.get(HISTORICAL_DB_URL, stream=True)
    if resp.status_code == 200:
        with open(ZIP_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        print("Download complete. Extracting...")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(RAW_DIR)
        ZIP_PATH.unlink()
        print(f"Historical CSVs extracted to {RAW_DIR}")
    else:
        raise Exception(f"Historical DB download failed: HTTP {resp.status_code}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="One-time historical F1 data download (pre-2023)."
    )
    args = parser.parse_args()
    download_historical_csvs()
    print("Historical data ingestion complete.")
