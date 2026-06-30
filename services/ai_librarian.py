"""
Stage 3: AI Librarian
Final AI-based validation to ensure books are real narrative works.
"""

import os
import json
import google.generativeai as genai


def validate_book_with_ai(book, confidence_threshold=80):
    """
    Stage 3: Ask Gemini if this is a real narrative book.
    
    This is the SECOND validation layer after BookValidator.
    Even if a book passes initial filtering, Gemini makes the final call.
    
    Args:
        book: Book dictionary
        confidence_threshold: Minimum confidence to accept (0-100)
    
    Returns:
        {
            "valid": bool,
            "type": str,  # Novel, Fiction, Non-fiction, Notebook, etc.
            "confidence": int,  # 0-100
            "reason": str,
            "below_threshold": bool  # True if confidence < threshold
        }
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "valid": True,
            "type": "Unknown",
            "confidence": 100,
            "reason": "Skipped AI validation (No API key)",
            "below_threshold": False
        }
    
    title = book.get("title", "Unknown")
    description = book.get("description", "")
    categories = ", ".join(book.get("categories", []))
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""You are an expert librarian with 20+ years of experience categorizing books.

Determine if this is a REAL NARRATIVE BOOK that someone would read for enjoyment/learning, or whether it is a non-narrative publication like a notebook, journal, or planner.

Title: {title}
Description: {description}
Categories: {categories}

IMPORTANT:
- Notebooks, journals, planners, workbooks, activity books, coloring books, and other consumable/non-narrative items should be marked as NOT valid
- Actual books (novels, fiction, non-fiction, memoir, biography, poetry, etc.) should be marked as valid
- If uncertain, err on the side of rejecting (set lower confidence)

Return JSON ONLY:
{{
    "valid": true or false,
    "type": "Novel / Fiction / Non-Fiction / Memoir / Biography / Poetry / Children's Book / Graphic Novel / Essay Collection / Short Stories / Notebook / Journal / Planner / Workbook / Activity Book / Coloring Book / Other",
    "confidence": 0-100,
    "reason": "Clear explanation of your decision"
}}"""
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        
        confidence = data.get("confidence", 100)
        is_valid = data.get("valid", True) and confidence >= confidence_threshold
        
        result = {
            "valid": is_valid,
            "type": data.get("type", "Unknown"),
            "confidence": confidence,
            "reason": data.get("reason", ""),
            "below_threshold": confidence < confidence_threshold
        }
        
        if not is_valid:
            reason = f"AI Rejection (confidence: {confidence}%)"
            if result["below_threshold"]:
                reason = f"Low AI confidence ({confidence}%, threshold: {confidence_threshold}%)"
            print(f"🚫 [AILibrarian] {reason}: '{title}'")
        
        return result
    
    except Exception as e:
        print(f"[AILibrarian Error] {e}")
        return {
            "valid": True,
            "type": "Unknown",
            "confidence": 100,
            "reason": f"Error calling AI: {e}",
            "below_threshold": False
        }


def batch_validate_books(books, confidence_threshold=80):
    """
    Validate multiple books and return only valid ones.
    
    Args:
        books: List of book dictionaries
        confidence_threshold: Minimum confidence
    
    Returns:
        (valid_books, rejected_books) tuples with metadata
    """
    valid_books = []
    rejected_books = []
    
    for i, book in enumerate(books, 1):
        result = validate_book_with_ai(book, confidence_threshold)
        
        book_with_validation = dict(book)
        book_with_validation["ai_validation"] = result
        
        if result["valid"]:
            valid_books.append(book_with_validation)
        else:
            rejected_books.append(book_with_validation)
        
        if i % 10 == 0:
            print(f"[AILibrarian] Processed {i} books... ({len(valid_books)} valid)")
    
    print(f"[AILibrarian] Final: {len(valid_books)} valid, {len(rejected_books)} rejected")
    return valid_books, rejected_books
