"""Enhanced Recommendation Pipeline

Orchestrates: Query Interpretation → Retrieval → Validation → Shortlist → BookSoul → Ranking → Judge → Format.
The system behaves like an expert librarian, not a keyword search engine.
"""

import json
import re
import concurrent.futures
from typing import List, Dict, Any, Union

import numpy as np

from booksoul.vector.embeddings import embedding_model, collection, store_book_vector
from booksoul.generators.booksoul_generator import generate_booksoul
from booksoul.retrieval.google_books import search_books
from booksoul.retrieval.openlibrary import fetch_openlibrary_book
from booksoul.validation.book_validator import validate_book_candidate
from booksoul.vector.embeddings import retrieve_book_vector
from booksoul.pipeline.query_interpreter import interpret_query
from booksoul.validation.relevance_judge import judge_recommendation_relevance
from booksoul.pipeline.match_reason_generator import generate_match_reasons
from booksoul.models.book_dna import ensure_book_dna
from booksoul.common.utils import setup_logger
from booksoul.ranking.hybrid_ranker import compute_hybrid_score

logger = setup_logger("Recommender")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_result_row(meta: Dict[str, Any], distance: Union[float, int]) -> Dict[str, Any]:
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
    logger.info("[Distance] %s -> %.4f", meta.get('title'), raw_dist)
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


def _ingest_book(book: Dict[str, Any], quality_score: int = 0) -> bool:
    """Generate BookSoul and store in ChromaDB.

    Skips generation if the book is already cached in the vector DB.
    Returns True on success, False on failure.
    """
    if not book or not book.get("title"):
        return False

    book_id = "".join(c for c in book["title"] if c.isalnum()).lower()

    # Cache hit: skip generator call entirely
    if retrieve_book_vector(book_id):
        logger.info("[Cache Hit] '%s' already in DB.", book['title'])
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
        logger.error("Could not store '%s': %s", book['title'], str(e))
        return False


def _query_chroma(query_embedding: List[float], n_results: int = 20) -> List[Dict[str, Any]]:
    """Query ChromaDB and return a list of formatted result dicts."""
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances"]
        )
    except Exception as e:
        logger.error("ChromaDB query failed: %s", str(e))
        return []

    matches = []
    if results and results.get("ids") and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            matches.append(
                _format_result_row(results["metadatas"][0][i], results["distances"][0][i])
            )
    return matches


