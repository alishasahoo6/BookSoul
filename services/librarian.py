import os
import json
import google.generativeai as genai
from services.utils import parse_gemini_json, setup_logger

logger = setup_logger("Librarian")

REJECT_KEYWORDS = [
    "notebook", "journal", "planner", "logbook", "log book", "workbook", 
    "activity book", "coloring book", "blank", "prompt journal", 
    "composition notebook", "diary", "sketchbook", "notebook for", 
    "password book", "guest book"
]

def _rule_based_filtering(book):
    """Step 1: Check for banned keywords in metadata."""
    text = " ".join([
        book.get("title", ""),
        book.get("subtitle", ""),
        " ".join(book.get("categories", [])),
        book.get("description", "")
    ]).lower()
    
    for kw in REJECT_KEYWORDS:
        if kw in text:
            return False, f"Rule rejection: contains keyword '{kw}'"
            
    return True, "Passed rule filtering"

def _ai_validation(title, description, categories):
    """Step 3: Ask Gemini to classify the book type."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return True, "Novel", 100, "Skipped AI validation (No API key)"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
You are an experienced librarian.

Determine whether this item is an actual narrative book intended for reading enjoyment or whether it is another type of publication.

Title: {title}
Description: {description}
Categories: {categories}

Possible categories:
* Novel
* Fiction
* Non-fiction
* Biography
* Memoir
* Children's Book
* Graphic Novel
* Poetry
* Notebook
* Journal
* Planner
* Workbook
* Coloring Book
* Activity Book
* Prompt Journal
* Educational Material
* Other

Return JSON only:
{{
"valid": true/false,
"book_type": "...",
"confidence": 0-100,
"reason": "..."
}}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        fallback_data = {"valid": True, "book_type": "Unknown", "confidence": 100, "reason": "Error parsing JSON"}
        data = parse_gemini_json(response.text, fallback=fallback_data)
        
        return data.get("valid", True), data.get("book_type", "Unknown"), data.get("confidence", 100), data.get("reason", "")
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning("Quota exceeded. Falling back to rule-based validation (approving).")
            return True, "Fiction", 100, "Quota exceeded fallback"
            
        logger.error(f"Librarian AI Error: {e}")
        return True, "Unknown", 100, "Error calling AI"

def validate_book(book, threshold=20):
    """
    Validates a book candidate before indexing/recommending.
    Returns (is_valid, reason)
    """
    title = book.get("title", "Unknown")
    
    # ── Step 1: Rule-Based Filtering ──
    passed, rule_reason = _rule_based_filtering(book)
    if not passed:
        print(f"🚫 [Librarian] Rejected '{title}': {rule_reason}")
        return False, 0, rule_reason
        
    score = 0
    
    # ── Step 2: Metadata Validation ──
    desc = book.get("description", "")
    cats = book.get("categories", [])
    cover = book.get("cover_image", "")
    page_count = book.get("page_count", 0)
    publisher = book.get("publisher", "")
    
    if not desc or "No narrative synopsis" in desc or "No synopsis profile" in desc:
        score -= 30
        return False, score, "No description"
    else:
        score += 15
        
    if not cats or "Uncategorized" in cats:
        score -= 20
        return False, score, "No categories"
    else:
        score += 10
        
    if not cover:
        return False, score, "No cover"
    else:
        score += 5
        
    if isinstance(page_count, int) and page_count > 0:
        if page_count < 20:
            cats_text = " ".join(cats).lower()
            # It's okay if it's a children's book
            if "children" not in cats_text and "picture" not in cats_text:
                score -= 15
                
    if publisher:
        score += 5
        
    # ── Step 3: AI Validation ──
    ai_valid, book_type, confidence, ai_reason = _ai_validation(
        title, desc, ", ".join(cats)
    )
    
    if not ai_valid:
        print(f"🚫 [Librarian] AI Rejected '{title}': {ai_reason}")
        return False, score, f"AI rejection: {ai_reason}"
        
    if confidence < 80:
        print(f"🚫 [Librarian] Low AI Confidence '{title}': {confidence}%")
        return False, score, f"Low AI confidence ({confidence}%)"
        
    # ── Step 4: Quality Score Modifiers ──
    bt_lower = book_type.lower()
    if "novel" in bt_lower or "fiction" in bt_lower:
        score += 40
    elif "notebook" in bt_lower:
        score -= 100
    elif "planner" in bt_lower:
        score -= 100
    elif "workbook" in bt_lower:
        score -= 80
        
    if score < threshold:
        print(f"🚫 [Librarian] Low Quality Score for '{title}': {score} (Type: {book_type})")
        return False, score, f"Quality score too low ({score})"
        
    print(f"✅ [Librarian] Approved '{title}' (Score: {score}, Type: {book_type})")
    return True, score, "Passed validation"
