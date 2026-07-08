"""Filesystem paths used by BookSoul."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
LEGACY_LKRE_CACHE_PATH = PROJECT_ROOT / "lkre_cache.json"
LKRE_CACHE_PATH = DATA_DIR / "lkre_cache.json"
CHROMA_DATA_PATH = PROJECT_ROOT / "chroma_db"

