"""
World and setting type registry.

Maps to the shared single source of truth in the taxonomy module.
"""

from typing import Dict, Any
from booksoul.knowledge.taxonomy import WORLD_TYPES

REGISTRY: Dict[str, Any] = WORLD_TYPES


