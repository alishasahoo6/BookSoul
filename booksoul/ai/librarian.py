"""
Librarian: Rule-based book validation pipeline.
Deterministic replacement — no external AI calls.

Three-step pipeline:
  1. Rule-based keyword rejection
  2. Metadata completeness scoring
  3. Type classification via keyword patterns
"""

from booksoul.common.utils import setup_logger

logger = setup_logger("Librarian")

REJECT_KEYWORDS = [
    "notebook", "journal", "planner", "logbook", "log book", "workbook",
    "activity book", "coloring book", "blank", "prompt journal",
    "composition notebook", "diary", "sketchbook", "notebook for",
    "password book", "guest book",
]

# Book types that indicate positive narrative content
NARRATIVE_TYPE_MAP = [
    (["novel"], "Novel"),
    (["fiction"], "Fiction"),
    (["non-fiction", "nonfiction", "biography", "memoir"], "Non-Fiction"),
    (["children", "picture book", "juvenile"], "Children's Book"),
    (["graphic novel", "comic"], "Graphic Novel"),
    (["poetry"], "Poetry"),
    (["short stories", "anthology"], "Short Stories"),
    (["thriller", "suspense"], "Fiction"),
    (["mystery", "crime"], "Fiction"),
    (["fantasy", "science fiction", "horror", "romance", "young adult"], "Fiction"),
]

NON_NARRATIVE_TYPES = {
    "notebook", "journal", "planner", "workbook", "activity book",
    "coloring book",
}


def _rule_based_filtering(book):
    """Step 1: Check for banned keywords in metadata."""
    text = " ".join([
        book.get("title", ""),
        book.get("subtitle", ""),
        " ".join(book.get("categories", [])),
        book.get("description", "")
    ]).lower()

    for kw in REJECT_KEYWORDS:
        if kw in text:
            return False, f"Rule rejection: contains keyword '{kw}'"

    return True, "Passed rule filtering"


def _classify_book_type(title, description, categories):
    """Step 3 (deterministic): Classify the book type from metadata."""
    text = f"{title} {description} {' '.join(categories)}".lower()

    for keywords, book_type in NARRATIVE_TYPE_MAP:
        if any(kw in text for kw in keywords):
            return True, book_type, 90, "Matched narrative keyword pattern"

    # If no clear type found but description is substantial, accept cautiously
    if len(description.strip()) > 50:
        return True, "Fiction", 75, "Description present; defaulting to Fiction"

    return False, "Unknown", 30, "Could not identify narrative type"


def validate_book(book, threshold=20):
    """
    Validates a book candidate before indexing/recommending.

    Returns:
        (is_valid: bool, score: int, reason: str)
    """
    title = book.get("title", "Unknown")

    # ── Step 1: Rule-Based Filtering ──
    passed, rule_reason = _rule_based_filtering(book)
    if not passed:
        print(f"🚫 [Librarian] Rejected '{title}': {rule_reason}")
        return False, 0, rule_reason

    score = 0

    # ── Step 2: Metadata Validation ──
    desc = book.get("description", "")
    cats = book.get("categories", [])
    cover = book.get("cover_image", "")
    page_count = book.get("page_count", 0)
    publisher = book.get("publisher", "")

    if not desc or "No narrative synopsis" in desc or "No synopsis profile" in desc:
        score -= 30
        return False, score, "No description"
    else:
        score += 15

    if not cats or "Uncategorized" in cats:
        score -= 20
        return False, score, "No categories"
    else:
        score += 10

    if not cover:
        return False, score, "No cover"
    else:
        score += 5

    if isinstance(page_count, int) and page_count > 0:
        if page_count < 20:
            cats_text = " ".join(cats).lower()
            if "children" not in cats_text and "picture" not in cats_text:
                score -= 15

    if publisher:
        score += 5

    # ── Step 3: Type Classification (deterministic) ──
    ai_valid, book_type, confidence, ai_reason = _classify_book_type(
        title, desc, cats
    )

    if not ai_valid:
        print(f"🚫 [Librarian] Classification rejected '{title}': {ai_reason}")
        return False, score, f"Classification rejection: {ai_reason}"

    if confidence < 50:
        print(f"🚫 [Librarian] Low classification confidence '{title}': {confidence}%")
        return False, score, f"Low classification confidence ({confidence}%)"

    # ── Step 4: Quality Score Modifiers ──
    bt_lower = book_type.lower()
    if "novel" in bt_lower or "fiction" in bt_lower:
        score += 40
    elif "notebook" in bt_lower:
        score -= 100
    elif "planner" in bt_lower:
        score -= 100
    elif "workbook" in bt_lower:
        score -= 80

    if score < threshold:
        print(f"🚫 [Librarian] Low Quality Score for '{title}': {score} (Type: {book_type})")
        return False, score, f"Quality score too low ({score})"

    print(f"✅ [Librarian] Approved '{title}' (Score: {score}, Type: {book_type})")
    return True, score, "Passed validation"
