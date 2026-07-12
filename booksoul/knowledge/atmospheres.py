"""
Atmosphere registry.

Maps to the shared single source of truth in the taxonomy module.
"""

from typing import Dict, Any
from booksoul.knowledge.taxonomy import ATMOSPHERES

REGISTRY: Dict[str, Any] = ATMOSPHERES


