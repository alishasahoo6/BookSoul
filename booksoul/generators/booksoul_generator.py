"""
BookSoul Generator — Deterministic Rule-Based Implementation.

All Gemini API calls have been removed.
The rule-based engine (rule_based_booksoul.py) is now the sole source of
BookSoul profiles. Public API is preserved exactly.
"""

from typing import Dict, Any, Union, List
from booksoul.common.utils import setup_logger
from booksoul.models.book_dna import ensure_book_dna

logger = setup_logger("BookSoulGenerator")


def generate_local_fallback_soul(title: str, description: str, categories: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Delegates to the modular rule-based BookSoul engine.
    """
    from booksoul.generators.rule_based_booksoul import generate_book_soul
    
    book_categories = categories
    if isinstance(categories, str):
        book_categories = [c.strip() for c in categories.split(",") if c.strip()]
    elif not isinstance(categories, list):
        book_categories = []
        
    book = {
        "title": title,
        "description": description,
        "categories": book_categories,
    }
    return generate_book_soul(book)


def generate_booksoul(book_title: str, book_description: str, categories: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Generates the structured BookSoul representation with DNA attributes.

    Fully deterministic — uses heuristic genre/keyword matching.
    Output schema is identical to the previous Gemini-backed implementation.
    """
    logger.info("Generating rule-based soul for '%s'", book_title)
    soul = generate_local_fallback_soul(book_title, book_description, categories)
    if not soul:
        logger.warning("Rule-based engine returned empty soul for '%s'", book_title)
        soul = {}

    ensure_book_dna(
        soul,
        description=book_description,
        categories=categories.split(", ") if isinstance(categories, str) else (categories or []),
    )
    return soul

