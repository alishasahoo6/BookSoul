"""
PRIORITY 1: Enhanced Book Validator
Strict filtering for notebooks, journals, planners, and other non-narrative publications.

This runs BEFORE BookSoul generation to avoid wasting resources.
"""

REJECT_KEYWORDS = [
    # Blank/consumable products
    "notebook", "journal", "planner", "logbook", "log book", "workbook",
    "activity book", "coloring book", "blank", "prompt journal",
    "composition notebook", "diary", "sketchbook", "notebook for",
    "password book", "guest book", "quote book", "organizer",
    "bullet journal", "planner notebook", "writing journal",
    "scrapbook", "graffiti book", "doodle book",
    
    # Exercise/educational materials
    "exercise book", "workbook", "exercise workbook", "practice book",
    "test prep", "study guide", "homework", "activity", "puzzle book",
    "crossword", "sudoku", "maze",
    
    # Other non-narrative
    "cookbook", "recipe", "comic strip", "comic book annual",
    "scratch", "sticker", "temporary tattoo", "temporary",
    "scratch and sniff", "board book", "lift the flap",
    "bath book", "board", "cardboard",
]

REJECT_TITLE_PATTERNS = [
    # Generic notebook-like titles
    r"^\d+",  # Starts with number
    r"my .*book$",
    r"my .*journal$",
    r"my .*planner$",
]


def validate_book_candidate(book):
    """
    PRIORITY 1: Pre-validation filtering for notebook/journal/planner etc.
    
    This is the FIRST filter before AI validation.
    Rejects obviously non-narrative items quickly.
    
    Args:
        book: Book dictionary with metadata
    
    Returns:
        (is_valid: bool, rejection_reason: str or None)
    """
    title = book.get("title", "").lower()
    description = book.get("description", "").lower()
    categories = [c.lower() for c in book.get("categories", [])]
    cover_image = book.get("cover_image", "")
    page_count = book.get("page_count", 0)
    
    # --- Reject: Missing critical metadata ---
    if not book.get("title"):
        return False, "Missing title"
    
    if not description or description == "no description available.":
        return False, "Missing description"
    
    if not categories or categories == ["uncategorized"]:
        return False, "Missing or uncategorized"
    
    if not cover_image:
        return False, "Missing cover image"
    
    # --- Reject: Keyword-based filtering (AGGRESSIVE) ---
    full_text = f"{title} {' '.join(categories)} {description}"
    
    for keyword in REJECT_KEYWORDS:
        if keyword in full_text:
            return False, f"Contains rejected keyword: '{keyword}'"
    
    # --- Reject: Suspicious page counts ---
    if isinstance(page_count, int) and page_count > 0:
        # Reject very short items that aren't picture books
        if page_count < 30:
            categories_str = " ".join(categories)
            is_picture_book = any(
                word in categories_str 
                for word in ["picture", "children", "board book", "boardbook", "kids", "toddler"]
            )
            if not is_picture_book:
                return False, f"Suspiciously short ({page_count} pages)"
        
        # Also reject books with extremely low page counts even if they might match genres
        if page_count < 20 and "children" not in " ".join(categories).lower():
            return False, f"Too short for adult book ({page_count} pages)"
    
    # --- Reject: Generic/ambiguous titles ---
    title_clean = title.strip()
    if len(title_clean) < 3:
        return False, "Title too short/ambiguous"
    
    # --- Reject: No narrative content indicators ---
    # Look for indicators that it's NOT a narrative book
    non_narrative_indicators = [
        "100 blank", "200 blank", "365 blank",  # Count + blank
        "for you to write", "for you to draw",
        "fill in the blanks", "fill-in", "fill in",
        "write in", "write-in", "create your own",
    ]
    
    for indicator in non_narrative_indicators:
        if indicator in full_text:
            return False, f"Non-narrative indicator: '{indicator}'"
    
    # --- Reject: Categories that are clearly non-narrative ---
    non_narrative_categories = [
        "calendars", "cartography", "comics & graphic novels",  # Comics are usually narrative, but comics strips aren't
        "reference", "self-help", "textbooks", "educational",
    ]
    
    for cat in categories:
        for non_narr_cat in non_narrative_categories:
            if non_narr_cat in cat:
                # Self-help could be okay, but be cautious
                if non_narr_cat == "self-help":
                    # Allow self-help only if it has positive indicators
                    narrative_indicators = ["memoir", "biography", "story", "narrative", "narrative non-fiction"]
                    has_narrative_indicator = any(ind in full_text for ind in narrative_indicators)
                    if not has_narrative_indicator:
                        return False, f"Appears to be self-help, not narrative"
                else:
                    return False, f"Non-narrative category: '{non_narr_cat}'"
    
    return True, None


def get_rejection_reasons(book):
    """
    Debug helper: Get all rejection reasons for a book.
    Useful for understanding why books are filtered.
    """
    is_valid, reason = validate_book_candidate(book)
    return reason if not is_valid else "VALID"
