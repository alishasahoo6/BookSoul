"""
Match Reason Generator — Deterministic Template-Based Implementation.

All Gemini API calls have been removed.
Match reasons are generated via parameterised templates derived from BookSoul
metadata. Public API is preserved exactly:

    generate_match_reasons(user_query, book_title, book_description, book_soul)
    → list[str]  (5-6 bullet points prefixed with ✓)
"""

import re
from booksoul.common.utils import setup_logger

logger = setup_logger("MatchReasonGenerator")

# ---------------------------------------------------------------------------
# Mood / trope keyword → template phrases
# ---------------------------------------------------------------------------

_MOOD_PHRASES = {
    "romance":      "Delivers a rich romantic emotional arc",
    "mystery":      "Builds suspenseful mystery with satisfying reveals",
    "thriller":     "Keeps the tension high with propulsive pacing",
    "fantasy":      "Immerses you in a richly built fantastical world",
    "horror":       "Creates an unsettling, atmospheric dread",
    "cozy":         "Offers a warm, comforting reading experience",
    "dark":         "Explores dark, morally complex themes",
    "heartwarming": "Leaves you with a heartwarming sense of hope",
    "emotional":    "Explores deep, emotionally resonant themes",
    "funny":        "Delivers wit and lighthearted humour",
    "historical":   "Transports you to a richly researched historical era",
    "academic":     "Set in an intellectually charged academic atmosphere",
    "spicy":        "Features steamy, passionate romantic tension",
    "healing":      "Offers a gentle, emotionally healing narrative",
    "grief":        "Thoughtfully explores grief and emotional recovery",
}

_TROPE_PHRASES = {
    "enemies to lovers":  "Features the beloved enemies-to-lovers slow burn",
    "slow burn":          "Delivers a satisfying slow-burn romance",
    "fake dating":        "Built around the tension of a fake-dating scenario",
    "friends to lovers":  "Explores the tender transition from friendship to love",
    "found family":       "Celebrates the warmth of found-family bonds",
    "dark academia":      "Steeped in dark-academia atmosphere and intrigue",
    "forced proximity":   "Uses forced proximity to build emotional tension",
    "second chance":      "Gives characters a second chance at love",
    "grumpy sunshine":    "Pairs grumpy and sunshine personalities perfectly",
    "chosen one":         "Follows the classic Chosen One journey",
    "unreliable narrator":"Uses an unreliable narrator for layered suspense",
    "love triangle":      "Navigates the tension of a compelling love triangle",
}


def _extract_query_signals(user_query: str) -> list[str]:
    """Extract mood/trope matches from the user query."""
    q = user_query.lower()
    found = []
    for phrase, template in {**_MOOD_PHRASES, **_TROPE_PHRASES}.items():
        if phrase in q:
            found.append(f"✓ {template}")
    return found


def generate_match_reasons(
    user_query: str,
    book_title: str,
    book_description: str,
    book_soul: dict,
) -> list:
    """
    Generates 5-6 concise bullet points explaining WHY this book matches the query.

    Returns:
        ["✓ Cozy autumn atmosphere", "✓ Emotionally comforting", ...]
    """
    reasons = []

    # 1. Query-signal matches
    query_signals = _extract_query_signals(user_query)
    reasons.extend(query_signals[:2])

    # 2. Reader vibe
    vibe = book_soul.get("reader_vibe", "")
    if vibe and vibe not in ("Unknown", "N/A", ""):
        reasons.append(f"✓ {vibe} reading experience")

    # 3. Emotional tone
    tone = book_soul.get("emotional_tone", "")
    if tone and tone not in ("Unknown", "N/A", ""):
        reasons.append(f"✓ {tone} emotional tone")

    # 4. Themes
    themes = book_soul.get("themes", [])
    if themes:
        short_themes = [t for t in themes if len(t) <= 30][:2]
        if short_themes:
            reasons.append(f"✓ Explores {' & '.join(short_themes)}")

    # 5. Tropes
    tropes = book_soul.get("tropes", [])
    if tropes:
        short_tropes = [t for t in tropes if len(t) <= 30][:2]
        if short_tropes:
            reasons.append(f"✓ Features {' & '.join(short_tropes)}")

    # 6. Writing style
    style = book_soul.get("writing_style", "")
    if style and style not in ("Unknown", "N/A", ""):
        reasons.append(f"✓ {style} narrative style")

    # Pad to at least 4
    fallback_pads = [
        "✓ Strong character development throughout",
        "✓ Matches your requested reading mood",
        "✓ Recommended based on semantic similarity",
        "✓ Well-rated in its genre",
    ]
    pad_idx = 0
    while len(reasons) < 4 and pad_idx < len(fallback_pads):
        if fallback_pads[pad_idx] not in reasons:
            reasons.append(fallback_pads[pad_idx])
        pad_idx += 1

    return reasons[:6]
