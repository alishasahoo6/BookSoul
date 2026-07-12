"""
Stage 6: AI Critic (Final Validation)
Deterministic replacement — no external AI calls.

Validates whether a recommendation genuinely matches the user's search intent
by scoring keyword overlap between the query and book metadata.
"""


def validate_recommendation(user_query: str, book_title: str, book_description: str):
    """
    Deterministic relevance check: does this book plausibly match the user query?

    Returns:
        (recommended: bool, confidence: int, reason: str)
    """
    query = user_query.lower()
    text = f"{book_title} {book_description}".lower()

    score = 50  # neutral baseline

    # Reward significant query-word overlap
    query_words = [w for w in query.split() if len(w) >= 4]
    for word in query_words:
        if word in text:
            score += 10

    # Reward genre/mood signals present in both query and book
    genre_signals = [
        "romance", "mystery", "thriller", "fantasy", "horror",
        "fiction", "historical", "science fiction", "young adult",
        "literary", "adventure", "crime",
    ]
    for sig in genre_signals:
        if sig in query and sig in text:
            score += 8

    # Reward atmosphere/trope matches
    trope_signals = [
        "dark academia", "enemies to lovers", "slow burn", "found family",
        "cozy", "small town", "coming of age", "second chance",
    ]
    for trope in trope_signals:
        if trope in query and trope in text:
            score += 12

    # Penalise clearly off-genre content
    non_fiction_penalty = [
        "guide", "handbook", "manual", "encyclopedia",
        "textbook", "workbook", "reference",
    ]
    for term in non_fiction_penalty:
        if term in text and term not in query:
            score -= 20

    score = max(0, min(100, score))
    recommended = score >= 40

    reason = (
        f"Keyword-overlap score: {score}/100 "
        f"({'accepted' if recommended else 'rejected'})"
    )
    return recommended, score, reason
