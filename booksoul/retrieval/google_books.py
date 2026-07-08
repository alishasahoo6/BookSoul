import os
import requests
from dotenv import load_dotenv

# Ensure environment variables are loaded up front
load_dotenv()

def _normalize_volume(volume_info):
    """Shared helper: convert a Google Books volumeInfo dict into our standard format."""
    images = volume_info.get("imageLinks", {})
    cover_url = images.get("thumbnail") or images.get("smallThumbnail") or ""
    pub_date = volume_info.get("publishedDate", "N/A")
    return {
        "title": volume_info.get("title", "Unknown Title"),
        "authors": volume_info.get("authors", ["Unknown Author"]),
        "description": volume_info.get("description", "No narrative synopsis profile recorded."),
        "categories": volume_info.get("categories", ["Uncategorized"]),
        "published_year": pub_date[:4] if len(pub_date) >= 4 else "N/A",
        "cover_image": cover_url,
        "page_count": volume_info.get("pageCount", 0),
        "publisher": volume_info.get("publisher", "")
    }

def _get_api_params(query, max_results=1):
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    params = {"q": query.strip(), "maxResults": max_results, "printType": "books"}
    if api_key:
        params["key"] = api_key
    else:
        print("[Google Books] Warning: No API key set. Rate limits may apply.")
    return params

from booksoul.common.utils import request_with_retry

def fetch_book_info(query):
    """
    Fetches the single best-matching book from Google Books for a query.
    """
    url = "https://www.googleapis.com/books/v1/volumes"
    try:
        print(f"[LKRE - Google Books] Querying: '{query}'")
        response = request_with_retry("GET", url, params=_get_api_params(query, max_results=5), timeout=10)
        print(f"[LKRE - Google Books] Status Code: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        if "items" not in data or len(data["items"]) == 0:
            print("[LKRE - Google Books] No records returned.")
            return None

        best_book = None
        best_score = -1

        for item in data["items"]:
            vi = item.get("volumeInfo", {})
            score = 0

            title = vi.get("title", "").lower()
            lang = vi.get("language", "")

            if lang == "en":
                score += 5

            if lang != "en":
                score -= 2

            if query.lower().split(" by ")[0] in title:
                score += 5

            if vi.get("description"):
                score += 4
            if vi.get("imageLinks"):
                score += 2
            if vi.get("categories"):
                score += 2
            if vi.get("authors"):
                score += 1
            if vi.get("pageCount", 0) > 50:
                score += 1

            if score > best_score:
                best_score = score
                best_book = vi

        return _normalize_volume(best_book) if best_book else None
    except Exception as e:
        print(f"[LKRE - Google Books Error]: {e}")
        return None

def search_books(query, max_results=8):
    """
    Searches Google Books for up to max_results books matching a query.
    Returns a list of normalized book dicts (never None).
    Used by the recommender to enrich ChromaDB before semantic search.
    """
    url = "https://www.googleapis.com/books/v1/volumes"
    try:
        print(f"[Google Books Search] Fetching up to {max_results} books for: '{query}'")
        response = request_with_retry("GET", url, params=_get_api_params(query, max_results=max_results), timeout=12)
        response.raise_for_status()
        data = response.json()
        books = []
        for item in data.get("items", []):
            vi = item.get("volumeInfo", {})
            # Skip items without a title or description — they add no value to the index
            if not vi.get("title") or not vi.get("description"):
                continue
            books.append(_normalize_volume(vi))
        print(f"[Google Books Search] Retrieved {len(books)} usable records.")
        return books
    except Exception as e:
        print(f"[Google Books Search Error]: {e}")
        return []

