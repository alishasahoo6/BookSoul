import os
import json

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "../lkre_cache.json")

def _load_cache():
    """Helper to safely read the on-disk cache JSON file into memory."""
    if not os.path.exists(CACHE_FILE_PATH):
        return {}
    try:
        with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[LKRE Cache Warning] Could not parse cache file: {e}")
        return {}

def _save_cache(cache_data):
    """Helper to commit the in-memory cache back down to the disk file."""
    try:
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[LKRE Cache Error] Could not write save out to disk: {e}")

def get_cached_book(query):
    """
    Checks if a normalized variant of the query string is already cached.
    Returns the stored book metadata payload or None.
    """
    normalized_key = query.strip().lower()
    cache = _load_cache()
    
    if normalized_key in cache:
        print(f"⚡ [LKRE Cache] Hit! Found immediate local memory match for '{normalized_key}'")
        return cache[normalized_key]
    
    return None

def set_cached_book(query, book_data):
    """Stores a book metadata payload against the normalized search query key."""
    if not book_data:
        return
        
    normalized_key = query.strip().lower()
    cache = _load_cache()
    
    cache[normalized_key] = book_data
    _save_cache(cache)
    print(f"💾 [LKRE Cache] Saved record for '{normalized_key}' to local file store.")