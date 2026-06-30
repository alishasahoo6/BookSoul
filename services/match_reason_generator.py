"""
PRIORITY 3: Concise Explanation Generator
Creates brief bullet-point "Why this matches" explanations.

Focus: Semantic similarities, not generic metadata.
Format: 5-6 bullet points, max 15 words each.
"""

import os
import json
import google.generativeai as genai
from services.utils import parse_gemini_json, setup_logger

logger = setup_logger("MatchReasonGenerator")


def generate_match_reasons(user_query: str, book_title: str, book_description: str, book_soul: dict) -> list:
    """
    Generates 5-6 concise bullet points explaining WHY this book matches the query.
    
    Focus on semantic similarities, not generic metadata.
    
    Returns:
    ["✓ Cozy autumn atmosphere", "✓ Emotionally comforting", ...]
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_reasons(book_soul)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        themes = ", ".join(book_soul.get("themes", [])[:4])
        tropes = ", ".join(book_soul.get("tropes", [])[:2])
        vibe = book_soul.get("reader_vibe", "")
        tone = book_soul.get("emotional_tone", "")
        
        prompt = f"""You are a concise book recommendation expert.

User searched for: "{user_query}"
Book: {book_title}
Description: {book_description}

Book Attributes:
- Vibe: {vibe}
- Tone: {tone}
- Themes: {themes}
- Tropes: {tropes}

Generate 5-6 CONCISE bullet points explaining WHY this book matches their search.

Rules:
- Each point: 15 words max
- Focus on semantic meaning, not plot summary
- No generic phrases like "well-written" or "popular"
- Be specific: "Witty banter" not "Good dialogue"
- Format each as a JSON string (no bullet symbols)

Return JSON array:
["reason 1", "reason 2", "reason 3", "reason 4", "reason 5"]"""
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        fallback_data = ["Good match"]
        reasons = parse_gemini_json(response.text, fallback=fallback_data)
        
        # Add checkmark prefix
        formatted = [f"✓ {r}" if not r.startswith("✓") else r for r in reasons]
        
        return formatted[:6]  # Max 6 points
        
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning("Quota exceeded. Falling back.")
            return _fallback_reasons(book_soul)
        logger.error(f"Error generating match reasons: {e}")
        return _fallback_reasons(book_soul)


def _fallback_reasons(book_soul: dict) -> list:
    """Fallback reasons based on BookSoul when Gemini unavailable."""
    reasons = []
    
    themes = book_soul.get("themes", [])
    tropes = book_soul.get("tropes", [])
    vibe = book_soul.get("reader_vibe", "")
    tone = book_soul.get("emotional_tone", "")
    
    if vibe:
        reasons.append(f"✓ {vibe}")
    
    if themes:
        if len(themes[0]) < 20:
            reasons.append(f"✓ Explores {themes[0]}")
    
    if tone:
        reasons.append(f"✓ {tone} tone")
    
    if tropes:
        if len(tropes[0]) < 20:
            reasons.append(f"✓ Features {tropes[0]}")
    
    # Pad to at least 4 reasons
    while len(reasons) < 4:
        reasons.append("✓ Strong character work")
    
    return reasons[:6]
