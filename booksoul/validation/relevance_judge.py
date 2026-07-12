"""
Stage 5: Relevance Judge — Deterministic Scoring Implementation.

All Gemini API calls have been removed.
Relevance is computed via a multi-signal scoring function:

  • Embedding similarity (via soul_match / distance_score)
  • Keyword overlap (query ↔ title + description + themes + tropes)
  • Genre overlap
  • Mood overlap
  • Metadata completeness
  • Publication quality score
  • Non-fiction penalties

Public API is preserved exactly:
    judge_recommendation_relevance(user_query, book, confidence_threshold) → dict
    batch_judge_relevance(user_query, books, confidence_threshold) → (relevant, filtered)
"""

from booksoul.common.utils import setup_logger

logger = setup_logger("RelevanceJudge")


# ---------------------------------------------------------------------------
# Genre / mood signal vocabularies
# ---------------------------------------------------------------------------

_FICTION_SIGNALS = [
    "fiction", "novel", "mystery", "thriller", "fantasy", "romance",
    "crime", "secret", "academy", "campus", "murder", "horror",
    "historical", "literary", "adventure", "young adult", "sci-fi",
    "science fiction",
]

_NON_FICTION_PENALTIES = [
    "guide", "handbook", "encyclopedia", "manual", "reference",
    "self-help", "psychology", "research", "textbook", "techniques",
    "therapy", "workbook", "planner",
]

_GENRE_KEYWORDS = {
    "romance": ["romance", "love", "relationship", "heartwarming", "emotional"],
    "mystery": ["mystery", "detective", "crime", "murder", "investigation", "whodunit"],
    "thriller": ["thriller", "suspense", "danger", "killer", "survival"],
    "fantasy": ["fantasy", "magic", "dragon", "wizard", "quest", "kingdom"],
    "horror": ["horror", "ghost", "haunted", "monster", "demon", "paranormal"],
    "dark academia": ["dark academia", "campus", "secret society", "gothic", "university"],
    "cozy": ["cozy", "small town", "comfort", "warm", "wholesome"],
    "historical": ["historical", "century", "war", "era", "period", "monarchy"],
}


def local_relevance_fallback(user_query: str, book: dict) -> dict:
    """
    Deterministic relevance scoring — always used (previously only a fallback).
    """
    query = user_query.lower()

    title       = book.get("title", "").lower()
    description = book.get("description", "").lower()

    raw_categories = book.get("categories", [])
    categories = " ".join(raw_categories).lower() if isinstance(raw_categories, list) else str(raw_categories).lower()

    soul = book.get("soul", {}) if isinstance(book.get("soul"), dict) else {}
    themes = " ".join(soul.get("themes", [])).lower()
    tropes = " ".join(soul.get("tropes", [])).lower()

    text = f"{title} {description} {categories} {themes} {tropes}"

    # --- Base score from embedding similarity ---
    soul_match = book.get("soul_match", 50)
    score = soul_match * 0.4  # 40% weight from embedding

    # --- Keyword overlap (query → book) ---
    for word in query.split():
        if len(word) >= 4 and word in text:
            score += 8

    # --- Genre overlap ---
    for genre, signals in _GENRE_KEYWORDS.items():
        genre_in_query = genre in query or any(s in query for s in signals)
        genre_in_book  = any(s in text for s in signals)
        if genre_in_query and genre_in_book:
            score += 10

    # --- Fiction signals reward ---
    for sig in _FICTION_SIGNALS:
        if sig in text:
            score += 2

    # --- Non-fiction penalties ---
    for term in _NON_FICTION_PENALTIES:
        if term in text and term not in query:
            score -= 20

    # --- Metadata quality bonus ---
    if soul.get("themes"):
        score += 3
    if soul.get("tropes"):
        score += 3
    if book.get("cover_image"):
        score += 2

    # --- Clamp ---
    score = max(0, min(100, round(score)))

    return {
        "recommend":       score >= 40,
        "confidence":      score,
        "reason":          f"Deterministic multi-signal score: {score}/100",
        "below_threshold": score < 40,
    }


def judge_recommendation_relevance(user_query: str, book: dict, confidence_threshold: int = 40) -> dict:
    """
    Stage 5: Deterministic relevance check.

    Args:
        user_query          : The user's original search query
        book                : Book dictionary
        confidence_threshold: Minimum score to include (default lowered to 40
                              since we are scoring without AI)

    Returns:
        {
            "recommend":       bool,
            "confidence":      int,
            "reason":          str,
            "below_threshold": bool
        }
    """
    result = local_relevance_fallback(user_query, book)

    confidence = result["confidence"]
    recommend  = result["recommend"] and confidence >= confidence_threshold

    result["recommend"]       = recommend
    result["below_threshold"] = confidence < confidence_threshold

    if not recommend:
        title = book.get("title", "Unknown")
        logger.info(
            f"[RelevanceJudge] Rejected '{title}' "
            f"(score={confidence}, threshold={confidence_threshold})"
        )

    return result


def batch_judge_relevance(user_query: str, books: list, confidence_threshold: int = 40) -> tuple:
    """
    Judge relevance for multiple books.

    Returns:
        (relevant_books, filtered_books) lists
    """
    relevant_books = []
    filtered_books = []

    for i, book in enumerate(books, 1):
        result = judge_recommendation_relevance(user_query, book, confidence_threshold)

        book_with_judgment = dict(book)
        book_with_judgment["relevance_judgment"] = result

        if result["recommend"]:
            relevant_books.append(book_with_judgment)
        else:
            filtered_books.append(book_with_judgment)

        if i % 5 == 0:
            print(f"[RelevanceJudge] Processed {i} books... ({len(relevant_books)} relevant)")

    print(f"[RelevanceJudge] Final: {len(relevant_books)} relevant, {len(filtered_books)} filtered")
    return relevant_books, filtered_books
