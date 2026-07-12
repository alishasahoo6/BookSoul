"""
Stage 4: Semantic Ranker.

Ranks validated books using semantic embeddings (BookSoul).
"""

import json
from typing import List, Dict, Any
from booksoul.vector.embeddings import embedding_model
from booksoul.common.utils import setup_logger

logger = setup_logger("SemanticRanker")


def rank_by_semantic_similarity(
    user_query: str,
    books: List[Dict[str, Any]],
    n_top: int = 20
) -> List[Dict[str, Any]]:
    """
    Stage 4: Rank books using BookSoul embeddings.
    
    For each book, we compute semantic similarity between:
    - The user's query (embedded)
    - The book's soul representation (already embedded)
    """
    if not books:
        return []
    
    try:
        # Embed the user query using the correct encode method
        query_embedding = embedding_model.encode(user_query).tolist()
    except Exception:
        logger.exception("Error embedding query")
        return books[:n_top]
    
    # Score each book
    ranked_books = []
    
    for book in books:
        try:
            book_with_score = dict(book)
            
            # Get book's embedding from stored soul or regenerate
            soul = book.get("soul", {})
            if isinstance(soul, str):
                soul = json.loads(soul)
            
            # Embed the book's soul
            soul_text = _soul_to_text(soul)
            book_embedding = embedding_model.encode(soul_text).tolist()
            
            # Compute cosine similarity
            similarity = _cosine_similarity(query_embedding, book_embedding)
            book_with_score["semantic_score"] = similarity
            
            ranked_books.append(book_with_score)
        
        except Exception:
            logger.exception("Error scoring '%s'", book.get('title'))
            book_with_score = dict(book)
            book_with_score["semantic_score"] = 0.0
            ranked_books.append(book_with_score)
    
    # Sort by semantic score (descending)
    ranked_books.sort(key=lambda b: b.get("semantic_score", 0.0), reverse=True)
    
    if ranked_books:
        logger.info(
            "Ranked %d books. Top score: %.3f",
            len(ranked_books),
            ranked_books[0].get('semantic_score', 0.0)
        )
    
    return ranked_books[:n_top]


def _soul_to_text(soul: Dict[str, Any]) -> str:
    """Convert BookSoul dictionary to searchable text."""
    if not soul or not isinstance(soul, dict):
        return ""
    
    parts = []
    
    if "themes" in soul:
        parts.append("Themes: " + ", ".join(soul.get("themes", [])))
    
    if "tropes" in soul:
        parts.append("Tropes: " + ", ".join(soul.get("tropes", [])))
    
    if "emotional_tone" in soul:
        parts.append("Tone: " + soul.get("emotional_tone", ""))
    
    if "writing_style" in soul:
        parts.append("Style: " + soul.get("writing_style", ""))
    
    if "character_dynamics" in soul:
        parts.append("Characters: " + soul.get("character_dynamics", ""))
    
    if "reader_vibe" in soul:
        parts.append("Vibe: " + soul.get("reader_vibe", ""))
    
    return " ".join(parts)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    Returns a value between -1 and 1 (typically 0 to 1 for embeddings).
    """
    if not vec1 or not vec2:
        return 0.0
    
    # Ensure they're lists
    if hasattr(vec1, 'tolist'):
        vec1 = vec1.tolist()  # type: ignore
    if hasattr(vec2, 'tolist'):
        vec2 = vec2.tolist()  # type: ignore
    
    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Compute magnitudes
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)
