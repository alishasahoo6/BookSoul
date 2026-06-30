"""Enhanced Recommendation Pipeline
Orchestrates: Query Interpretation → Retrieval → Validation → Shortlist → BookSoul → Ranking → Judge → Format

The system behaves like an expert librarian, not a keyword search engine.
"""

import json
import re
import concurrent.futures

from services.embeddings import embedding_model, collection, store_book_vector
from services.booksoul_generator import generate_booksoul
from services.google_books import search_books
from services.openlibrary import fetch_openlibrary_book
from services.book_validator import validate_book_candidate
from services.embeddings import retrieve_book_vector
from services.query_interpreter import interpret_query
from services.relevance_judge import judge_recommendation_relevance
from services.match_reason_generator import generate_match_reasons
from services.book_dna import ensure_book_dna
from services.utils import setup_logger

import numpy as np

logger = setup_logger("Recommender")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_result_row(meta, distance):
    """Turn a ChromaDB metadata dict + distance into the display dict.

    Normalises the vector distance (0–2 cosine-distance space) into a
    human-readable 0–100 'soul_match' percentage.
    """
    try:
        soul = json.loads(meta.get("soul_json_str", "{}"))
    except (json.JSONDecodeError, TypeError, KeyError):
        soul = {}

    ensure_book_dna(
        soul,
        description=meta.get("description", ""),
        categories=(meta.get("categories") or "").split(", ") if meta.get("categories") else [],
    )

    raw_dist = float(distance)
    # cosine distance: 0 = identical, 2 = opposite
    soul_match_pct = round(max(0.0, min(100.0, (1.0 - raw_dist / 2.0) * 100)))

    return {
        "title":          meta.get("title", "Unknown"),
        "authors":        meta.get("authors", "Unknown"),
        "cover_image":    meta.get("cover_image", ""),
        "description":    meta.get("description", ""),
        "quality_score":  meta.get("quality_score", 0),
        "soul":           soul,
        "distance_score": round(raw_dist, 4),
        "soul_match":     soul_match_pct,
    }


def _ingest_book(book, quality_score=0):
    """Generate BookSoul and store in ChromaDB.
    Skips generation if the book is already cached in the vector DB.
    Returns True on success, False on failure.
    """
    if not book or not book.get("title"):
        return False

    book_id = "".join(c for c in book["title"] if c.isalnum()).lower()

    # Cache hit: skip Gemini call entirely
    if retrieve_book_vector(book_id):
        logger.info(f"[Cache Hit] '{book['title']}' already in DB.")
        return True

    soul = generate_booksoul(
        book["title"],
        book.get("description", ""),
        ", ".join(book.get("categories", []))
    )
    if not soul:
        return False

    try:
        store_book_vector(
            book_id=book_id,
            book_title=book["title"],
            book_metadata=book,
            soul_json=soul,
            quality_score=quality_score
        )
        return True
    except Exception as e:
        logger.error(f"Could not store '{book['title']}': {e}")
        return False


def _query_chroma(query_embedding, n_results=20):
    """Query ChromaDB and return a list of formatted result dicts."""
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances"]
        )
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []

    matches = []
    if results and results.get("ids") and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            matches.append(
                _format_result_row(results["metadatas"][0][i], results["distances"][0][i])
            )
    return matches


