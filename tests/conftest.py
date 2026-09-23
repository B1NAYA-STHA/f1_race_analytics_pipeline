import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
INGEST_DIR = SRC_DIR / "ingest"
APP_DIR = SRC_DIR / "app"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(INGEST_DIR))
sys.path.insert(0, str(APP_DIR))
