"""
Query Interpreter — Deterministic Rule-Based Implementation.

All Gemini API calls have been removed.
Query classification and search term generation are handled by:
  - Regex pattern matching for BOOK_QUERY / AUTHOR_QUERY detection
  - Weighted synonym dictionaries for MOOD_QUERY expansion
  - Entity extraction heuristics for book/author titles

Public API is preserved exactly:
    interpret_query(user_query: str) -> dict
"""

import re
from typing import List, Dict, Any, Optional
from booksoul.common.utils import setup_logger
from booksoul.knowledge.synonyms import QUERY_SYNONYMS

logger = setup_logger("QueryInterpreter")


# ---------------------------------------------------------------------------
# Query type constants
# ---------------------------------------------------------------------------

class QueryType:
    BOOK_QUERY: str = "BOOK_QUERY"
    AUTHOR_QUERY: str = "AUTHOR_QUERY"
    MOOD_QUERY: str = "MOOD_QUERY"
    TROPE_QUERY: str = "TROPE_QUERY"
    EMOTION_QUERY: str = "EMOTION_QUERY"


# ---------------------------------------------------------------------------
# Regex patterns for classification
# ---------------------------------------------------------------------------

_BOOK_LIKE_PATTERNS: List[str] = [
    r"\bbooks?\s+like\b",
    r"\bsimilar\s+to\b",
    r"\bif\s+you\s+liked\b",
    r"\bmore\s+like\b(?!.*(?:town|city|place|setting|vibe|feel))",
    r"\bsame\s+(?:vibe|feel|energy)\s+as\b",
    r"\breads?\s+like\b",
    r"\breminds?\s+(?:me\s+)?of\b",
]

_AUTHOR_PATTERNS: List[str] = [
    r"\bbooks?\s+by\b",
    r"\bauthor\s+like\b",
    r"\bwrites?\s+like\b",
    r"\bin\s+the\s+style\s+of\b",
]

# Trope patterns map to MOOD_QUERY with trope search terms
_TROPE_PATTERNS: List[str] = [
    r"\benemies\s+to\s+lovers\b",
    r"\bslow\s+burn\b",
    r"\bfake\s+dating\b",
    r"\bfriends\s+to\s+lovers\b",
    r"\bfound\s+family\b",
    r"\bchosen\s+one\b",
    r"\bdark\s+academia\b",
    r"\bforced\s+proximity\b",
    r"\bsecond\s+chance\b",
    r"\bgrumpy\s+sunshine\b",
    r"\btouched\s+by\s+darkness\b",
]

# Emotion / mood patterns
_EMOTION_PATTERNS: List[str] = [
    r"\bmake\s+me\s+(?:cry|feel|laugh|smile)\b",
    r"\bi\s+(?:need|want|crave)\b",
    r"\bsomething\s+(?:cozy|dark|light|heavy|heartwarming|sad|funny|happy)\b",
    r"\b(?:feel|feeling)\s+\w+\b",
    r"\bin\s+a\s+(?:\w+\s+)?mood\b",
]


# ---------------------------------------------------------------------------
# Fiction scope helpers
# ---------------------------------------------------------------------------

_FICTION_SUFFIXES: List[str] = ["novel", "fiction", "romance", "book", "story", "literary"]

_NON_FICTION_BLOCKLIST: List[str] = [
    "economic development", "business", "guide", "manual", "handbook",
    "textbook", "workbook", "how to", "strategy", "management",
    "policy", "analysis", "report", "study", "research",
]


def _enforce_fiction_scope(terms: List[str], original_query: str) -> List[str]:
    """
    Ensure every search term is fiction-scoped.

    - Drops terms that match non-fiction patterns
    - Appends 'novel' or 'fiction' to bare terms that lack qualifiers
    - Never returns the raw user query alone
    """
    result = []
    for term in terms:
        t = term.lower().strip()

        if any(block in t for block in _NON_FICTION_BLOCKLIST):
            logger.info("Dropped non-fiction term: '%s'", term)
            continue

        if t == original_query.lower().strip():
            continue

        has_qualifier = any(suf in t for suf in _FICTION_SUFFIXES)
        if not has_qualifier:
            term = term.rstrip() + " novel"

        result.append(term)

    if not result:
        logger.warning("All terms dropped — using safe fallback terms.")
        words = original_query.strip().split()[:3]
        base = " ".join(words)
        result = [
            f"{base} fiction novel",
            f"{base} contemporary novel",
            f"heartwarming {base} story",
        ]

    return result[:10]


# ---------------------------------------------------------------------------
# Entity extraction helpers
# ---------------------------------------------------------------------------

