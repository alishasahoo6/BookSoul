import requests
from urllib.parse import quote

def fetch_wikipedia_summary(query):
    """
    Queries the Wikipedia REST API for a clean page summary.
    Fixes Bug 3: URL-encodes raw search strings to prevent spaces from breaking HTTP requests.
    """
    normalized_query = query.strip()
    
    # Clean up common book search terms to increase Wikipedia match accuracy
    # (e.g., matching the actual page title format "Wild_Love_(novel)")
    encoded_query = quote(normalized_query)
    
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
    headers = {
        "User-Agent": "BookSoul_Engine/1.0 (your_email@example.com)"
    }

    try:
        print(f"[LKRE - Wikipedia] Fetching summary for: '{normalized_query}'")
        response = requests.get(url, headers=headers, timeout=5)
        print(f"[LKRE - Wikipedia] Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print(f"[LKRE - Wikipedia] No exact page profile match found for '{normalized_query}'.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        return {
            "title": data.get("title", "Unknown"),
            "extract": data.get("extract", "No snapshot available."),
            "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
        
    except Exception as e:
        print(f"[LKRE - Wikipedia Error]: {e}")
        return None