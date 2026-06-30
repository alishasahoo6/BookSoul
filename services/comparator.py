"""
services/comparator.py
BookSoul Comparison Engine — scores two books across literary dimensions
using rule-based keyword analysis on their description + soul fields.
Zero Gemini dependency.
"""

from services.knowledge_retriever import get_book
from services.book_soul import generate_book_soul

# ──────────────────────────────────────────────
# Dimension definitions
# ──────────────────────────────────────────────
# Each entry: (display_name, icon_type, positive_keywords, negative_keywords)
DIMENSIONS = [
    {
        "name": "Slow Burn",
        "icon": "🔥",
        "type": "star",
        "pos": ["slow burn", "slow-burn", "tension", "unresolved", "simmering",
                "slow", "restraint", "build-up", "waiting", "longing", "pine"],
        "neg": ["fast", "instant", "love at first sight", "immediate"],
    },
    {
        "name": "Emotional Depth",
        "icon": "💜",
        "type": "star",
        "pos": ["heartbreaking", "emotional", "deeply", "raw", "vulnerable",
                "poignant", "moving", "tears", "grief", "loss", "longing",
                "complex", "nuanced", "profound", "resonant"],
        "neg": ["shallow", "surface", "light"],
    },
    {
        "name": "Found Family",
        "icon": "🫂",
        "type": "star",
        "pos": ["found family", "friendship", "community", "belonging", "chosen family",
                "teammates", "crew", "group", "bonds", "loyalty", "together",
                "support", "friends"],
        "neg": ["isolated", "alone", "solitary"],
    },
    {
        "name": "Humor & Wit",
        "icon": "😂",
        "type": "star",
        "pos": ["funny", "humor", "humour", "witty", "comedy", "laugh",
                "banter", "sarcasm", "quirky", "playful", "lighthearted",
                "hilarious", "amusing"],
        "neg": ["serious", "dark", "grim", "somber", "tragic"],
    },
    {
        "name": "Spice",
        "icon": "🌶️",
        "type": "pepper",
        "pos": ["steamy", "spicy", "passionate", "desire", "attraction",
                "explicit", "sensual", "chemistry", "seduction", "heat",
                "erotic", "intimate", "romance"],
        "neg": ["clean", "wholesome", "fade to black", "innocent", "chaste"],
    },
    {
        "name": "World Building",
        "icon": "🌍",
        "type": "star",
        "pos": ["world", "realm", "universe", "magic system", "lore", "mythology",
                "setting", "detailed", "rich world", "immersive", "landscape",
                "fantastical", "world-building", "epic"],
        "neg": ["contemporary", "realistic", "real world", "modern day"],
    },
    {
        "name": "Suspense",
        "icon": "🕵️",
        "type": "star",
        "pos": ["mystery", "thriller", "suspense", "twist", "shocking", "plot twist",
                "unexpected", "secret", "conspiracy", "danger", "stakes",
                "murder", "crime", "investigation"],
        "neg": ["predictable", "cozy", "lighthearted", "no mystery"],
    },
    {
        "name": "Dark Themes",
        "icon": "🖤",
        "type": "star",
        "pos": ["dark", "gritty", "disturbing", "violence", "trauma", "abuse",
                "death", "war", "horror", "grief", "suffering", "bleak",
                "brutal", "dark themes"],
        "neg": ["light", "uplifting", "cozy", "wholesome", "happy"],
    },
    {
        "name": "Pacing",
        "icon": "⚡",
        "type": "star",
        "pos": ["fast-paced", "fast paced", "gripping", "page-turner", "action",
                "propulsive", "quick", "breathless", "non-stop", "addictive"],
        "neg": ["slow", "deliberate", "leisurely", "contemplative", "measured"],
    },
    {
        "name": "Character Depth",
        "icon": "🎭",
        "type": "star",
        "pos": ["complex characters", "well-developed", "flawed", "layered",
                "character-driven", "growth", "arc", "development", "realistic",
                "relatable", "compelling", "multidimensional"],
        "neg": ["flat", "one-dimensional", "cardboard", "clichéd"],
    },
]


def _all_text(book_data: dict, soul: dict) -> str:
    """Combine all indexable text from a book into one lowercase string."""
    parts = [
        book_data.get("description", ""),
        " ".join(book_data.get("categories", [])),
        " ".join(soul.get("themes", [])),
        " ".join(soul.get("tropes", [])),
        soul.get("reader_vibe", ""),
        soul.get("writing_style", ""),
        soul.get("emotional_tone", ""),
        soul.get("pacing", ""),
    ]
    return " ".join(parts).lower()


def _score_dimension(text: str, dim: dict) -> int:
    """Score a single dimension 1-5 based on keyword presence."""
    score = 2  # neutral baseline
    for kw in dim.get("pos", []):
        if kw in text:
            score += 1
    for kw in dim.get("neg", []):
        if kw in text:
            score -= 1
    return max(1, min(5, score))


def _fetch_and_process(title_query: str):
    """Fetch a book via LKRE and generate its soul. Returns (book, soul) or (None, None)."""
    book = get_book(title_query.strip())
    if not book:
        return None, None
    soul = generate_book_soul(book)
    return book, soul


def compare_books(query1: str, query2: str) -> dict:
    """
    Main comparison entry point.

    Returns:
        {
          "book1": { title, authors, cover_image },
          "book2": { title, authors, cover_image },
          "scores": [
              { "name": "Slow Burn", "icon": "🔥", "type": "star",
                "score1": 4, "score2": 3 },
              ...
          ],
          "summary": { winner_count1, winner_count2, verdict }
        }
    """
    print(f"\n⚖️ [Comparator] Comparing: '{query1}' vs '{query2}'")

    book1, soul1 = _fetch_and_process(query1)
    book2, soul2 = _fetch_and_process(query2)

    if not book1:
        return {"error": f"Could not find book: '{query1}'"}
    if not book2:
        return {"error": f"Could not find book: '{query2}'"}

    text1 = _all_text(book1, soul1)
    text2 = _all_text(book2, soul2)

    scores = []
    wins1, wins2 = 0, 0

    for dim in DIMENSIONS:
        s1 = _score_dimension(text1, dim)
        s2 = _score_dimension(text2, dim)
        if s1 > s2:
            wins1 += 1
        elif s2 > s1:
            wins2 += 1
        scores.append({
            "name":   dim["name"],
            "icon":   dim["icon"],
            "type":   dim["type"],
            "score1": s1,
            "score2": s2,
        })

    if wins1 > wins2:
        verdict = f"📖 **{book1['title']}** wins in {wins1} out of {len(DIMENSIONS)} categories."
    elif wins2 > wins1:
        verdict = f"📖 **{book2['title']}** wins in {wins2} out of {len(DIMENSIONS)} categories."
    else:
        verdict = "🤝 It's a tie! Both books are evenly matched across categories."

    return {
        "book1":   book1,
        "soul1":   soul1,
        "book2":   book2,
        "soul2":   soul2,
        "scores":  scores,
        "summary": {
            "wins1":   wins1,
            "wins2":   wins2,
            "verdict": verdict,
        },
    }
