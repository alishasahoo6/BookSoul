"""
Reader intent registry.

Maps to the shared single source of truth in the taxonomy module.
"""

from typing import Dict, Any
from booksoul.knowledge.taxonomy import READER_INTENTS

REGISTRY: Dict[str, Any] = READER_INTENTS


