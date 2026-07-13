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

EXPLICIT_GENRES = {
    "romance": "Romance",
    "fantasy": "Fantasy",
    "mystery": "Mystery",
    "thriller": "Thriller",
    "horror": "Horror",
    "sci-fi": "Sci-Fi",
    "science fiction": "Sci-Fi",
    "historical fiction": "Historical Fiction",
    "historical": "Historical Fiction",
    "young adult": "Young Adult",
    "ya": "Young Adult",
    "nonfiction": "Non-fiction",
    "non-fiction": "Non-fiction",
    "literary": "Literary",
    "dark academia": "Dark Academia"
}

EXPLICIT_TONES = {
    "cozy": "Cozy",
    "warm": "Warm",
    "heartwarming": "Heartwarming",
    "dark": "Dark",
    "heavy": "Heavy",
    "sad": "Sad",
    "funny": "Funny",
    "happy": "Happy",
    "wholesome": "Wholesome",
    "grim": "Grim",
    "somber": "Somber",
    "tragic": "Tragic",
    "tense": "Tense",
    "anxious": "Anxious",
    "dread": "Dread",
    "atmospheric": "Atmospheric",
    "introspective": "Introspective",
    "reflective": "Reflective",
    "poignant": "Poignant"
}

EXPLICIT_SETTINGS = {
    "small town": "Small Town",
    "small-town": "Small Town",
    "campus": "Campus",
    "academy": "Academy",
    "academia": "Academy",
    "academic": "Academy",
    "space": "Space",
    "castle": "Castle",
    "forest": "Forest",
    "rainy": "Rainy",
    "coastal": "Coastal"
}

EXPLICIT_TROPES = {
    "enemies to lovers": "Enemies to Lovers",
    "slow burn": "Slow Burn",
    "fake dating": "Fake Dating",
    "friends to lovers": "Friends to Lovers",
    "found family": "Found Family",
    "chosen one": "Chosen One",
    "forced proximity": "Forced Proximity",
    "second chance": "Second Chance",
    "grumpy sunshine": "Grumpy Sunshine",
    "single dad": "Single Dad",
    "single mom": "Single Mom",
    "marriage of convenience": "Marriage of Convenience",
    "age gap": "Age Gap",
    "workplace romance": "Workplace Romance",
    "sports romance": "Sports Romance",
    "brother's best friend": "Brother's Best Friend",
    "fake marriage": "Fake Marriage",
    "forced marriage": "Forced Marriage"
}

EXPLICIT_INTENTS = {
    "comfort read": "Comfort Read",
    "emotional rollercoaster": "Emotional Rollercoaster",
    "character driven": "Character Driven",
    "character-driven": "Character Driven",
    "plot driven": "Plot Driven",
    "plot-driven": "Plot Driven",
    "atmospheric": "Atmospheric",
    "page turner": "Page Turner",
    "page-turner": "Page Turner",
    "low stakes": "Low Stakes",
    "low-stakes": "Low Stakes",
    "high stakes": "High Stakes",
    "high-stakes": "High Stakes"
}

STRONG_INFERRED = {
    "genres": {
        "magic": "Fantasy",
        "dragon": "Fantasy",
        "witch": "Fantasy",
        "spells": "Fantasy",
        "murder": "Mystery",
        "killer": "Thriller",
        "clue": "Mystery",
        "steamy": "Romance",
        "passionate": "Romance",
        "love": "Romance",
        "spooky": "Horror",
        "gothic": "Horror",
        "ghost": "Horror"
    },
    "tones": {
        "heartfelt": "Warm",
        "gentle": "Cozy",
        "spooky": "Dark",
        "creepy": "Dark"
    },
    "settings": {
        "university": "Academy",
        "college": "Academy"
    },
    "tropes": {
        "enemies": "Enemies to Lovers",
        "banter": "Grumpy Sunshine"
    },
    "intents": {
        "wholesome": "Comfort Read",
        "gripping": "Page Turner",
        "thrilling": "Page Turner"
    }
}

