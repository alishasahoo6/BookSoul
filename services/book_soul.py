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


def generate_book_soul(book):
    """
    Creates a lightweight BookSoul from book metadata.
    All fields are now inferred — no more 'Unknown' values.
    """
    categories = book.get("categories", [])
    description = book.get("description", "").lower()

    soul = {
        "themes": categories if categories else ["General"],
        "tropes": [],
        "writing_style": infer_writing_style(categories, description),
        "emotional_tone": infer_emotional_tone(categories, description),
        "pacing": infer_pacing(categories, description),
        "reader_vibe": infer_reader_vibe(categories, description)
    }

    return soul