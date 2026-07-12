"""
Open Library API client.

Fetches volume metadata from Open Library Search API.
"""

from typing import Dict, Any, Optional
from booksoul.common.utils import request_with_retry, setup_logger

logger = setup_logger("OpenLibraryClient")


def fetch_openlibrary_book(query: str) -> Optional[Dict[str, Any]]:
    """
    Queries the Open Library Search API as a secondary source for LKRE.
    Normalizes the returned structure to match our internal BookSoul format.
    """
    url = "https://openlibrary.org/search.json"
    params = {
        "q": query.strip(),
        "limit": 1
    }
    headers = {
        "User-Agent": "BookSoul_LKRE_Engine/1.0 (your_email@example.com)"
    }
    
    try:
        logger.info("Querying: '%s'", query)
        response = request_with_retry("GET", url, params=params, headers=headers, timeout=10)
        logger.info("Status Code: %d", response.status_code)
        
        response.raise_for_status()
        data = response.json()
        
        if "docs" not in data or len(data["docs"]) == 0:
            logger.warning("No docs found for this query.")
            return None
            
        doc = data["docs"][0]
        
        # Open Library stores covers via an explicit ID string. We build the thumbnail URL.
        cover_id = doc.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
        
        fs = doc.get("first_sentence", "")
        if isinstance(fs, list):
            description = fs[0] if fs else ""
        elif isinstance(fs, dict):
            description = fs.get("value", "")
        else:
            description = str(fs) if fs else ""
            
        # Fallback completely if no first sentence fields are recovered
        if not description.strip():
            subjects = doc.get("subject", ["No synopsis profile available."])
            description = f"Subjects / Context: {', '.join(subjects[:5])}"
        else:
            description = f"Synopsis: {description}"
        
        normalized_book = {
            "title": doc.get("title", "Unknown Title"),
            "authors": doc.get("author_name", ["Unknown Author"]),
            "description": description,
            "categories": doc.get("subject", ["Uncategorized"])[:3],
            "published_year": str(doc.get("first_publish_year", "N/A")),
            "cover_image": cover_url,
            "page_count": doc.get("number_of_pages_median", 0),
            "publisher": doc.get("publisher", [""])[0] if doc.get("publisher") else ""
        }
        return normalized_book
        
    except Exception:
        logger.exception("Open Library query failed")
        return None
