import os
import json
import google.generativeai as genai
from services.utils import parse_gemini_json, setup_logger
from services.book_dna import ensure_book_dna

logger = setup_logger("BookSoulGenerator")

def generate_booksoul(book_title, book_description, categories):
    """
    PRIORITY 2: Enhanced BookSoul Generator
    
    Generates the structured BookSoul representation with DNA attributes.
    Includes numeric values (0-10) for visualization as bars.
    
    Stage 3: Generates the structured BookSoul representation using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("Missing API Key. Returning empty BookSoul.")
        return {}
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
You are an expert literary analyst. Generate a comprehensive BookSoul for this book.

Title: {book_title}
Description: {book_description}
Categories: {categories}

Return JSON ONLY:
{{
    "themes": ["theme1", "theme2", ...],
    "tropes": ["trope1", "trope2", ...],
    "emotional_tone": "tone",
    "writing_style": "style",
    "pacing": "pace",
    "character_dynamics": "dynamics",
    "reader_vibe": "vibe",
    "emotional_arc": "arc",
    
    "dna": {{
        "emotional_depth": 0-10,
        "comfort": 0-10,
        "humor": 0-10,
        "angst": 0-10,
        "spice": 0-10,
        "character_growth": 0-10,
        "pacing": 0-10,
        "atmosphere": "description"
    }}
}}

DNA Guide:
- emotional_depth: How deeply the book explores emotions (0=surface level, 10=profoundly emotional)
- comfort: How comforting/cozy it feels (0=challenging/dark, 10=very comforting)
- humor: Level of humor/wit (0=serious, 10=hilarious)
- angst: Level of emotional turmoil/drama (0=peaceful, 10=very angsty)
- spice: Romance/intimacy level (0=none, 10=very spicy)
- character_growth: How much characters evolve (0=static, 10=major transformation)
- pacing: Reading speed (0=very slow, 10=fast-paced)
- atmosphere: One-line description of the atmosphere
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        fallback_soul = {
            "themes": ["General"],
            "tropes": ["General"],
            "emotional_tone": "Unknown",
            "writing_style": "Unknown",
            "pacing": "Unknown",
            "character_dynamics": "Unknown",
            "reader_vibe": "Unknown",
            "emotional_arc": "Unknown",
            "dna": {
                "emotional_depth": 5, "comfort": 5, "humor": 5,
                "angst": 5, "spice": 5, "character_growth": 5,
                "pacing": 5, "atmosphere": "Unknown"
            }
        }
        
        soul = parse_gemini_json(response.text, fallback=fallback_soul)
        
        # Validate DNA scores are in range
        if "dna" in soul:
            for key in ["emotional_depth", "comfort", "humor", "angst", "spice", "character_growth", "pacing"]:
                if key in soul["dna"]:
                    score = soul["dna"][key]
                    if not isinstance(score, (int, float)) or score < 0 or score > 10:
                        soul["dna"][key] = 5  # Default to middle value if invalid

        ensure_book_dna(soul, description=book_description, categories=categories.split(", ") if categories else [])
        
        return soul
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
            logger.warning("Quota exceeded. Returning fallback BookSoul.")
            return fallback_soul if 'fallback_soul' in locals() else {
                "themes": ["General"],
                "tropes": ["General"],
                "emotional_tone": "Unknown",
                "writing_style": "Unknown",
                "pacing": "Unknown",
                "character_dynamics": "Unknown",
                "reader_vibe": "Unknown",
                "emotional_arc": "Unknown",
                "dna": {
                    "emotional_depth": 5, "comfort": 5, "humor": 5,
                    "angst": 5, "spice": 5, "character_growth": 5,
                    "pacing": 5, "atmosphere": "Unknown"
                }
            }
        logger.error(f"Error generating booksoul: {e}")
        return fallback_soul if 'fallback_soul' in locals() else {}
