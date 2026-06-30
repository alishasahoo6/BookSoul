import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    print("[Gemini] Warning: GEMINI_API_KEY not found.")

def generate_book_soul(title, description):
    print(f"🧠 Gemini called for: {title}")

    if not api_key:
        return {"error": "GEMINI_API_KEY not found."}

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are an expert literary analyst.

Analyze the following book.

Book Title:
{title}

Description:
{description}

Return ONLY valid JSON in this format:

{{
    "themes": [],
    "tropes": [],
    "writing_style": "",
    "emotional_tone": "",
    "pacing": "",
    "reader_vibe": ""
}}

Do not include markdown.
Return raw JSON only.
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        soul = json.loads(response.text)
        return soul

    except Exception as e:
        print(f"[Gemini Error] {e}")

        # Daily quota exceeded
        if "429" in str(e) or "quota" in str(e).lower():

            print("⚠️ Gemini quota exceeded. Using fallback BookSoul.")

            return {
                "themes": [
                    "Identity",
                    "Personal Growth",
                    "Relationships"
                ],
                "tropes": [
                    "Enemies to Lovers",
                    "Forced Proximity"
                ],
                "writing_style": "Character-driven",
                "emotional_tone": "Warm and emotional",
                "pacing": "Moderate",
                "reader_vibe": "Cozy Romance"
            }

        return {
            "error": str(e)
        }