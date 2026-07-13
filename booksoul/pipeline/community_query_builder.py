"""
Community Search Query Builder.

Generates optimized search queries for community sites (Goodreads, Reddit, Romance.io, etc.)
when community_mode is enabled.
"""

import re
from typing import List

# ---------------------------------------------------------------------------
# Reusable Search Template Constants
# ---------------------------------------------------------------------------

BOOK_TEMPLATES: List[str] = [
    "books like {book}",
    "site:goodreads.com books like {book}",
    "site:reddit.com books similar to {book}",
    "{genre_phrase} like {book}",
    "books recommended after {book}",
    "site:thestorygraph.com books like {book}"
]

AUTHOR_TEMPLATES: List[str] = [
    "books by {author}",
    "site:goodreads.com books by {author}",
    "site:reddit.com authors like {author}",
    "best books by {author}",
    "site:thestorygraph.com {author}"
]

COMMUNITY_TEMPLATES: List[str] = [
    "best {phrase} books",
    "site:goodreads.com {phrase}",
    "site:reddit.com {phrase} recommendations",
    "site:thestorygraph.com {phrase}"
]

ROMANCE_TEMPLATES: List[str] = [
    "site:romance.io {phrase}"
]


def get_phrase_from_dna(dimensions: dict, fallback_query: str) -> str:
    """Build a descriptive search phrase from extracted Reader DNA/dimensions."""
    genres = [g["value"] for g in dimensions.get("genres", [])]
    tones = [t["value"] for t in dimensions.get("tones", [])]
    settings = [s["value"] for s in dimensions.get("settings", [])]
    tropes = [tr["value"] for tr in dimensions.get("tropes", [])]
    
    parts = []
    if tones:
        parts.append(tones[0])
    if settings:
        parts.append(settings[0])
    if tropes:
        parts.append(tropes[0])
    if genres:
        parts.append(genres[0])
        
    if parts:
        # Standardize space separators and lower case
        return " ".join(parts).lower()
        
    # Fallback to normalized original query
    clean_q = fallback_query.replace("with", "").replace("read", "").strip()
    return re.sub(r'\s+', ' ', clean_q)


def is_romance_query(q_lower: str, dimensions: dict) -> bool:
    """Detect romance queries based on query string, genres, and trope dimensions."""
    if "romance" in q_lower or "love" in q_lower:
        return True
        
    # Check genres
    for g in dimensions.get("genres", []):
        if g["value"].lower() == "romance":
            return True
            
    # Check tropes (romance-related tropes)
    romance_tropes = {
        "romance", "enemies to lovers", "friends to lovers", "slow burn", "fake dating",
        "forced proximity", "second chance", "grumpy sunshine", "single dad", "single mom",
        "marriage of convenience", "age gap", "workplace romance", "sports romance",
        "brother's best friend", "fake marriage", "forced marriage"
    }
    for tr in dimensions.get("tropes", []):
        if tr["value"].lower() in romance_tropes:
            return True
            
    return False


def build_community_queries(original_query: str, dimensions: dict) -> List[str]:
    """
    Generate optimized community search queries from an original query and extracted dimensions.
    
    Args:
        original_query (str): The raw search string entered by the user.
        dimensions (dict): The parsed dimensions (genres, tones, tropes, reference book, etc.)
        
    Returns:
        List[str]: A list of 5-10 search query strings.
    """
    q_lower = original_query.lower()
    queries = []
    
    ref_book = dimensions.get("reference_book", {}).get("value")
    ref_author = dimensions.get("reference_author", {}).get("value")
    
    if ref_book:
        genres = [g["value"] for g in dimensions.get("genres", [])]
        for temp in BOOK_TEMPLATES:
            if "{genre_phrase}" in temp:
                if genres:
                    genre_name = genres[0].lower()
                    g_phrase = genre_name + "s" if not genre_name.endswith("s") else genre_name
                    queries.append(temp.format(genre_phrase=g_phrase, book=ref_book))
                else:
                    queries.append(f"books similar to {ref_book}")
            else:
                queries.append(temp.format(book=ref_book))
                
    elif ref_author:
        for temp in AUTHOR_TEMPLATES:
            queries.append(temp.format(author=ref_author))
            
    else:
        # Build search phrase from DNA
        phrase = get_phrase_from_dna(dimensions, original_query)
        
        # Populate community search queries
        for temp in COMMUNITY_TEMPLATES:
            queries.append(temp.format(phrase=phrase))
            
        # Detect romance to target romance.io
        if is_romance_query(q_lower, dimensions):
            for temp in ROMANCE_TEMPLATES:
                queries.append(temp.format(phrase=phrase))
                
        # Target specific combinations (e.g. dark academia mystery)
        if "dark academia" in q_lower and "mystery" in q_lower:
            queries.append("gothic campus mystery novels")
            queries.append("academic thriller books")
            
    # Deduplicate and limit to 5-10
    seen = set()
    deduped = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped.append(q)
            
    return deduped[:10]
