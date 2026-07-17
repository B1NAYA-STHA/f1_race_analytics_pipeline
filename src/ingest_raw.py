import os
import requests
import zipfile
import json
from pathlib import Path

# Setup paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ZIP_PATH = DATA_DIR / "f1db_csv.zip"

# URL of the historical Ergast CSV dataset mirror
HISTORICAL_DB_URL = "https://raw.githubusercontent.com/rubenv/ergast-mrd/master/f1db_csv.zip"

# Jolpica API URL
JOLPICA_API_URL = "https://api.jolpi.ca/ergast/f1"

def create_directories():
    """Ensure raw and data directories exist."""
    print("Creating local directories...")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

def download_historical_csvs():
    """Download and extract historical database CSVs."""
    print(f"Downloading historical F1 database zip from {HISTORICAL_DB_URL}...")
    
    response = requests.get(HISTORICAL_DB_URL, stream=True)
    if response.status_code == 200:
        with open(ZIP_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        print("Download complete. Extracting files...")
        
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(RAW_DIR)
        
        # Clean up zip
        ZIP_PATH.unlink()
        print(f"Extraction complete. CSVs stored in: {RAW_DIR}")
    else:
        raise Exception(f"Failed to download historical database. HTTP status: {response.status_code}")

def download_recent_race_data(season=2024, round_num=1):
    """
    Fetch recent race results from Jolpica F1 API (Ergast successor)
    and save them as a JSON file to demonstrate incremental refresh capability.
    """
    api_url = f"{JOLPICA_API_URL}/{season}/{round_num}/results.json"
    print(f"Fetching race results from Jolpica API: {api_url}...")
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Save raw json output
            output_file = RAW_DIR / f"api_results_{season}_r{round_num}.json"
            with open(output_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Successfully saved API results to: {output_file}")
        else:
            print(f"Jolpica API call failed with status: {response.status_code}")
    except Exception as e:
        print(f"Failed to fetch from Jolpica API: {e}")

if __name__ == "__main__":
    create_directories()
    download_historical_csvs()
    # Download 2024 Round 1 results to demonstrate API integration
    download_recent_race_data(season=2024, round_num=1)
    print("Ingestion layer completed successfully!")
