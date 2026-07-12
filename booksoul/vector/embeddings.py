"""
Vector embeddings module.

Orchestrates loading the local SentenceTransformer embedding model and manages ChromaDB persistent vector storage.
"""

import json
from typing import Dict, List, Any, Optional, Union
import chromadb
from sentence_transformers import SentenceTransformer
from booksoul.config.constants import EMBEDDING_MODEL_NAME, BOOKSOUL_COLLECTION_NAME
from booksoul.config.paths import CHROMA_DATA_PATH
from booksoul.common.utils import setup_logger

logger = setup_logger("Embeddings")

# 1. Initialize the embedding model locally (will auto-download on first run)
logger.info("Loading all-MiniLM-L6-v2 model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# 2. Initialize ChromaDB client pointing to our on-disk directory
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))

# 3. Create or get our books collection
collection = chroma_client.get_or_create_collection(name=BOOKSOUL_COLLECTION_NAME)


def prepare_soul_text(book_title: str, soul_json: Dict[str, Any]) -> str:
    """
    Build a rich semantic representation of a book for embedding.
    This is the ONLY text embedded into ChromaDB.
    """

    def join(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(value)
        return value or "Unknown"

    text = f"""
TITLE
{book_title}

GENRE
{join(soul_json.get("genre"))}

THEMES
{join(soul_json.get("themes"))}

TROPES
{join(soul_json.get("tropes"))}

WRITING STYLE
{join(soul_json.get("writing_style"))}

EMOTIONAL TONE
{join(soul_json.get("emotional_tone"))}

PACING
{join(soul_json.get("pacing"))}

CHARACTER DYNAMICS
{join(soul_json.get("character_dynamics"))}

READER VIBE
{join(soul_json.get("reader_vibe"))}

EMOTIONAL ARC
{join(soul_json.get("emotional_arc"))}

ATMOSPHERE
{join(soul_json.get("atmosphere"))}

SETTING
{join(soul_json.get("setting"))}

CORE PREMISE
{join(soul_json.get("core_premise"))}

CHARACTER ARCHETYPES
{join(soul_json.get("character_archetypes"))}

EMOTIONAL DNA

Emotional Depth: {soul_json.get("emotional_depth", 5)}

Comfort: {soul_json.get("comfort", 5)}

Humor: {soul_json.get("humor", 5)}

Angst: {soul_json.get("angst", 5)}

Spice: {soul_json.get("spice", 5)}

Character Growth: {soul_json.get("character_growth", 5)}

Reader Experience

This book is ideal for readers who enjoy
{join(soul_json.get("reader_vibe"))},
with themes of {join(soul_json.get("themes"))},
strong emphasis on {join(soul_json.get("character_dynamics"))},
and a {join(soul_json.get("emotional_tone"))} atmosphere.
"""

    return text.strip()


def store_book_vector(
    book_id: str,
    book_title: str,
    book_metadata: Dict[str, Any],
    soul_json: Dict[str, Any],
    quality_score: Union[int, float] = 0
) -> bool:
    """
    Generates an embedding for a book's soul and saves it to ChromaDB along with metadata.
    """
    try:
        soul_text = prepare_soul_text(book_title, soul_json)
        vector = embedding_model.encode(soul_text).tolist()

        metadata_payload = {
            "title": book_title,
            "authors": ", ".join(book_metadata.get("authors", [])),
            "cover_image": book_metadata.get("cover_image", "") or "",
            "description": book_metadata.get("description", "") or "",
            "categories": json.dumps(book_metadata.get("categories", [])),
            "page_count": book_metadata.get("page_count", 0),
            "publisher": book_metadata.get("publisher", ""),
            "published_date": book_metadata.get("published_date", ""),
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
    except Exception:
        logger.exception("ChromaDB Write failed")
        return False


def retrieve_book_vector(book_id: str) -> Optional[Dict[str, Any]]:
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
    except Exception:
        logger.exception("ChromaDB Retrieval failed")
        return None
