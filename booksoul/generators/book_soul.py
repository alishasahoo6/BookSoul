 
import os
import json
import google.generativeai as genai
from booksoul.common.utils import parse_gemini_json, setup_logger
from booksoul.models.book_dna import ensure_book_dna

logger = setup_logger("BookSoulGenerator")
def infer_reader_vibe(categories, description):
    text = " ".join(categories).lower() + " " + description

    if "romance" in text:
        return "Cozy Romance"
    if "fantasy" in text:
        return "Magical & Immersive"
    if "horror" in text:
        return "Dark & Thrilling"
    if "mystery" in text:
        return "Suspenseful"
    if "thriller" in text:
        return "High-Stakes Intense"
    if "science fiction" in text or "sci-fi" in text:
        return "Futuristic & Mind-Bending"
    if "self" in text or "personal" in text or "habit" in text or "growth" in text:
        return "Motivational & Reflective"
    if "history" in text or "biography" in text or "memoir" in text:
        return "Thoughtful & Informative"
    return "General Non-Fiction"

def infer_writing_style(categories, description):
    text = " ".join(categories).lower() + " " + description

    if "poetry" in text:
        return "Lyrical"
    if "fantasy" in text:
        return "World-Building & Descriptive"
    if "thriller" in text:
        return "Fast-Paced & Gripping"
    if "mystery" in text:
        return "Suspense-Driven"
    if "romance" in text:
        return "Character-Driven & Emotional"
    if "science fiction" in text or "sci-fi" in text:
        return "Concept-Driven & Speculative"
    if "self" in text or "habit" in text or "growth" in text:
        return "Practical & Actionable"
    if "history" in text or "biography" in text:
        return "Narrative Non-Fiction"
    return "Balanced & Accessible"

def infer_emotional_tone(categories, description):
    text = " ".join(categories).lower() + " " + description

    if "romance" in text:
        return "Warm & Heartfelt"
    if "horror" in text:
        return "Tense & Unsettling"
    if "thriller" in text:
        return "Anxious & Adrenaline-Fuelled"
    if "mystery" in text:
        return "Curious & Contemplative"
    if "fantasy" in text:
        return "Wondrous & Epic"
    if "self" in text or "habit" in text or "growth" in text:
        return "Optimistic & Empowering"
    if "history" in text or "biography" in text:
        return "Reflective & Grounded"
    return "Neutral & Informative"

def infer_pacing(categories, description):
    text = " ".join(categories).lower() + " " + description

    if "thriller" in text or "action" in text:
        return "Fast"
    if "romance" in text or "literary" in text:
        return "Moderate"
    if "self" in text or "habit" in text or "history" in text:
        return "Steady & Deliberate"
    if "fantasy" in text or "adventure" in text:
        return "Varied — builds to a climax"
    return "Moderate"


import random
from google.api_core.exceptions import ResourceExhausted, GoogleAPICallError

def generate_book_soul(book):
    """
    Generates the BookSoul using the official Gemini API.
    If quota is exhausted (429), it falls back seamlessly to rule-based analysis.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("Missing API Key. Returning local fallback analysis.")
        return generate_book_soul_fallback(book)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Use the official SDK generation syntax instead of manual web requests
        prompt = f"Analyze this book and return a dynamic narrative profile structure: {str(book)}"
        response = model.generate_content(prompt)
        
        soul = parse_gemini_json(response.text)
        if not soul:
            logger.warning("Failed to parse Gemini response. Returning local fallback BookSoul.")
            return generate_book_soul_fallback(book)
        
        ensure_book_dna(soul, description=book.get("description", ""), categories=book.get("categories", []))
        return soul
    
    except (ResourceExhausted, GoogleAPICallError) as e:
        logger.warning(f"Gemini API quota exhausted or call error: {e}. Triggering robust local fallback.")
        return generate_book_soul_fallback(book)
    
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning(f"Gemini API quota exhausted: {e}. Triggering robust local fallback.")
        else:
            logger.error(f"Unexpected error in generation: {e}. Triggering robust local fallback.")
        return generate_book_soul_fallback(book)


def generate_book_soul_fallback(book):
    """
    Generates a rule-based BookSoul fallback using your existing text logic helpers
    and maps them to the precise keys expected by the application frontend interface.
    """
    from booksoul.generators.rule_based_booksoul import generate_book_soul
    return generate_book_soul(book)