def _normalize_text(s):
    """Strip everything except lowercase alphanumerics for fuzzy comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _fetch_single_term(args):
    """Worker for parallel retrieval: Google Books + Open Library fallback."""
    sq, max_results = args
    results = []
    try:
        batch = search_books(sq, max_results=max_results)
        results.extend(batch)
        if len(batch) < 3:
            ol = fetch_openlibrary_book(sq)
            if ol:
                results.append(ol)
    except Exception as e:
        logger.error(f"Retrieval failed for term '{sq}': {e}")
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_semantic_recommendations(user_query, n_results=5):
    """Complete AI Librarian Pipeline

    Stage 1  : Query Interpretation   — classify & generate search terms
    Stage 2  : Parallel Retrieval     — fetch 30-50 candidates concurrently
    Stage 3  : Validation             — filter notebooks / journals / planners
    Stage 3.5: Shortlist              — cosine-rank & keep top-15 by embedding
    Stage 4  : BookSoul Generation    — Gemini profiles for shortlist only
    Stage 5  : Semantic Ranking       — ChromaDB vector search
    Stage 6  : Relevance Judge        — AI confidence gate (≥85%)
    Stage 7  : Diversity + Reasons    — author cap + bullet-point explanations
    """
    try:
        # ── STAGE 1: Query Interpretation ──────────────────────────────────
        logger.info(f"[Stage 1] Interpreting query: '{user_query}'")
        interpreted = interpret_query(user_query)
        search_terms = interpreted.get("search_terms", [user_query])
        logger.info(f"[Stage 1] Type={interpreted.get('query_type')} | Terms={search_terms[:3]}")

        # ── STAGE 2: Parallel Candidate Retrieval ──────────────────────────
        logger.info(f"[Stage 2] Fetching candidates in parallel ({len(search_terms)} terms)...")
        seen_titles: set = set()
        internet_books = []

        fetch_args = [(sq, 15) for sq in search_terms]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            for batch in executor.map(_fetch_single_term, fetch_args):
                for book in batch:
                    title_key = book["title"].strip().lower()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        internet_books.append(book)

        logger.info(f"[Stage 2] Total unique candidates: {len(internet_books)}")

        # ── STAGE 3: Book Validation ────────────────────────────────────────
        logger.info("[Stage 3] Validating candidates...")
        validated_books = []
        rejected_count = 0
        for book in internet_books:
            is_valid, _ = validate_book_candidate(book)
            if is_valid:
                validated_books.append(book)
            else:
                rejected_count += 1

        logger.info(f"[Stage 3] Validated={len(validated_books)} | Rejected={rejected_count}")

        if not validated_books:
            logger.warning("[Stage 3] No valid candidates — returning empty list.")
            return []

        # ── STAGE 3.5: Batch cosine-similarity shortlist ────────────────────
        logger.info("[Stage 3.5] Shortlisting with batch embeddings...")

        # Single batch encode: query + all candidates
        texts = [user_query] + [
            f"{b.get('title', '')} {b.get('description', '')[:300]}"
            for b in validated_books
        ]
        all_vecs = embedding_model.encode(texts, batch_size=64, show_progress_bar=False)
        query_vec = all_vecs[0]
        book_vecs  = all_vecs[1:]

        norm_q = np.linalg.norm(query_vec)
        scored = []
        for i, b in enumerate(validated_books):
            norm_b = np.linalg.norm(book_vecs[i])
            sim = float(np.dot(query_vec, book_vecs[i]) / (norm_q * norm_b + 1e-9))
            scored.append((sim, b))

        scored.sort(key=lambda x: x[0], reverse=True)
        shortlisted = [b for _, b in scored[:15]]
        logger.info(f"[Stage 3.5] Shortlisted {len(shortlisted)} from {len(validated_books)}")

        # ── STAGE 4: BookSoul Generation (shortlisted only) ────────────────
        logger.info(f"[Stage 4] Generating BookSouls for {len(shortlisted)} candidates...")
        ingested = sum(1 for b in shortlisted if _ingest_book(b))
        logger.info(f"[Stage 4] Ingested={ingested} (cache hits included)")

        # ── STAGE 5: Semantic Ranking via ChromaDB ──────────────────────────
        logger.info("[Stage 5] Querying ChromaDB for semantic matches...")
        query_embedding = embedding_model.encode(user_query).tolist()
        semantic_matches = _query_chroma(query_embedding, n_results=20)

        if not semantic_matches:
            logger.warning("[Stage 5] No semantic matches — returning empty list.")
            return []

        logger.info(f"[Stage 5] Retrieved {len(semantic_matches)} candidates from vector DB")

        # ── STAGE 6: Relevance Judge ────────────────────────────────────────
        logger.info("[Stage 6] Running AI relevance judgment...")
        final_candidates = []
        confidence_threshold = 85

        for m in semantic_matches:
            title = m.get("title", "")
            # IMPORTANT: pass full book dict — not positional title/desc/themes
            judgment   = judge_recommendation_relevance(user_query, m, confidence_threshold)
            confidence = judgment.get("confidence", 0)

            if not judgment.get("recommend", False):
                logger.info(f"[Stage 6] Rejected '{title}' (confidence={confidence}%)")
                continue

            # Boost exact-title matches to 100%
            if _normalize_text(user_query) in _normalize_text(title):
                confidence = 100
                logger.info(f"[Stage 6] Exact title match boosted: '{title}'")

            m["relevance_confidence"] = confidence
            m["relevance_reason"]     = judgment.get("reason", "")
            final_candidates.append(m)

        logger.info(f"[Stage 6] Approved {len(final_candidates)} / {len(semantic_matches)}")

        # ── STAGE 7: Rank → Diversity → Match Reasons ──────────────────────
        final_candidates.sort(
            key=lambda x: (-x.get("relevance_confidence", 0), x.get("distance_score", 1.0))
        )

        # Diversity cap: max 2 books per author
        author_counts: dict = {}
        diverse: list = []
        for m in final_candidates:
            author = m.get("authors", "Unknown").lower()
            author_counts[author] = author_counts.get(author, 0) + 1
            if author_counts[author] <= 2:
                diverse.append(m)
        final_candidates = diverse
        logger.info(f"[Stage 7] After diversity filter: {len(final_candidates)}")

        # Generate concise bullet-point match reasons for the top-N only
        logger.info("[Stage 7] Generating match reasons...")
        for m in final_candidates[:n_results]:
            soul = m.get("soul", {})
            m["match_reasons"] = generate_match_reasons(
                user_query,
                m.get("title", ""),
                m.get("description", ""),
                soul
            )

        result = final_candidates[:n_results]
        logger.info(f"[Pipeline Complete] Returning {len(result)} recommendations")
        return result

    except Exception as e:
        logger.error(f"Pipeline breakdown: {e}")
        import traceback
        traceback.print_exc()
        return []


def generate_recommendation_explanation(user_query, book_title, book_soul):
    """
    Builds a personalised explanation entirely from soul fields — no Gemini needed.
    Uses sentence templates so each book gets a unique, readable reason.
    """
    vibe   = book_soul.get("reader_vibe", "")
    style  = book_soul.get("writing_style", "")
    tone   = book_soul.get("emotional_tone", "")
    pacing = book_soul.get("pacing", "")
    themes = book_soul.get("themes", [])
    tropes = book_soul.get("tropes", [])

    _is_real = lambda v: v and v not in ("Unknown", "N/A", "")

    parts = []

    if _is_real(vibe):
        parts.append(f"<strong>{book_title}</strong> delivers a <em>{vibe}</em> reading experience")
    else:
        parts.append(f"<strong>{book_title}</strong> is a great pick for your search")

    if _is_real(style):
        parts.append(f"written in a <em>{style}</em> style")
    if _is_real(tone):
        parts.append(f"with a <em>{tone}</em> emotional undercurrent")
    if _is_real(pacing):
        parts.append(f"and <em>{pacing}</em> pacing that keeps the pages turning")
    if themes:
        parts.append(f"\u2014 exploring themes of <em>{', '.join(themes[:3])}</em>")
    if tropes:
        parts.append(f"featuring beloved tropes like <em>{' & '.join(tropes[:2])}</em>")

    parts.append(f'making it a strong match for your search: "{user_query}".')
    return " ".join(parts)