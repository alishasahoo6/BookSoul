"""
Book Retriever Orchestrator.

Handles search and candidate fetching from Google Books.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from booksoul.common.utils import setup_logger, request_with_retry

load_dotenv()

logger = setup_logger("BookRetriever")


def search_with_subject_filters(
    query: str,
    subject_filters: Optional[List[str]] = None,
    max_results: int = 40
) -> List[Dict[str, Any]]:
    """
    Search Google Books with subject filters and proper query construction.
    
    Args:
        query: The search term(s)
        subject_filters: List of subject filters (e.g., ["fiction", "romance"])
        max_results: Number of results to request (30-50 for candidates)
    
    Returns:
        List of normalized book dictionaries
    """
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    url = "https://www.googleapis.com/books/v1/volumes"
    
    try:
        # Build advanced query with subject filters
        query_parts = [f'"{query}"']  # Quote the main query for exact matching
        
        if subject_filters:
            # Add subject filters
            for subject in subject_filters:
                query_parts.append(f'subject:{subject}')
        
        full_query = " ".join(query_parts)
        
        logger.info("Query: %s", full_query)
        
        params = {
            "q": full_query,
            "maxResults": max_results,
            "printType": "books"
        }
        
        if api_key:
            params["key"] = api_key
        else:
            logger.warning("No API key. Rate limits may apply.")
        
        response = request_with_retry("GET", url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get("items", []):
            try:
                book = _normalize_volume(item.get("volumeInfo", {}))
                books.append(book)
            except Exception as e:
                logger.error("Error normalizing item: %s", str(e))
                continue
        
        logger.info("Retrieved %d books for query: %s", len(books), query)
        return books
    
    except Exception:
        logger.exception("Error searching with subject filters")
        return []


def search_by_title(title: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search Google Books by exact book title.
    Used for BOOK_QUERY type.
    """
    return search_with_subject_filters(
        query=title,
        subject_filters=["fiction"],
        max_results=max_results
    )


def search_by_author(author: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Search Google Books by author name.
    Used for AUTHOR_QUERY type.
    """
    query = f'inauthor:"{author}"'
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    url = "https://www.googleapis.com/books/v1/volumes"
    
    try:
        params = {
            "q": query,
            "maxResults": max_results,
            "printType": "books"
        }
        
        if api_key:
            params["key"] = api_key
        
        response = request_with_retry("GET", url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get("items", []):
            try:
                book = _normalize_volume(item.get("volumeInfo", {}))
                books.append(book)
            except Exception:
                continue
        
        logger.info("Retrieved %d books by author: %s", len(books), author)
        return books
    
    except Exception:
        logger.exception("Author search error")
        return []


def search_by_mood(
    search_terms: List[str],
    genres: Optional[List[str]] = None,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Search Google Books using mood/vibe search terms with subject filtering.
    Used for MOOD_QUERY type.
    
    Args:
        search_terms: List of search phrases
        genres: List of genre subjects to filter by
        max_results: Number of results per search term
    
    Returns:
        Merged list of unique books from all search terms
    """
    if not genres:
        genres = ["fiction"]
    
    all_books = []
    seen_titles = set()
    
    for search_term in search_terms:
        logger.info("Searching mood query: %s", search_term)
        books = search_with_subject_filters(
            query=search_term,
            subject_filters=genres,
            max_results=max_results
        )
        
        for book in books:
            # Deduplicate by title
            title_key = book["title"].lower()
            if title_key not in seen_titles:
                all_books.append(book)
                seen_titles.add(title_key)
    
    logger.info("Total unique books from mood search: %d", len(all_books))
    return all_books


def _normalize_volume(volume_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Google Books volumeInfo to standard format.
    """
    images = volume_info.get("imageLinks", {})
    cover_url = images.get("thumbnail") or images.get("smallThumbnail") or ""
    pub_date = volume_info.get("publishedDate", "N/A")
    
    return {
        "title": volume_info.get("title", "Unknown Title"),
        "authors": volume_info.get("authors", ["Unknown Author"]),
        "description": volume_info.get("description", "No description available."),
        "categories": volume_info.get("categories", ["Uncategorized"]),
        "published_year": pub_date[:4] if len(pub_date) >= 4 else "N/A",
        "cover_image": cover_url,
        "page_count": volume_info.get("pageCount", 0),
        "publisher": volume_info.get("publisher", ""),
        "isbn": volume_info.get("industryIdentifiers", [{}])[0].get("identifier", "")
    }