WEAK_INFERRED = {
    "genres": {
        "secret": "Mystery",
        "hidden": "Mystery",
        "future": "Sci-Fi",
        "ai": "Sci-Fi",
        "space": "Sci-Fi",
        "exciting": "Thriller",
        "chase": "Thriller"
    },
    "tones": {
        "cry": "Sad",
        "tears": "Sad",
        "laugh": "Funny"
    },
    "settings": {
        "school": "Academy"
    },
    "tropes": {
        "grumpy": "Grumpy Sunshine",
        "sunshine": "Grumpy Sunshine",
        "fake": "Fake Dating"
    },
    "intents": {
        "grief": "Emotional Rollercoaster",
        "heartbreak": "Emotional Rollercoaster"
    }
}

def generate_combined_search_terms(query_lower: str, dims: dict) -> List[str]:
    """Dynamically combine detected dimensions to generate high-quality search terms."""
    # Cozy Fantasy case
    if "cozy" in query_lower and "fantasy" in query_lower:
        return [
            "cozy fantasy novel",
            "low stakes fantasy",
            "magical cozy fantasy",
            "wholesome fantasy story",
            "cozy magical fiction"
        ]

    # Dark Academia Mystery case
    if "dark academia" in query_lower and "mystery" in query_lower:
        return [
            "dark academia mystery novel",
            "gothic campus mystery",
            "academic thriller",
            "secret society mystery fiction",
            "intellectual campus mystery"
        ]

    # Small-town Romance with Found Family
    if "small-town" in query_lower or "small town" in query_lower:
        if "romance" in query_lower:
            terms = ["small-town romance novel"]
            if "found family" in query_lower:
                terms.extend(["found family romance", "small-town romance with found family", "cozy small-town romance"])
            return terms

    # Dynamic fallback combination
    genres_list = [g["value"] for g in dims.get("genres", [])]
    tones_list = [t["value"] for t in dims.get("tones", [])]
    settings_list = [s["value"] for s in dims.get("settings", [])]
    tropes_list = [tr["value"] for tr in dims.get("tropes", [])]

    combined = []
    if tones_list and genres_list:
        t = tones_list[0].lower()
        g = genres_list[0].lower()
        combined.append(f"{t} {g} novel")
        combined.append(f"atmospheric {t} {g} story")
    if settings_list and genres_list:
        s = settings_list[0].lower()
        g = genres_list[0].lower()
        combined.append(f"{s} {g} novel")
    if tropes_list and genres_list:
        tr = tropes_list[0].lower()
        g = genres_list[0].lower()
        combined.append(f"{tr} {g} fiction")

    return combined

