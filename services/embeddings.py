import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# 1. Initialize the embedding model locally (will auto-download on first run)
print("[Embeddings] Loading all-MiniLM-L6-v2 model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Initialize ChromaDB client pointing to our on-disk directory
CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# 3. Create or get our books collection
# Note: ChromaDB requires us to provide a custom embedding function if we want it to auto-embed,
# but manually generating and passing vectors gives us explicit control over our data pipeline.
collection = chroma_client.get_or_create_collection(name="booksoul_collection")

def prepare_soul_text(book_title, soul_json):
    """
    Stage 4: Embed ONLY the BookSoul representation. Never embed raw descriptions.
    """
    themes = ", ".join(soul_json.get("themes", []))
    tropes = ", ".join(soul_json.get("tropes", []))
    style  = soul_json.get("writing_style", "N/A")
    tone   = soul_json.get("emotional_tone", "N/A")
    pacing = soul_json.get("pacing", "N/A")
    char   = soul_json.get("character_dynamics", "N/A")
    vibe   = soul_json.get("reader_vibe", "N/A")
    arc    = soul_json.get("emotional_arc", "N/A")

    text_block = (
        f"Book Title: {book_title}. "
        f"Themes: {themes}. "
        f"Tropes: {tropes}. "
        f"Style: {style}. "
        f"Emotional Tone: {tone}. "
        f"Pacing: {pacing}. "
        f"Character Dynamics: {char}. "
        f"Reader Vibe: {vibe}. "
        f"Emotional Arc: {arc}."
    )
    return text_block

def store_book_vector(book_id, book_title, book_metadata, soul_json, quality_score=0):
    """
    Generates an embedding for a book's soul and saves it to ChromaDB along with metadata.
    """
    try:
        soul_text = prepare_soul_text(book_title, soul_json)
        vector = embedding_model.encode(soul_text).tolist()

        metadata_payload = {
            "title":        book_title,
            "authors":      ", ".join(book_metadata.get("authors", [])),
            "cover_image":  book_metadata.get("cover_image", "") or "",
            "description":  book_metadata.get("description", "") or "",
            "quality_score": quality_score,
            "soul_json_str": json.dumps(soul_json)
        }

        collection.upsert(
            ids=[book_id],
            embeddings=[vector],
            documents=[soul_text],
            metadatas=[metadata_payload]
        )
        return True
    except Exception as e:
        print(f"[ChromaDB Error] Write failed: {e}")
        return False

def retrieve_book_vector(book_id):
    """
    Fetches a single stored book from ChromaDB by its ID to verify storage status.
    """
    try:
        result = collection.get(ids=[book_id], include=["documents", "metadatas", "embeddings"])
        if result and result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None
    except Exception as e:
        print(f"[ChromaDB Error] Retrieval failed: {e}")
        return None