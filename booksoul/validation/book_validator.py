"""
Enhanced Book Validator.

Strict filtering for notebooks, journals, planners, and other non-narrative publications.
This runs BEFORE BookSoul generation to avoid wasting resources.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from booksoul.common.utils import setup_logger

logger = setup_logger("BookValidator")

REJECT_KEYWORDS: List[str] = [
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

NON_STORY_KEYWORDS: List[str] = [
    # Reference works
    "encyclopedia",
    "dictionary",
    "glossary",
    "atlas",
    "almanac",

    # Academic / literary analysis
    "literary criticism",
    "criticism",
    "critical study",
    "critical studies",
    "analysis",
    "essays",
    "scholarship",
    "academic",

    # Guides
    "handbook",
    "manual",
    "companion",
    "how to",
    "techniques",
    "tips",
    "writing humor",
    "writing comedy",

    # Collections that are not stories
    "jokes",
    "joke book",
    "humorists",
    "quotation",
    "humour",
    "quotes",
]

REJECT_TITLE_PATTERNS: List[str] = [
    # Generic notebook-like titles
    r"^\d+",  # Starts with number
    r"my .*book$",
    r"my .*journal$",
    r"my .*planner$",
]

# Categories that BookSoul currently supports.
# Version 1 focuses on narrative fiction only.
FICTION_CATEGORIES: List[str] = [
    "fiction",
    "romance",
    "fantasy",
    "science fiction",
    "fantasy fiction",
    "historical fiction",
    "literary fiction",
    "mystery",
    "thriller",
    "horror",
    "crime",
    "suspense",
    "young adult",
    "young adult fiction",
    "coming of age",
    "adventure",
    "action",
    "dystopian",
    "paranormal",
    "urban fantasy",
    "dark fantasy",
    "epic fantasy",
    "romantic suspense",
    "romantic comedy",
    "romantic fiction",
    "contemporary romance",
    "historical romance",
    "sports romance",
    "small town romance",
]


def validate_book_candidate(book: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Pre-validation filtering for notebook/journal/planner etc.
    
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
    
    # Version 1 of BookSoul supports fiction only.
    # If none of the categories indicate fiction, reject.
    categories_text = " ".join(categories)
    has_fiction_category = any(
        keyword in categories_text
        for keyword in FICTION_CATEGORIES
    )

    if not has_fiction_category:
        return False, "Not a supported fiction category"
    
    # --- Reject: Keyword-based filtering (AGGRESSIVE) ---
    full_text = f"{title} {' '.join(categories)} {description}"
    
    for keyword in REJECT_KEYWORDS:
        if keyword in full_text:
            return False, f"Contains rejected keyword: '{keyword}'"
        
    # --- Reject: Non-story books ---
    for keyword in NON_STORY_KEYWORDS:
        if keyword in full_text:
            return False, f"Non-story book: '{keyword}'"
    
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
    non_narrative_indicators = [
        "100 blank", "200 blank", "365 blank",
        "for you to write", "for you to draw",
        "fill in the blanks", "fill-in", "fill in",
        "write in", "write-in", "create your own",
    ]
    
    for indicator in non_narrative_indicators:
        if indicator in full_text:
            return False, f"Non-narrative indicator: '{indicator}'"
    
    # --- Reject: Categories that are clearly non-narrative ---
    non_narrative_categories = [
        "calendars", "cartography", "comics & graphic novels",
        "reference", "self-help", "textbooks", "educational",
    ]
    
    for cat in categories:
        for non_narr_cat in non_narrative_categories:
            if non_narr_cat in cat:
                if non_narr_cat == "self-help":
                    # Allow self-help only if it has positive indicators
                    narrative_indicators = ["memoir", "biography", "story", "narrative", "narrative non-fiction"]
                    has_narrative_indicator = any(ind in full_text for ind in narrative_indicators)
                    if not has_narrative_indicator:
                        return False, f"Appears to be self-help, not narrative"
                else:
                    return False, f"Non-narrative category: '{non_narr_cat}'"
    
    return True, None


def get_rejection_reasons(book: Dict[str, Any]) -> str:
    """
    Debug helper: Get all rejection reasons for a book.
    """
    is_valid, reason = validate_book_candidate(book)
    return reason if not is_valid else "VALID"