def extract_dimensions(query: str) -> dict:
    q_lower = query.lower()
    dimensions = {}

    # 1. Reference Book
    for pattern in _BOOK_LIKE_EXTRACTORS:
        m = pattern.search(query)
        if m:
            dimensions["reference_book"] = {"value": m.group(1).strip().strip("'\"")}
            break

    # 2. Reference Author
    for pattern in _AUTHOR_EXTRACTORS:
        m = pattern.search(query)
        if m:
            dimensions["reference_author"] = {"value": m.group(1).strip().strip("'\"")}
            break

    # Helper to collect with confidence
    def collect_dimension(explicit_map, strong_map, weak_map):
        results = []
        # Explicit (1.0)
        for kw, val in explicit_map.items():
            if kw in q_lower:
                if not any(r["value"] == val for r in results):
                    results.append({"value": val, "confidence": 1.0})
        # Strong Inferred (0.8)
        for kw, val in strong_map.items():
            if kw in q_lower:
                if not any(r["value"] == val for r in results):
                    results.append({"value": val, "confidence": 0.8})
        # Weak Inferred (0.6)
        for kw, val in weak_map.items():
            if kw in q_lower:
                if not any(r["value"] == val for r in results):
                    results.append({"value": val, "confidence": 0.6})
        return results

    # 3. Genre
    genres = collect_dimension(EXPLICIT_GENRES, STRONG_INFERRED["genres"], WEAK_INFERRED["genres"])
    if genres:
        dimensions["genres"] = genres

    # 4. Tone
    tones = collect_dimension(EXPLICIT_TONES, STRONG_INFERRED["tones"], WEAK_INFERRED["tones"])
    if tones:
        dimensions["tones"] = tones

    # 5. Setting
    settings = collect_dimension(EXPLICIT_SETTINGS, STRONG_INFERRED["settings"], WEAK_INFERRED["settings"])
    if settings:
        dimensions["settings"] = settings

    # 6. Tropes
    tropes = collect_dimension(EXPLICIT_TROPES, STRONG_INFERRED["tropes"], WEAK_INFERRED["tropes"])
    if tropes:
        dimensions["tropes"] = tropes

    # 7. Intents / Reader Vibes
    intents = collect_dimension(EXPLICIT_INTENTS, STRONG_INFERRED["intents"], WEAK_INFERRED["intents"])
    if intents:
        dimensions["intents"] = intents

    # 8. Dedicated Pacing
    pacing_val = None
    pacing_conf = 0.0
    if "slow burn" in q_lower or "slow-burn" in q_lower:
        pacing_val, pacing_conf = "Slow Burn", 1.0
    elif "fast paced" in q_lower or "fast-paced" in q_lower:
        pacing_val, pacing_conf = "Fast Paced", 1.0
    elif "moderate" in q_lower or "moderate-paced" in q_lower or "moderate pace" in q_lower:
        pacing_val, pacing_conf = "Moderate", 1.0
    elif any(kw in q_lower for kw in ["page turner", "page-turner", "gripping", "thrilling"]):
        pacing_val, pacing_conf = "Fast Paced", 0.8
    elif any(kw in q_lower for kw in ["slow", "deliberate"]):
        pacing_val, pacing_conf = "Slow Burn", 0.8
    elif any(kw in q_lower for kw in ["chase", "action"]):
        pacing_val, pacing_conf = "Fast Paced", 0.6
        
    if pacing_val:
        dimensions["pacing"] = {"value": pacing_val, "confidence": pacing_conf}

    return dimensions

def check_community_mode(query: str, query_type: str, dims: dict) -> bool:
    """Determine if query matches community recommendations, author searches, tropes, or mood/vibe criteria."""
    q = query.lower().strip()
    
    # 1. books like <title>
    has_book_like_pattern = any(re.search(pat, q) for pat in _BOOK_LIKE_PATTERNS)
    
    # 2. books by <author>
    has_author_pattern = any(re.search(pat, q) for pat in _AUTHOR_PATTERNS)
    
    # 3. Trope searches (has explicit tropes or strong/weak trope matches)
    has_trope = "tropes" in dims
    
    # 4. Mood/vibe searches (has genres, tones, settings, intents, or pacing)
    has_mood_or_vibe = "genres" in dims or "tones" in dims or "settings" in dims or "intents" in dims or "pacing" in dims
    
    return bool(has_book_like_pattern or has_author_pattern or has_trope or has_mood_or_vibe)

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
        dimensions      : dict
        community_mode  : bool
    """
    query_type = _rule_preclass(user_query)

    logger.info("Classified '%s' → %s", user_query, query_type)
    dims = extract_dimensions(user_query)
    comm_mode = check_community_mode(user_query, query_type, dims)

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
            "dimensions":       dims,
            "community_mode":   comm_mode,
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
            "dimensions":       dims,
            "community_mode":   comm_mode,
        }

    # ── MOOD / TROPE / EMOTION: use synonym dictionary + genre detection ──
    return _fallback(user_query, query_type, dims, comm_mode)


# ---------------------------------------------------------------------------
# Fallback (now primary) — rule-based mood/trope interpretation
# ---------------------------------------------------------------------------

def _fallback(query: str, hint: str = QueryType.MOOD_QUERY, dims: dict = None, comm_mode: bool = None) -> Dict[str, Any]:
    """
    Fully rule-based query expansion.

    Supports MULTIPLE matching concepts instead of stopping at the first match.
    """
    query_lower = query.lower()
    if dims is None:
        dims = extract_dimensions(query)
    if comm_mode is None:
        comm_mode = check_community_mode(query, hint, dims)

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

    # Prepend combined search terms
    comb_terms = generate_combined_search_terms(query_lower, dims)
    search_terms = comb_terms + search_terms

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
            "dimensions":       dims,
            "community_mode":   comm_mode,
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
        "dimensions":       dims,
        "community_mode":   comm_mode,
    }