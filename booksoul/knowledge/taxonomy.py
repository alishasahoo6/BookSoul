"""
Single source of truth for reusable BookSoul taxonomy strings.

The registries are intentionally data-only in Phase 2. Existing generators keep
their behavior unchanged, and future phases can migrate duplicated strings here.
"""

from typing import Dict, Any

GENRES: Dict[str, str] = {
    "romance": "Romance",
    "dark_romance": "Dark Romance",
    "fantasy": "Fantasy",
    "mystery": "Mystery",
    "thriller": "Thriller",
    "sci_fi": "Sci-Fi",
    "historical": "Historical Fiction",
    "horror": "Horror",
    "young_adult": "Young Adult",
    "nonfiction": "Non-fiction",
}

THEMES: Dict[str, Any] = {}
TROPES: Dict[str, Any] = {}
CHARACTER_ARCHETYPES: Dict[str, Any] = {}
RELATIONSHIP_DYNAMICS: Dict[str, Any] = {}
WORLD_TYPES: Dict[str, Any] = {}
ATMOSPHERES: Dict[str, Any] = {}
READER_INTENTS: Dict[str, Any] = {}
CONTENT_FLAGS: Dict[str, Any] = {}


