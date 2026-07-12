"""
Shared defaults for genre rule registries.

Defines the default schema keys and default scores for BookSoul entities.
"""

from typing import Dict, Any

BOOKSOUL_SCHEMA_DEFAULTS: Dict[str, Any] = {
    "themes": [],
    "tropes": [],
    "emotional_tone": "Unknown",
    "writing_style": "Unknown",
    "pacing": "Unknown",
    "character_dynamics": "Unknown",
    "reader_vibe": "Unknown",
    "emotional_arc": "Unknown",
    "dna": {
        "emotional_depth": 5,
        "comfort": 5,
        "humor": 5,
        "angst": 5,
        "spice": 5,
        "character_growth": 5,
        "pacing": 5,
        "atmosphere": "Balanced",
    },
}


