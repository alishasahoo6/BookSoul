"""
Live Knowledge Retrieval Engine (LKRE) Orchestrator.

Checks local file cache first, then queries Google Books, Open Library, or Wikipedia.
"""

from typing import Dict, Any, Optional
from booksoul.retrieval.google_books import fetch_book_info
from booksoul.retrieval.openlibrary import fetch_openlibrary_book
from booksoul.retrieval.cache import get_cached_book, set_cached_book
from booksoul.retrieval.wikipedia import fetch_wikipedia_summary
from booksoul.common.utils import setup_logger

logger = setup_logger("LKRE")


def get_book(query: str) -> Optional[Dict[str, Any]]:
    """
    Live Knowledge Retrieval Engine (LKRE) Orchestrator with Local Caching.
    Checks cache first, then defaults to Google Books -> Open Library.
    """
    logger.info("Dispatching Search Request for: '%s'", query)
    
    # 1. Check local file cache
    cached_data = get_cached_book(query)
    if cached_data:
        logger.info("Serving immediate match from local cache.")
        return cached_data
        
    # 2. Primary Attempt: Google Books
    logger.info("Cache Miss. Route 1: Checking Google Books API...")
    book_data = fetch_book_info(query)
    if book_data:
        logger.info("Primary Match Confirmed via Google Books.")
        set_cached_book(query, book_data)  # Save to cache
        return book_data
        
    # 3. Fallback Route: Open Library API
    logger.info("Route 1 Failed. Route 2: Falling back to Open Library API...")
    book_data = fetch_openlibrary_book(query)
    if book_data:
        logger.info("Fallback Match Confirmed via Open Library.")
        set_cached_book(query, book_data)  # Save to cache
        return book_data
    
    logger.info("Route 3: Checking Wikipedia...")

    wiki_data = fetch_wikipedia_summary(query)

    if wiki_data:
        # Normalize Wikipedia's unique schema to the standard book format
        book_data = {
            "title": wiki_data.get("title", query),
            "description": wiki_data.get("extract", ""),
            "cover_image": None,
            "authors": [],
            "categories": [],
            "published_year": "N/A"
        }
        logger.info("Match confirmed via Wikipedia.")
        set_cached_book(query, book_data)
        return book_data
        
    logger.warning("All retrieval nodes exhausted. No book data recovered.")
    return None
