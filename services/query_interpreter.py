import os
import re
import google.generativeai as genai
from services.utils import parse_gemini_json, setup_logger

logger = setup_logger("QueryInterpreter")


class QueryType:
    BOOK_QUERY   = "BOOK_QUERY"
    AUTHOR_QUERY = "AUTHOR_QUERY"
    MOOD_QUERY   = "MOOD_QUERY"


# ---------------------------------------------------------------------------
# Rule-based pre-classifier: runs BEFORE Gemini to catch clear patterns
# quickly and reduce latency on obvious queries.
# ---------------------------------------------------------------------------

_BOOK_LIKE_PATTERNS = [
    r"\bbooks? like\b", r"\bsimilar to\b", r"\bif you liked\b",
    r"\bmore like\b(?!.*(?:town|city|place|setting|vibe|feel))",
    r"\bsame (vibe|feel|energy) as\b",
]
_AUTHOR_PATTERNS = [
    r"\bbooks? by\b", r"\bauthor like\b", r"\bwrites like\b",
]


def _rule_preclass(query: str):
    """Return a QueryType hint from regex before hitting Gemini."""
    q = query.lower()
    for pat in _AUTHOR_PATTERNS:
        if re.search(pat, q):
            return QueryType.AUTHOR_QUERY
    for pat in _BOOK_LIKE_PATTERNS:
        if re.search(pat, q):
            return QueryType.BOOK_QUERY
    return QueryType.MOOD_QUERY  # default


# ---------------------------------------------------------------------------
# Gemini-powered full interpreter
# ---------------------------------------------------------------------------

def interpret_query(user_query: str) -> dict:
    """Convert a raw user query into structured semantic intent.

    Returns a dict with:
        query_type      : BOOK_QUERY | AUTHOR_QUERY | MOOD_QUERY
        original_query  : str
        extracted_value : str | None   (book title or author name)
        mood            : list[str]
        themes          : list[str]
        settings        : list[str]    # NEW — distinguishes location vs atmosphere
        genre           : str
        tone            : str
        character_traits: list[str]
        reader_intent   : str          # NEW — what the reader is really after
        search_terms    : list[str]    # fiction-scoped, never raw-query
    """
    hint = _rule_preclass(user_query)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback(user_query, hint)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""You are a senior librarian and book recommendation expert.
A reader typed: "{user_query}"

════════════════════════════════════════════
STEP 1 — CLASSIFY
════════════════════════════════════════════
Classify the query as ONE of:
• BOOK_QUERY   — reader names a specific book title (e.g. "books like Wild Love")
• AUTHOR_QUERY — reader names a specific author (e.g. "books like Emily Henry")
• MOOD_QUERY   — reader describes a feeling, atmosphere, trope, or setting

IMPORTANT RULES:
- "more like small town", "small town vibes", "cozy small town feel" → MOOD_QUERY (atmosphere, NOT a book title)
- "books like Small Town Economic Development" would be BOOK_QUERY only if it's clearly a title
- When in doubt, lean toward MOOD_QUERY

════════════════════════════════════════════
STEP 2 — SEMANTIC INTENT EXTRACTION
════════════════════════════════════════════
For MOOD_QUERY — identify the reader's TRUE emotional intent, not just keywords.
Ask yourself: "What reading EXPERIENCE is this person craving?"

