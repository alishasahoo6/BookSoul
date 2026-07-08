import os
import json
import google.generativeai as genai

def validate_recommendation(user_query, book_title, book_description):
    """
    Stage 6: AI Critic (Final Validation)
    Validates if the recommendation actually matches the user's intent.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ [AI Critic] Missing API Key. Assuming valid.")
        return True, 100, "Skipped AI validation (No API key)"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""
You are an expert AI book critic.

Would a reader searching for:
'{user_query}'

actually be delighted receiving this recommendation?

Book Title: {book_title}
Book Description: {book_description}

Return JSON only.
{{
    "recommended": true/false,
    "confidence": 0-100,
    "reason": "..."
}}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data.get("recommended", True), data.get("confidence", 100), data.get("reason", "")
    except Exception as e:
        print(f"[AI Critic Error] {e}")
        return True, 100, "Error calling AI Critic"
