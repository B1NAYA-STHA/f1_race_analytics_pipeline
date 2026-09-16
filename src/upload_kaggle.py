#!/usr/bin/env python3
"""
Upload F1 data to Kaggle as a new dataset version.

Auth (set via Airflow Connection or .env):
- KAGGLE_API_TOKEN (the KGAT_... access token; primary, required by Kaggle CLI >= 2.x)
- Legacy fallback: KAGGLE_USERNAME + KAGGLE_KEY
- KAGGLE_DATASET (format: "username/dataset-slug", e.g., "binayas/f1-dataset")

Tags/description/subtitle are carried into the new version from the dataset's
current metadata so version uploads do not clear values set in the Kaggle UI.
Override per upload (env wins over fetched metadata):
- KAGGLE_TAGS (comma-separated tag names)
- KAGGLE_DESCRIPTION
- KAGGLE_SUBTITLE (must be 20-80 characters)

Optional:
- KAGGLE_CONFIG_DIR (default: ~/.kaggle)

Run manually:
    KAGGLE_API_TOKEN=KGAT_xxx KAGGLE_DATASET=binayas/f1-dataset python src/upload_kaggle.py
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
METADATA_FILE = "dataset-metadata.json"

KAGGLE_CONFIG_DIR = Path(os.getenv("KAGGLE_CONFIG_DIR", Path.home() / ".kaggle"))


def find_kaggle() -> str:
    candidates = []
    venv = os.getenv("VIRTUAL_ENV")
    if venv is not None:
        candidates.append(Path(venv) / "Scripts" / "kaggle.exe")
        candidates.append(Path(venv) / "bin" / "kaggle")
    candidates.append(Path(sys.executable).parent / "Scripts" / "kaggle.exe")
    candidates.append(Path(sys.executable).parent / "kaggle")
    candidates.append(PROJECT_ROOT / ".venv" / "Scripts" / "kaggle.exe")
    for cand in candidates:
        if cand.exists():
            return str(cand)
    path_kaggle = shutil.which("kaggle")
    if path_kaggle:
        return path_kaggle
    return "kaggle"


def fetch_live_metadata(dataset: str) -> dict | None:
    """Fetch the dataset's current tags/description/subtitle from Kaggle.

    Returns a dict with keys: tags, description, subtitle (and license_name,
    current_version_number, title).  Returns None on any failure so the upload
    can fall back to env defaults only.
    """
    try:
        from kaggle import KaggleApi
        from kagglesdk.datasets.types.dataset_api_service import ApiGetDatasetRequest

        owner, slug = dataset.split("/", 1)
        api = KaggleApi()
        api.authenticate()

        with api.build_kaggle_client() as kaggle:
            request = ApiGetDatasetRequest()
            request.owner_slug = owner
            request.dataset_slug = slug
            ds = kaggle.datasets.dataset_api_client.get_dataset(request)

        if ds is None:
            return None

        return {
            "title": getattr(ds, "title", None),
            "subtitle": getattr(ds, "subtitle", None),
            "description": getattr(ds, "description", None),
            "license_name": getattr(ds, "license_name", None),
            "current_version_number": getattr(ds, "current_version_number", None),
            "tags": [
                {"name": getattr(t, "name", None)}
                for t in (getattr(ds, "tags", None) or [])
                if getattr(t, "name", None)
            ],
        }
    except Exception as e:
        print(f"Warning: Could not fetch live dataset metadata: {e}", file=sys.stderr)
        return None


def parse_tags(live: dict | None) -> list:
    """Tag names from fetched metadata, or [] if none/absent."""
    if not live:
        return []
    return [
        str(tag["name"])
        for tag in (live.get("tags") or [])
        if isinstance(tag, dict) and tag.get("name")
    ]


def build_metadata(dataset: str, live: dict | None = None) -> dict:
    """Build dataset-metadata.json contents preserving tags/description/subtitle.

    Env vars override the fetched metadata; fields absent from both are omitted.
    """
    meta = {"id": dataset}

    env_tags = os.getenv("KAGGLE_TAGS", "").strip()
    keywords = [t.strip() for t in env_tags.split(",")] if env_tags else parse_tags(live)
    if keywords:
        meta["keywords"] = keywords

    description = os.getenv("KAGGLE_DESCRIPTION", "").strip()
    if not description and live and live.get("description"):
        description = str(live["description"]).strip()
    if description:
        meta["description"] = description

    subtitle = os.getenv("KAGGLE_SUBTITLE", "").strip()
    if not subtitle and live and live.get("subtitle"):
        subtitle = str(live["subtitle"]).strip()
    if subtitle and 20 <= len(subtitle) <= 80:
        meta["subtitle"] = subtitle
    elif subtitle:
        print("Warning: KAGGLE_SUBTITLE must be 20-80 chars; omitting it", file=sys.stderr)

    return meta


def main() -> None:
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    dataset = os.getenv("KAGGLE_DATASET")
    api_token = os.getenv("KAGGLE_API_TOKEN")

    auth = ("token", api_token) if api_token else ("legacy", None)
    if auth[0] == "legacy" and not all([username, key]):
        print(
            "ERROR: Missing Kaggle credentials. Provide KAGGLE_API_TOKEN "
            "or KAGGLE_USERNAME + KAGGLE_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not dataset:
        print("ERROR: Missing env var: KAGGLE_DATASET", file=sys.stderr)
        sys.exit(1)

    if not BRONZE_DIR.exists():
        print(f"ERROR: Bronze directory not found: {BRONZE_DIR}", file=sys.stderr)
        sys.exit(1)

    csv_files = list(BRONZE_DIR.glob("*.csv"))
    if not csv_files:
        print(f"ERROR: No CSV files found in {BRONZE_DIR}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.utcnow().strftime("%Y%m%d")

    KAGGLE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    access_token_file = KAGGLE_CONFIG_DIR / "access_token"
    config_file = KAGGLE_CONFIG_DIR / "kaggle.json"
    if auth[0] == "token":
        try:
            with open(access_token_file, "w") as f:
                f.write(api_token)
            print(f"Wrote access token to {access_token_file}")
        except Exception as e:
            print(f"Warning: Could not write access token: {e}", file=sys.stderr)
    else:
        config = {"username": username, "key": key}
        try:
            with open(config_file, "w") as f:
                f.write(json.dumps(config))
            config_file.chmod(0o600)
            print(f"Wrote kaggle.json to {config_file}")
        except Exception as e:
            print(f"Warning: Could not write kaggle.json: {e}", file=sys.stderr)

    env = os.environ.copy()
    if auth[0] == "token":
        env["KAGGLE_API_TOKEN"] = api_token
    else:
        env["KAGGLE_USERNAME"] = username
        env["KAGGLE_KEY"] = key
    env["KAGGLE_CONFIG_DIR"] = str(KAGGLE_CONFIG_DIR)

    live = fetch_live_metadata(dataset)

    metadata_path = BRONZE_DIR / METADATA_FILE
    metadata = build_metadata(dataset, live)
    try:
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Wrote {metadata_path}")
    except Exception as e:
        print(f"ERROR: Could not write {METADATA_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    kaggle_exe = find_kaggle()

    print(f"Uploading {len(csv_files)} files to Kaggle dataset: {dataset}")
    print(f"kaggle executable: {kaggle_exe}")

    cmd = [
        kaggle_exe,
        "datasets",
        "version",
        "-p",
        str(BRONZE_DIR),
        "-m",
        f"F1 dataset {timestamp}",
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("Upload successful!")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed (returncode {e.returncode}):", file=sys.stderr)
        print(f"STDOUT: {e.stdout}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        if metadata_path.exists():
            metadata_path.unlink()
            print(f"Removed {metadata_path}")


if __name__ == "__main__":
    main()
