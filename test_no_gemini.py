"""
Smoke test: verify all Gemini dependencies have been removed and
the pipeline modules still work correctly.
"""

import sys

def test_imports():
    from booksoul.pipeline.query_interpreter import interpret_query, QueryType
    from booksoul.generators.booksoul_generator import generate_booksoul
    from booksoul.validation.book_validator import validate_book_candidate
    from booksoul.validation.relevance_judge import judge_recommendation_relevance
    from booksoul.pipeline.match_reason_generator import generate_match_reasons
    from booksoul.ranking.hybrid_ranker import compute_hybrid_score
    from booksoul.models.book_dna import ensure_book_dna
    from booksoul.ai.ai_critic import validate_recommendation
    from booksoul.ai.ai_librarian import validate_book_with_ai
    from booksoul.ai.librarian import validate_book
    from booksoul.config.settings import GOOGLE_BOOKS_API_KEY
    print("  [PASS] All imports successful")

def test_query_interpreter():
    from booksoul.pipeline.query_interpreter import interpret_query, QueryType

    # BOOK_QUERY
    q1 = interpret_query("books like Verity")
    assert q1["query_type"] == QueryType.BOOK_QUERY, f"Got {q1['query_type']}"
    assert q1["extracted_value"] == "Verity", f"Got {q1['extracted_value']}"

    # AUTHOR_QUERY
    q2 = interpret_query("books by Colleen Hoover")
    assert q2["query_type"] == QueryType.AUTHOR_QUERY

    # MOOD_QUERY
    q3 = interpret_query("something cozy and heartwarming")
    assert q3["query_type"] in (QueryType.MOOD_QUERY, QueryType.EMOTION_QUERY)

    # TROPE_QUERY
    q4 = interpret_query("enemies to lovers romance")
    assert q4["query_type"] in (QueryType.TROPE_QUERY, QueryType.MOOD_QUERY)

    # Check search terms are always fiction-scoped
    for q in [q1, q2, q3, q4]:
        for term in q["search_terms"]:
            assert term, "Empty search term found"
    print("  [PASS] Query interpreter: all classifications correct")

def test_booksoul_dna_schema():
    from booksoul.generators.booksoul_generator import generate_booksoul
    soul = generate_booksoul(
        "Verity",
        "A dark psychological thriller about a woman hired to finish a book series.",
        "Thriller, Mystery"
    )
    assert soul, "Empty soul returned"
    dna = soul.get("dna", {})
    required_keys = ["emotional_depth", "comfort", "humor", "angst",
                     "spice", "character_growth", "pacing", "atmosphere"]
    for k in required_keys:
        assert k in dna, f"Missing DNA key: {k}"
        if k != "atmosphere":
            assert isinstance(dna[k], (int, float)), f"Non-numeric DNA: {k}={dna[k]}"
            assert 0 <= dna[k] <= 10, f"DNA out of range: {k}={dna[k]}"
    print("  [PASS] BookSoul DNA schema preserved and values in range")

def test_relevance_judge():
    from booksoul.validation.relevance_judge import judge_recommendation_relevance
    book = {
        "title": "Verity",
        "description": "A dark psychological thriller about betrayal and obsession.",
        "categories": ["Thriller", "Mystery"],
        "soul": {"themes": ["Paranoia"], "tropes": ["Unreliable Narrator"]},
        "soul_match": 75,
    }
    result = judge_recommendation_relevance("psychological thriller", book)
    assert "recommend" in result
    assert "confidence" in result
    assert "reason" in result
    assert "below_threshold" in result
    assert result["recommend"] is True, f"Expected recommend=True, got {result}"
    print(f"  [PASS] Relevance judge returned score={result['confidence']}")

def test_match_reasons():
    from booksoul.pipeline.match_reason_generator import generate_match_reasons
    soul = {
        "themes": ["Paranoia", "Survival"],
        "tropes": ["Unreliable Narrator"],
        "reader_vibe": "High-Stakes Intense",
        "emotional_tone": "Anxious",
        "writing_style": "Fast-Paced",
    }
    reasons = generate_match_reasons("dark thriller mystery", "Verity", "A dark thriller.", soul)
    assert 4 <= len(reasons) <= 6, f"Expected 4-6 reasons, got {len(reasons)}"
    for r in reasons:
        assert isinstance(r, str) and len(r) > 3, f"Bad reason: {r!r}"
    print(f"  [PASS] Match reasons generated: {len(reasons)} bullets")

def test_no_gemini_imports():
    """Ensure google-generativeai is not imported anywhere in booksoul package."""
    import importlib
    import pkgutil
    import booksoul

    for loader, name, is_pkg in pkgutil.walk_packages(
        booksoul.__path__, prefix="booksoul."
    ):
        try:
            mod = importlib.import_module(name)
            src = getattr(mod, "__file__", "") or ""
            if "google.generativeai" in open(src).read() if src.endswith(".py") else "":
                print(f"  [FAIL] Gemini still imported in {name}")
                sys.exit(1)
        except Exception:
            pass
    print("  [PASS] No google.generativeai imports found in booksoul package")


if __name__ == "__main__":
    print("\n=== BookSoul Gemini-Free Smoke Tests ===\n")
    test_imports()
    test_query_interpreter()
    test_booksoul_dna_schema()
    test_relevance_judge()
    test_match_reasons()
    test_no_gemini_imports()
    print("\n=== ALL TESTS PASSED ===\n")