Classify the intent across these dimensions:
• mood         : emotional tone craved (e.g. cozy, healing, heartwarming, dark, witty)
• themes       : narrative themes (e.g. found family, self-discovery, second chances)
• settings     : atmospheric settings — NOT literal geography (e.g. "cozy small town", "rural community", "close-knit neighborhood")
• genre        : specific fiction genre (e.g. Contemporary Romance, Women's Fiction, Cozy Mystery)
• tone         : narrative voice (e.g. warm, humorous, melancholic, whimsical)
• character_traits: what kind of characters (e.g. relatable protagonist, witty banter, ensemble cast)
• reader_intent: ONE sentence describing what the reader is truly after

════════════════════════════════════════════
STEP 3 — SEARCH TERMS (CRITICAL)
════════════════════════════════════════════
Generate 8-10 Google Books search terms that will return FICTION novels.

MANDATORY RULES:
1. NEVER use the raw user query as a search term
2. ALWAYS append "novel", "fiction", "romance", or "book" to make it fiction-specific
3. NEVER use generic terms like "small town" alone — always qualify: "small town romance novel"
4. Focus on EMOTIONAL and ATMOSPHERIC qualifiers, not literal keywords
5. Each term should be something a librarian would search for a NOVEL recommendation

EXAMPLES:
  Query: "something more like small town"
  WRONG: ["small town", "small town economic development"]
  RIGHT: ["small town romance novel", "cozy contemporary romance", "rural community fiction",
          "found family women's fiction", "small town healing romance", "close-knit community novel"]

  Query: "dark academia"
  WRONG: ["dark academia"]
  RIGHT: ["dark academia fiction novel", "gothic college mystery", "literary thriller campus",
          "secret society novel", "atmospheric academic mystery fiction"]

For BOOK_QUERY or AUTHOR_QUERY, generate search terms to find that specific book/author plus similar titles.

════════════════════════════════════════════
OUTPUT — return ONLY valid JSON, no markdown:
════════════════════════════════════════════
{{
    "query_type": "MOOD_QUERY",
    "extracted_value": null,
    "mood": ["cozy", "warm", "healing"],
    "themes": ["found family", "community", "slow life"],
    "settings": ["cozy small town", "rural community", "close-knit neighborhood"],
    "genre": "Contemporary Romance",
    "tone": "Warm and Heartfelt",
    "character_traits": ["relatable protagonist", "ensemble cast"],
    "reader_intent": "A heartwarming story set in a tight-knit community with found family themes",
    "search_terms": [
        "small town romance novel",
        "cozy contemporary romance fiction",
        "found family women's fiction",
        "rural community healing romance",
        "close-knit town heartwarming novel",
        "small town found family fiction",
        "cozy women's fiction community",
        "heartwarming contemporary romance novel"
    ]
}}"""

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        fallback_data = _fallback(user_query, hint)
        data = parse_gemini_json(response.text, fallback=fallback_data)

        # Post-process: ensure search terms are fiction-scoped
        raw_terms = data.get("search_terms", [user_query])
        clean_terms = _enforce_fiction_scope(raw_terms, user_query)

        result = {
            "query_type":      data.get("query_type", hint),
            "original_query":  user_query,
            "extracted_value": data.get("extracted_value"),
            "mood":            data.get("mood", []),
            "themes":          data.get("themes", []),
            "settings":        data.get("settings", []),
            "genre":           data.get("genre", "Unknown"),
            "tone":            data.get("tone", "Unknown"),
            "character_traits":data.get("character_traits", []),
            "reader_intent":   data.get("reader_intent", ""),
            "search_terms":    clean_terms,
        }

        logger.info(f"Type={result['query_type']} | Intent='{result['reader_intent']}'")
        logger.info(f"Search terms: {clean_terms[:4]}")
        return result

    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err:
            logger.warning("Quota exceeded — using rule-based fallback.")
        else:
            logger.error(f"Query interpretation failed: {e}")
        return _fallback(user_query, hint)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FICTION_SUFFIXES = ["novel", "fiction", "romance", "book", "story", "literary"]

_NON_FICTION_BLOCKLIST = [
    "economic development", "business", "guide", "manual", "handbook",
    "textbook", "workbook", "how to", "strategy", "management",
    "policy", "analysis", "report", "study", "research",
]


def _enforce_fiction_scope(terms: list, original_query: str) -> list:
    """Ensure every search term is fiction-scoped.

    - Drops terms that match non-fiction patterns
    - Appends 'novel' or 'fiction' to bare terms that lack qualifiers
    - Never returns the raw user query alone
    """
    result = []
    for term in terms:
        t = term.lower().strip()

        # Drop obviously non-fiction terms
        if any(block in t for block in _NON_FICTION_BLOCKLIST):
            logger.info(f"[ScopeFilter] Dropped non-fiction term: '{term}'")
            continue

        # Drop if it's just the raw query
        if t == original_query.lower().strip():
            continue

        # Append 'novel' if no fiction qualifier present
        has_qualifier = any(suf in t for suf in _FICTION_SUFFIXES)
        if not has_qualifier:
            term = term.rstrip() + " novel"

        result.append(term)

    # Fallback: if everything was dropped, generate safe terms
    if not result:
        logger.warning("[ScopeFilter] All terms dropped — using safe fallback terms.")
        words = original_query.strip().split()[:3]
        base = " ".join(words)
        result = [
            f"{base} fiction novel",
            f"{base} contemporary novel",
            f"heartwarming {base} story",
        ]

    return result[:10]


def _fallback(query: str, hint: str = QueryType.MOOD_QUERY) -> dict:
    """Safe fallback when Gemini is unavailable."""
    words = query.strip().split()[:3]
    base  = " ".join(words)
    return {
        "query_type":       hint,
        "original_query":   query,
        "extracted_value":  None,
        "mood":             [],
        "themes":           [],
        "settings":         [],
        "genre":            "Unknown",
        "tone":             "Unknown",
        "character_traits": [],
        "reader_intent":    "",
        "search_terms": [
            f"{base} fiction novel",
            f"{base} contemporary romance",
            f"heartwarming {base} novel",
        ],
    }
