"""
Local search cache management.

Stores and retrieves raw book responses from disk cache to minimize API queries.
"""

import os
import json
from typing import Dict, Any, Optional
from booksoul.config.paths import LEGACY_LKRE_CACHE_PATH, LKRE_CACHE_PATH
from booksoul.common.utils import setup_logger

logger = setup_logger("LKRECache")

CACHE_FILE_PATH = str(LKRE_CACHE_PATH if LKRE_CACHE_PATH.exists() else LEGACY_LKRE_CACHE_PATH)


def _load_cache() -> Dict[str, Any]:
    """Helper to safely read the on-disk cache JSON file into memory."""
    if not os.path.exists(CACHE_FILE_PATH):
        return {}
    try:
        with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Could not parse cache file")
        return {}


def _save_cache(cache_data: Dict[str, Any]) -> None:
    """Helper to commit the in-memory cache back down to the disk file."""
    try:
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception:
        logger.exception("Could not write save out to disk")


def get_cached_book(query: str) -> Optional[Dict[str, Any]]:
    """
    Checks if a normalized variant of the query string is already cached.
    Returns the stored book metadata payload or None.
    """
    normalized_key = query.strip().lower()
    cache = _load_cache()
    
    if normalized_key in cache:
        logger.info("Hit! Found immediate local memory match for '%s'", normalized_key)
        return cache[normalized_key]
    
    return None


def set_cached_book(query: str, book_data: Dict[str, Any]) -> None:
    """Stores a book metadata payload against the normalized search query key."""
    if not book_data:
        return
        
    normalized_key = query.strip().lower()
    cache = _load_cache()
    
    cache[normalized_key] = book_data
    _save_cache(cache)
    logger.info("Saved record for '%s' to local file store.", normalized_key)
