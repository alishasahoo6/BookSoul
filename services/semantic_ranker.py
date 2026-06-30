"""
Stage 4: Semantic Ranker
Ranks validated books using semantic embeddings (BookSoul).
"""

import os
import json
from services.embeddings import embedding_model


def rank_by_semantic_similarity(user_query, books, n_top=20):
    """
    Stage 4: Rank books using BookSoul embeddings.
    
    For each book, we compute semantic similarity between:
    - The user's query (embedded)
    - The book's soul representation (already embedded)
    
    Args:
        user_query: The user's original search query
        books: List of validated books (with BookSoul already generated)
        n_top: Return top N books
    
    Returns:
        List of books ranked by semantic similarity, with scores
    """
    if not books:
        return []
    
    try:
        # Embed the user query
        query_embedding = embedding_model.embed_query(user_query)
    except Exception as e:
        print(f"[SemanticRanker] Error embedding query: {e}")
        # Fallback: return books in original order
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
            book_embedding = embedding_model.embed_query(soul_text)
            
            # Compute cosine similarity
            similarity = _cosine_similarity(query_embedding, book_embedding)
            book_with_score["semantic_score"] = similarity
            
            ranked_books.append(book_with_score)
        
        except Exception as e:
            print(f"[SemanticRanker] Error scoring '{book.get('title')}': {e}")
            # Still include the book, just without a score
            book_with_score = dict(book)
            book_with_score["semantic_score"] = 0.0
            ranked_books.append(book_with_score)
    
    # Sort by semantic score (descending)
    ranked_books.sort(key=lambda b: b.get("semantic_score", 0), reverse=True)
    
    print(f"[SemanticRanker] Ranked {len(ranked_books)} books. Top score: {ranked_books[0].get('semantic_score', 0):.3f}")
    
    return ranked_books[:n_top]


def _soul_to_text(soul):
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


def _cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two embedding vectors.
    Returns a value between -1 and 1 (typically 0 to 1 for embeddings).
    """
    if not vec1 or not vec2:
        return 0.0
    
    # Ensure they're lists
    if hasattr(vec1, 'tolist'):
        vec1 = vec1.tolist()
    if hasattr(vec2, 'tolist'):
        vec2 = vec2.tolist()
    
    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Compute magnitudes
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)
