"""
Content flag registry.

Maps to the shared single source of truth in the taxonomy module.
"""

from typing import Dict, Any
from booksoul.knowledge.taxonomy import CONTENT_FLAGS

REGISTRY: Dict[str, Any] = CONTENT_FLAGS