def _normalize_text(s: str) -> str:
    """Strip everything except lowercase alphanumerics for fuzzy comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _fetch_single_term(args: tuple) -> List[Dict[str, Any]]:
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
        logger.error("Retrieval failed for term '%s': %s", sq, str(e))
    return results


def adjust_distance_by_vibe_profile(book: Dict[str, Any], query_dims: Dict[str, Any]) -> float:
    d = float(book.get("distance_score", 1.0))
    
    title = book.get("title", "").lower()
    description = book.get("description", "").lower()
    soul = book.get("soul", {})
    
    themes = [t.lower() for t in soul.get("themes", [])]
    tropes = [tr.lower() for tr in soul.get("tropes", [])]
    tone = soul.get("emotional_tone", "").lower()
    vibe = soul.get("reader_vibe", "").lower()
    dynamics = soul.get("character_dynamics", "").lower()
    
    combined_book_text = f"{title} {description} {' '.join(themes)} {' '.join(tropes)} {tone} {vibe} {dynamics}"
    
    boost = 0.0
    
    # 1. Reference Book match (e.g. Verity)
    ref_book = query_dims.get("reference_book")
    if ref_book:
        val = ref_book["value"].lower()
        if val in title:
            boost += 0.5

    # 2. Reference Author match (e.g. Colleen Hoover)
    ref_author = query_dims.get("reference_author")
    if ref_author:
        val = ref_author["value"].lower()
        authors = book.get("authors", "").lower()
        if val in authors:
            boost += 0.4

    # 3. Settings matches
    for s_dim in query_dims.get("settings", []):
        val = s_dim["value"].lower()
        if val in combined_book_text:
            boost += 0.25 * s_dim["confidence"]

    # 4. Tropes matches
    for t_dim in query_dims.get("tropes", []):
        val = t_dim["value"].lower()
        if val in combined_book_text:
            boost += 0.25 * t_dim["confidence"]

    # 5. Tones matches
    for tn_dim in query_dims.get("tones", []):
        val = tn_dim["value"].lower()
        if val in combined_book_text:
            boost += 0.15 * tn_dim["confidence"]

    # 6. Genres matches
    for g_dim in query_dims.get("genres", []):
        val = g_dim["value"].lower()
        if val in combined_book_text:
            boost += 0.2 * g_dim["confidence"]

    # 7. Intents matches
    for int_dim in query_dims.get("intents", []):
        val = int_dim["value"].lower()
        if val in combined_book_text:
            boost += 0.15 * int_dim["confidence"]

    # Apply the boost: reduce distance score
    adjusted_d = max(0.05, d - boost)
    return adjusted_d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_semantic_recommendations(user_query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Complete AI Librarian Pipeline

    Stage 1  : Query Interpretation   — classify & generate search terms
    Stage 2  : Parallel Retrieval     — fetch 30-50 candidates concurrently
    Stage 3  : Validation             — filter notebooks / journals / planners
    Stage 3.5: Shortlist              — cosine-rank & keep top-15 by embedding
    Stage 4  : BookSoul Generation    — profiles for shortlist only
    Stage 5  : Semantic Ranking       — ChromaDB vector search
    Stage 6  : Relevance Judge        — AI confidence gate
    Stage 7  : Diversity + Reasons    — author cap + bullet-point explanations
    """
    try:
        # ── STAGE 1: Query Interpretation ──────────────────────────────────
        logger.info("[Stage 1] Interpreting query: '%s'", user_query)
        interpreted = interpret_query(user_query)
        search_terms = interpreted.get("search_terms", [user_query])
        logger.info("[Stage 1] Type=%s | Terms=%s", interpreted.get('query_type'), search_terms[:3])

        # ── STAGE 2: Parallel Candidate Retrieval ──────────────────────────
        logger.info("[Stage 2] Fetching candidates in parallel (%d terms)...", len(search_terms))
        seen_titles = set()
        internet_books = []

        logger.info("[Stage 2] Search terms: %s", search_terms)
        fetch_args = [(sq, 15) for sq in search_terms]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(_fetch_single_term, args) for args in fetch_args]
            try:
                for future in concurrent.futures.as_completed(futures, timeout=30.0):
                    try:
                        batch = future.result()
                        for book in batch:
                            title_key = book["title"].strip().lower()
                            if title_key not in seen_titles:
                                seen_titles.add(title_key)
                                internet_books.append(book)
                    except Exception as e:
                        logger.warning("Error retrieving candidate batch: %s", str(e))
            except concurrent.futures.TimeoutError:
                logger.warning("[Stage 2] Overall candidate retrieval timed out — proceeding with gathered results.")

        logger.info("[Stage 2] Total unique candidates: %d", len(internet_books))

        # ── STAGE 3: Book Validation ────────────────────────────────────────
        logger.info("[Stage 3] Validating candidates...")
        validated_books = []
        rejected_count = 0
        for book in internet_books:
            is_valid, reason = validate_book_candidate(book)
            if is_valid:
                validated_books.append(book)
            else:
                rejected_count += 1

        logger.info("[Stage 3] Validated=%d | Rejected=%d", len(validated_books), rejected_count)

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
        logger.info("[Stage 3.5] Shortlisted %d from %d", len(shortlisted), len(validated_books))

        # ── STAGE 4: BookSoul Generation (shortlisted only) ────────────────
        logger.info("[Stage 4] Generating BookSouls for %d candidates...", len(shortlisted))
        ingested = sum(1 for b in shortlisted if _ingest_book(b))
        logger.info("[Stage 4] Ingested=%d (cache hits included)", ingested)

        # ── STAGE 5: Semantic Ranking via ChromaDB ──────────────────────────
        logger.info("[Stage 5] Querying ChromaDB for semantic matches...")
        query_embedding = embedding_model.encode(user_query).tolist()
        semantic_matches = _query_chroma(query_embedding, n_results=20)

        if not semantic_matches:
            logger.warning("[Stage 5] No semantic matches — returning empty list.")
            return []

        logger.info("[Stage 5] Retrieved %d candidates from vector DB", len(semantic_matches))

        # Stage 5.5 — Hybrid Ranking
        query_dims = interpreted.get("dimensions", {})
        for book in semantic_matches:
            # Adjust distance score based on extracted dimensions
            adjusted_dist = adjust_distance_by_vibe_profile(book, query_dims)
            book["distance_score"] = adjusted_dist
            # Recalculate soul_match pct based on the adjusted distance
            book["soul_match"] = round(max(0.0, min(100.0, (1.0 - adjusted_dist / 2.0) * 100)))

            book["hybrid_score"] = compute_hybrid_score(book, user_query)

        semantic_matches.sort(
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        logger.info("[Stage 5.5] Hybrid ranking complete.")

        logger.info("===== HYBRID SCORES =====")
        for b in semantic_matches[:10]:
            logger.info(
                "%s -> Similarity=%s | Hybrid=%s",
                b['title'],
                b['soul_match'],
                b['hybrid_score']
            )
        logger.info("=========================")

        # ── STAGE 6: Relevance Judge ────────────────────────────────────────
        logger.info("[Stage 6] Running deterministic relevance scoring...")
        final_candidates = []
        confidence_threshold = 35  # Deterministic scorer: lower threshold than AI

        for m in semantic_matches:
            title = m.get("title", "")
            # IMPORTANT: pass full book dict — not positional title/desc/themes
            judgment   = judge_recommendation_relevance(user_query, m, confidence_threshold)
            confidence = judgment.get("confidence", 0)

            if not judgment.get("recommend", False):
                logger.info("[Stage 6] Rejected '%s' (confidence=%d%%)", title, confidence)
                continue

            # Boost exact-title matches to 100%
            if _normalize_text(user_query) in _normalize_text(title):
                confidence = 100
                logger.info("[Stage 6] Exact title match boosted: '%s'", title)

            m["relevance_confidence"] = confidence
            m["relevance_reason"]     = judgment.get("reason", "")
            final_candidates.append(m)

        logger.info("[Stage 6] Approved %d / %d", len(final_candidates), len(semantic_matches))

        # ── STAGE 7: Rank → Diversity → Match Reasons ──────────────────────
        final_candidates.sort(
            key=lambda x: (-x.get("relevance_confidence", 0), x.get("distance_score", 1.0))
        )

        # Diversity cap: max 2 books per author
        author_counts: Dict[str, int] = {}
        diverse = []
        for m in final_candidates:
            author = m.get("authors", "Unknown").lower()
            author_counts[author] = author_counts.get(author, 0) + 1
            if author_counts[author] <= 2:
                diverse.append(m)
        final_candidates = diverse
        logger.info("[Stage 7] After diversity filter: %d", len(final_candidates))

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
        logger.info("[Pipeline Complete] Returning %d recommendations", len(result))
        return result

    except Exception:
        logger.exception("Pipeline breakdown")
        return []


def generate_recommendation_explanation(user_query: str, book_title: str, book_soul: Dict[str, Any]) -> str:
    """Builds a personalised explanation entirely from soul fields — no Gemini needed.

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
