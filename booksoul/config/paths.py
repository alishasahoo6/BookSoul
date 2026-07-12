"""
Filesystem paths used by BookSoul.

Defines the core directory structure and data paths used for database storage,
local caches, and configuration settings.
"""

from pathlib import Path

PACKAGE_ROOT: Path = Path(__file__).resolve().parents[1]
PROJECT_ROOT: Path = PACKAGE_ROOT.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
LEGACY_LKRE_CACHE_PATH: Path = PROJECT_ROOT / "lkre_cache.json"
LKRE_CACHE_PATH: Path = DATA_DIR / "lkre_cache.json"
CHROMA_DATA_PATH: Path = PROJECT_ROOT / "chroma_db"


