"""
BookSoul Generator — Deterministic Rule-Based Implementation.

All Gemini API calls have been removed.
The rule-based engine (rule_based_booksoul.py) is now the sole source of
BookSoul profiles. Public API is preserved exactly.
"""

from booksoul.common.utils import setup_logger
from booksoul.models.book_dna import ensure_book_dna

logger = setup_logger("BookSoulGenerator")


def generate_local_fallback_soul(title, description, categories):
    """
    Delegates to the modular rule-based BookSoul engine.
    """
    from booksoul.generators.rule_based_booksoul import generate_book_soul
    book = {
        "title": title,
        "description": description,
        "categories": categories,
    }
    return generate_book_soul(book)


def generate_booksoul(book_title, book_description, categories):
    """
    Generates the structured BookSoul representation with DNA attributes.

    Fully deterministic — uses heuristic genre/keyword matching.
    Output schema is identical to the previous Gemini-backed implementation.
    """
    logger.info(f"[BookSoulGenerator] Generating rule-based soul for '{book_title}'")
    soul = generate_local_fallback_soul(book_title, book_description, categories)
    if not soul:
        logger.warning(f"[BookSoulGenerator] Rule-based engine returned empty soul for '{book_title}'")
        soul = {}

    ensure_book_dna(
        soul,
        description=book_description,
        categories=categories.split(", ") if isinstance(categories, str) else (categories or []),
    )
    return soul
