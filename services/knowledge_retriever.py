from services.google_books import fetch_book_info
from services.openlibrary import fetch_openlibrary_book
from services.cache import get_cached_book, set_cached_book   
from services.wikipedia import fetch_wikipedia_summary

def get_book(query):
    """
    Live Knowledge Retrieval Engine (LKRE) Orchestrator with Local Caching.
    Checks cache first, then defaults to Google Books -> Open Library.
    """
    print(f"\n⚡ [LKRE] Dispatching Search Request for: '{query}'")
    
    # 1. Check local file cache
    cached_data = get_cached_book(query)
    if cached_data:
        print("✅ [LKRE] Serving immediate match from local cache.")
        return cached_data
        
    # 2. Primary Attempt: Google Books
    print("🔍 [LKRE] Cache Miss. Route 1: Checking Google Books API...")
    book_data = fetch_book_info(query)
    if book_data:
        print("✅ [LKRE] Primary Match Confirmed via Google Books.")
        set_cached_book(query, book_data)  # Save to cache
        return book_data
        
    # 3. Fallback Route: Open Library API
    print("⚠️ [LKRE] Route 1 Failed. Route 2: Falling back to Open Library API...")
    book_data = fetch_openlibrary_book(query)
    if book_data:
        print("✅ [LKRE] Fallback Match Confirmed via Open Library.")
        set_cached_book(query, book_data)  # Save to cache
        return book_data
    
    print("📚 [LKRE] Route 3: Checking Wikipedia...")

    wiki_data = fetch_wikipedia_summary(query)

    if wiki_data:
        # Bug A fix: Normalize Wikipedia's unique schema to the standard book format
        book_data = {
            "title": wiki_data.get("title", query),
            "description": wiki_data.get("extract", ""),
            "cover_image": None,
            "authors": [],
            "categories": [],
            "published_year": "N/A"
        }
        print("✅ [LKRE] Match confirmed via Wikipedia.")
        set_cached_book(query, book_data)
        return book_data
        
    print("❌ [LKRE] All retrieval nodes exhausted. No book data recovered.")
    return None