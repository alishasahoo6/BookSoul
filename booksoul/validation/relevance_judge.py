"""
Stage 5: Relevance Judge
Final AI-based check: Would a reader actually enjoy this recommendation?
"""

import os
import json
import google.generativeai as genai
from booksoul.common.utils import parse_gemini_json, setup_logger

logger = setup_logger("RelevanceJudge")

 
def local_relevance_fallback(user_query, book):
    """
    Local relevance scoring when Gemini quota is exhausted.
    """

    query = user_query.lower()

    title = book.get("title", "").lower()
    description = book.get("description", "").lower()
    raw_categories = book.get("categories", [])

    if isinstance(raw_categories, list):
        categories = " ".join(raw_categories).lower()
    else:
        categories = str(raw_categories).lower()

    text = f"{title} {description} {categories}"

    score = 0

    # Reward matching important query words
    for word in query.split():
        if len(word) >= 4 and word in text:
            score += 20

    # Reward fiction signals
    fiction_words = [
        "fiction",
        "novel",
        "mystery",
        "thriller",
        "fantasy",
        "romance",
        "crime",
        "secret",
        "academy",
        "campus",
        "murder",
    ]

    for word in fiction_words:
        if word in text:
            score += 5

    # Penalize obvious non-fiction
    non_fiction_words = [
        "guide",
        "handbook",
        "encyclopedia",
        "manual",
        "reference",
        "self-help",
        "psychology",
        "research",
        "textbook",
        "techniques",
        "therapy",
    ]

    for word in non_fiction_words:
        if word in text:
            score -= 25

    score = max(0, min(score, 100))

    return {
        "recommend": score >= 40,
        "confidence": score,
        "reason": "Local relevance fallback",
        "below_threshold": score < 40,
    }
def judge_recommendation_relevance(user_query, book, confidence_threshold=85):
    """
    Stage 5: Final AI-based relevance check.
    
    Even if a book is valid and semantically ranked high, we do a final sanity check:
    "Would a reader searching for '{user_query}' actually enjoy this book?"
    
    Args:
        user_query: The user's original query
        book: Book dictionary
        confidence_threshold: Minimum confidence to include (0-100)
    
    Returns:
        {
            "recommend": bool,
            "confidence": int,  # 0-100
            "reason": str,
            "below_threshold": bool
        }
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "recommend": True,
            "confidence": 100,
            "reason": "Skipped AI validation (No API key)",
            "below_threshold": False
        }
    
    title = book.get("title", "Unknown")
    description = book.get("description", "")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""You are an expert book recommendation specialist.

A reader searched for:
"{user_query}"

Would they actually be delighted to receive this book as a recommendation?

Book Title: {title}
Book Description: {description}

Consider:
- Is this book relevant to the search query?
- Would it genuinely satisfy the reader's request?
- Is this a good match or just surface-level relevance?

Return JSON ONLY:
{{
    "recommend": true or false,
    "confidence": 0-100,
    "reason": "Brief explanation of your assessment"
}}"""
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        fallback_data = {"recommend": True, "confidence": 100, "reason": "Error parsing JSON"}
        data = parse_gemini_json(response.text, fallback=fallback_data)
        
        confidence = data.get("confidence", 100)
        recommend = data.get("recommend", False) and confidence >= confidence_threshold
        
        result = {
            "recommend": recommend,
            "confidence": confidence,
            "reason": data.get("reason", ""),
            "below_threshold": confidence < confidence_threshold
        }
        
        if not recommend:
            reason = "Rejected by Relevance Judge"
            if result["below_threshold"]:
                reason = f"Low relevance confidence ({confidence}%, threshold: {confidence_threshold}%)"
            logger.info(f"Rejected by Relevance Judge: '{title}' - {reason}")
        
        return result
    
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning("Quota exceeded. Using local relevance fallback.")
            return local_relevance_fallback(user_query, book)
        logger.error(f"Error calling AI: {e}")
        return {
            "recommend": True,
            "confidence": 100,
            "reason": f"Error calling AI: {e}",
            "below_threshold": False
        }


def batch_judge_relevance(user_query, books, confidence_threshold=85):
    """
    Judge relevance for multiple books.
    
    Args:
        user_query: The user's search query
        books: List of books to judge
        confidence_threshold: Minimum confidence
    
    Returns:
        (relevant_books, filtered_books) lists
    """
    relevant_books = []
    filtered_books = []
    
    for i, book in enumerate(books, 1):
        result = judge_recommendation_relevance(user_query, book, confidence_threshold)
        
        book_with_judgment = dict(book)
        book_with_judgment["relevance_judgment"] = result
        
        if result["recommend"]:
            relevant_books.append(book_with_judgment)
        else:
            filtered_books.append(book_with_judgment)
        
        if i % 5 == 0:
            print(f"[RelevanceJudge] Processed {i} books... ({len(relevant_books)} relevant)")
    
    print(f"[RelevanceJudge] Final: {len(relevant_books)} relevant, {len(filtered_books)} filtered")
    return relevant_books, filtered_books
