import json


def compute_hybrid_score(book, user_query):
    """
    Hybrid recommendation score.

    Returns:
        score (0-100)
    """

    distance = book.get("distance_score", 1.0)

    # convert distance into similarity
    score = (2 - distance) * 50

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
    
    score = max(0, min(score, 100))

    return round(score, 2)

    