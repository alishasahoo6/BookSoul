"""
Hybrid Ranker.

Calculates hybrid relevance score combining vector similarity, keyword matching,
metadata features, and quality modifiers.
"""

from typing import Dict, Any
from booksoul.common.utils import setup_logger

logger = setup_logger("HybridRanker")


def compute_hybrid_score(book: Dict[str, Any], user_query: str) -> float:
    """
    Computes a hybrid recommendation score from 0.0 to 100.0.
    
    Combines vector distance, query keyword matching across metadata, 
    specific genre bonuses (e.g. dark academia, mystery), quality scoring,
    and non-fiction keyword penalties.
    """
    distance = book.get("distance_score", 1.0)

    # convert distance into similarity
    score = (2.0 - distance) * 50.0

    query = user_query.lower()

    title = book.get("title", "").lower()
    description = book.get("description", "").lower()

    soul = book.get("soul", {})

    themes = " ".join(soul.get("themes", [])).lower()
    tropes = " ".join(soul.get("tropes", [])).lower()

    text = f"{title} {description} {themes} {tropes}"

    # Reward books containing the important query words
    for word in query.split():
        if len(word) >= 4 and word in text:
            score += 2

    # Strong bonus if themes match
    for word in query.split():
        if word in themes:
            score += 4

    # Strong bonus if tropes match
    for word in query.split():
        if word in tropes:
            score += 4

    # Reward higher-quality books slightly
    quality = book.get("quality_score", 0)

    # Maximum contribution: +10 points
    score += quality * 0.10

    # Dark academia bonus
    if "dark academia" in query:
        if "dark academia" in text:
            score += 6
        if "secret society" in text:
            score += 4
        if "campus" in text:
            score += 3
        if "university" in text:
            score += 3

    # Mystery bonus
    if "mystery" in query:
        mystery_words = [
            "murder",
            "detective",
            "investigation",
            "crime",
            "killer",
            "whodunit",
            "mystery",
        ]
        for word in mystery_words:
            if word in text:
                score += 2

    # Penalties
    penalties = [
        "guide",
        "handbook",
        "encyclopedia",
        "manual",
        "reference",
        "companion",
        "analysis",
        "criticism",
        "television series",
    ]

    for word in penalties:
        if word in text:
            score -= 30
    
    score = max(0.0, min(score, 100.0))

    logger.debug("Computed hybrid score for '%s': %.2f", book.get("title"), score)
    return round(score, 2)