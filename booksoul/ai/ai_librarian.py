"""
Stage 3: AI Librarian (Deterministic Replacement)
Rule-based validation — no external AI calls.

Validates whether a book is a real narrative work using keyword dictionaries
and metadata heuristics. Preserves the exact same public API.
"""

NON_NARRATIVE_KEYWORDS = [
    "notebook", "journal", "planner", "logbook", "log book", "workbook",
    "activity book", "coloring book", "blank", "prompt journal",
    "composition notebook", "diary", "sketchbook", "password book",
    "guest book", "sticker book", "puzzle book", "crossword",
    "sudoku", "recipe book", "cookbook",
]

NARRATIVE_TYPES = [
    "novel", "fiction", "non-fiction", "memoir", "biography",
    "poetry", "children", "graphic novel", "short stories",
    "young adult", "thriller", "mystery", "fantasy", "romance",
    "horror", "science fiction",
]


def validate_book_with_ai(book, confidence_threshold=80):
    """
    Deterministic book validation — replaces the Gemini AI validator.

    Returns the same dict schema as the previous Gemini implementation:
        {
            "valid": bool,
            "type": str,
            "confidence": int,
            "reason": str,
            "below_threshold": bool
        }
    """
    title = book.get("title", "Unknown")
    description = book.get("description", "").lower()
    categories = ", ".join(book.get("categories", []))
    full_text = f"{title.lower()} {description} {categories.lower()}"

    # Reject obvious non-narrative items
    for kw in NON_NARRATIVE_KEYWORDS:
        if kw in full_text:
            return {
                "valid": False,
                "type": "Non-narrative",
                "confidence": 95,
                "reason": f"Contains non-narrative keyword: '{kw}'",
                "below_threshold": False,
            }

    # Detect narrative type
    detected_type = "Unknown"
    confidence = 70

    for narrative in NARRATIVE_TYPES:
        if narrative in full_text:
            detected_type = narrative.title()
            confidence = 90
            break

    # Require a minimum description length
    if len(description.strip()) < 30:
        return {
            "valid": False,
            "type": detected_type,
            "confidence": 30,
            "reason": "Description too short to confirm narrative content",
            "below_threshold": True,
        }

    is_valid = confidence >= confidence_threshold
    return {
        "valid": is_valid,
        "type": detected_type,
        "confidence": confidence,
        "reason": "Passed rule-based narrative validation",
        "below_threshold": confidence < confidence_threshold,
    }


def batch_validate_books(books, confidence_threshold=80):
    """
    Validate multiple books and return only valid ones.

    Returns:
        (valid_books, rejected_books) tuples with validation metadata
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