_BOOK_LIKE_EXTRACTORS: List[re.Pattern] = [
    re.compile(r"books?\s+like\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"similar\s+to\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"if\s+you\s+liked?\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"more\s+like\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"reads?\s+like\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"reminds?\s+(?:me\s+)?of\s+['\"]?(.+?)['\"]?\s*$", re.I),
    re.compile(r"same\s+(?:vibe|feel|energy)\s+as\s+['\"]?(.+?)['\"]?\s*$", re.I),
]

_AUTHOR_EXTRACTORS: List[re.Pattern] = [
    re.compile(r"books?\s+by\s+(.+?)\s*$", re.I),
    re.compile(r"author\s+like\s+(.+?)\s*$", re.I),
    re.compile(r"writes?\s+like\s+(.+?)\s*$", re.I),
    re.compile(r"in\s+the\s+style\s+of\s+(.+?)\s*$", re.I),
]


def _extract_entity(query: str, query_type: str) -> Optional[str]:
    """Extract the book title or author name from the query string."""
    extractors = (
        _BOOK_LIKE_EXTRACTORS
        if query_type == QueryType.BOOK_QUERY
        else _AUTHOR_EXTRACTORS
    )
    for pattern in extractors:
        m = pattern.search(query)
        if m:
            return m.group(1).strip().strip("'\"")
    return None


# ---------------------------------------------------------------------------
# Pre-classifier
# ---------------------------------------------------------------------------

def _rule_preclass(query: str) -> str:
    """Return a QueryType from regex before any further processing."""
    q = query.lower()

    for pat in _AUTHOR_PATTERNS:
        if re.search(pat, q):
            return QueryType.AUTHOR_QUERY

    for pat in _BOOK_LIKE_PATTERNS:
        if re.search(pat, q):
            return QueryType.BOOK_QUERY

    for pat in _TROPE_PATTERNS:
        if re.search(pat, q):
            return QueryType.TROPE_QUERY

    for pat in _EMOTION_PATTERNS:
        if re.search(pat, q):
            return QueryType.EMOTION_QUERY

    return QueryType.MOOD_QUERY


# ---------------------------------------------------------------------------
# Search term generators
# ---------------------------------------------------------------------------

_GENRE_SEARCH_MAP: Dict[str, List[str]] = {
    "romance":          ["contemporary romance novel", "romantic fiction novel", "love story fiction"],
    "fantasy":          ["fantasy fiction novel", "epic fantasy novel", "magical fantasy story"],
    "mystery":          ["mystery fiction novel", "detective novel", "whodunit fiction"],
    "thriller":         ["thriller fiction novel", "psychological thriller", "suspense novel"],
    "horror":           ["horror fiction novel", "gothic horror story", "dark fiction novel"],
    "science fiction":  ["science fiction novel", "sci-fi fiction novel", "speculative fiction story"],
    "historical":       ["historical fiction novel", "period drama fiction", "historical novel story"],
    "young adult":      ["young adult fiction novel", "ya fiction novel", "teen fiction novel"],
    "literary":         ["literary fiction novel", "contemporary fiction literary", "literary drama novel"],
    "dark academia":    ["dark academia fiction novel", "gothic campus mystery", "literary thriller campus"],
}


def _genre_terms_from_query(query_lower: str) -> List[str]:
    """Generate fiction-scoped search terms based on detected genre keywords."""
    terms = []
    for genre, genre_terms in _GENRE_SEARCH_MAP.items():
        if genre in query_lower:
            terms.extend(genre_terms)
    return terms


def _build_book_query_terms(entity: Optional[str], original_query: str) -> List[str]:
    """Build search terms for a BOOK_QUERY (title-based search)."""
    terms = []
    if entity:
        terms.append(f"{entity} book fiction")
        terms.append(f"books like {entity} novel")
        terms.append(f"similar to {entity} fiction")
        # Add genre-flavored terms based on the entity name itself
        words = entity.lower().split()[:3]
        base = " ".join(words)
        terms.append(f"{base} romance novel")
        terms.append(f"{base} thriller fiction")
    return _enforce_fiction_scope(terms, original_query)


def _build_author_query_terms(entity: Optional[str], original_query: str) -> List[str]:
    """Build search terms for an AUTHOR_QUERY."""
    terms = []
    if entity:
        terms.append(f"{entity} fiction novel")
        terms.append(f"books by {entity}")
        terms.append(f"authors like {entity} novel")
        words = entity.lower().split()[:2]
        base = " ".join(words)
        terms.append(f"{base} contemporary fiction")
        terms.append(f"{base} style romance novel")
    return _enforce_fiction_scope(terms, original_query)


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def interpret_query(user_query: str) -> Dict[str, Any]:
    """Convert a raw user query into structured semantic intent.

    Returns a dict with:
        query_type      : BOOK_QUERY | AUTHOR_QUERY | MOOD_QUERY | TROPE_QUERY | EMOTION_QUERY
        original_query  : str
        extracted_value : str | None   (book title or author name)
        mood            : list[str]
        themes          : list[str]
        settings        : list[str]
        genre           : str
        tone            : str
        character_traits: list[str]
        reader_intent   : str
        search_terms    : list[str]
    """
    query_type = _rule_preclass(user_query)

    logger.info("Classified '%s' → %s", user_query, query_type)

    # ── BOOK_QUERY: extract title, build title-focused search terms ──
    if query_type == QueryType.BOOK_QUERY:
        entity = _extract_entity(user_query, QueryType.BOOK_QUERY)
        search_terms = _build_book_query_terms(entity, user_query)
        return {
            "query_type":       QueryType.BOOK_QUERY,
            "original_query":   user_query,
            "extracted_value":  entity,
            "mood":             [],
            "themes":           [],
            "settings":         [],
            "genre":            "Unknown",
            "tone":             "Unknown",
            "character_traits": [],
            "reader_intent":    f"Books similar to '{entity}'" if entity else user_query,
            "search_terms":     search_terms,
        }

    # ── AUTHOR_QUERY: extract author name ──
    if query_type == QueryType.AUTHOR_QUERY:
        entity = _extract_entity(user_query, QueryType.AUTHOR_QUERY)
        search_terms = _build_author_query_terms(entity, user_query)
        return {
            "query_type":       QueryType.AUTHOR_QUERY,
            "original_query":   user_query,
            "extracted_value":  entity,
            "mood":             [],
            "themes":           [],
            "settings":         [],
            "genre":            "Unknown",
            "tone":             "Unknown",
            "character_traits": [],
            "reader_intent":    f"Books by or similar to author '{entity}'" if entity else user_query,
            "search_terms":     search_terms,
        }

    # ── MOOD / TROPE / EMOTION: use synonym dictionary + genre detection ──
    return _fallback(user_query, query_type)


# ---------------------------------------------------------------------------
# Fallback (now primary) — rule-based mood/trope interpretation
# ---------------------------------------------------------------------------

def _fallback(query: str, hint: str = QueryType.MOOD_QUERY) -> Dict[str, Any]:
    """
    Fully rule-based query expansion.

    Supports MULTIPLE matching concepts instead of stopping at the first match.
    """
    query_lower = query.lower()

    matched_keywords = []
    mood = []
    genres = []
    settings = []
    character_traits = []
    search_terms = []
    reader_intents = []

    # Collect ALL matching concepts from synonym dictionary
    for keyword, data in QUERY_SYNONYMS.items():
        if keyword in query_lower:
            logger.info("Matched keyword: %s", keyword)
            matched_keywords.append(keyword)

            mood.extend(data.get("mood", []))
            genres.extend(data.get("genres", []))
            settings.extend(data.get("settings", []))
            character_traits.extend(data.get("character_traits", []))
            search_terms.extend(data.get("search_terms", []))

            if data.get("reader_intent"):
                reader_intents.append(data["reader_intent"])

    # Also add genre-detected terms
    search_terms.extend(_genre_terms_from_query(query_lower))

    # Remove duplicates while preserving order
    mood             = list(dict.fromkeys(mood))
    genres           = list(dict.fromkeys(genres))
    settings         = list(dict.fromkeys(settings))
    character_traits = list(dict.fromkeys(character_traits))
    search_terms     = list(dict.fromkeys(search_terms))

    if matched_keywords or search_terms:
        search_terms = _enforce_fiction_scope(search_terms, query)
        return {
            "query_type":       hint,
            "original_query":   query,
            "extracted_value":  None,
            "mood":             mood,
            "themes":           [],
            "settings":         settings,
            "genre":            genres[0] if genres else "Unknown",
            "tone":             " & ".join(mood[:2]) if mood else "Unknown",
            "character_traits": character_traits,
            "reader_intent":    " ".join(reader_intents) or query,
            "search_terms":     search_terms,
        }

    # Default fallback if nothing matches at all
    words = query.strip().split()[:3]
    base = " ".join(words)

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
        "search_terms":     [
            f"{base} fiction novel",
            f"{base} contemporary romance",
            f"heartwarming {base} novel",
        ],
    }