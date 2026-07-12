"""
Wikipedia REST API client.

Fetches page extract summary for a query as a fallback candidate lookup.
"""

from urllib.parse import quote
from typing import Dict, Any, Optional
from booksoul.common.utils import request_with_retry, setup_logger

logger = setup_logger("WikipediaClient")


def fetch_wikipedia_summary(query: str) -> Optional[Dict[str, Any]]:
    """
    Queries the Wikipedia REST API for a clean page summary.
    URL-encodes raw search strings to prevent spaces from breaking HTTP requests.
    """
    normalized_query = query.strip()
    encoded_query = quote(normalized_query)
    
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
    headers = {
        "User-Agent": "BookSoul_Engine/1.0 (your_email@example.com)"
    }

    try:
        logger.info("Fetching summary for: '%s'", normalized_query)
        response = request_with_retry("GET", url, headers=headers, timeout=5)
        logger.info("Status Code: %d", response.status_code)
        
        if response.status_code == 404:
            logger.warning("No exact page profile match found for '%s'.", normalized_query)
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return {
            "title": data.get("title", "Unknown"),
            "extract": data.get("extract", "No snapshot available."),
            "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
        
    except Exception:
        logger.exception("Wikipedia summary fetch failed")
        return None