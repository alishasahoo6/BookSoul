import chromadb

from booksoul.config.constants import BOOKSOUL_COLLECTION_NAME
from booksoul.config.paths import CHROMA_DATA_PATH

# Connect to ChromaDB
client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))
collection = client.get_collection(BOOKSOUL_COLLECTION_NAME)

# Strong title indicators (safe to remove)
REMOVE_IF_TITLE_CONTAINS = [
    "encyclopedia",
    "dictionary",
    "handbook",
    "manual",
    "companion",
    "reference",
    "journal",
    "workbook",
    "notebook",
    "planner",
    "humorists",
]

REMOVE_IF_AUTHOR_CONTAINS = [
    "sarcastic notebooks",
]

# Categories that are not fiction
BAD_CATEGORIES = [
    "reference",
    "literary criticism",
    "criticism",
    "education",
    "study aids",
    "language arts",
    "authorship",
    "writing",
    "journalism",
    "library science",
    "self-help",
]

results = collection.get(include=["metadatas"])

ids = results["ids"]
metadatas = results["metadatas"]

delete_ids = []

print("=" * 70)
print("BOOKS THAT WOULD BE REMOVED")
print("=" * 70)

for book_id, metadata in zip(ids, metadatas):

    title = metadata.get("title", "").lower()
    author = metadata.get("authors", "").lower()
    categories = metadata.get("categories", "").lower()

    remove = False
    reason = ""

    # 1. Category-based removal (preferred)
    for cat in BAD_CATEGORIES:
        if cat in categories:
            remove = True
            reason = f"category contains '{cat}'"
            break

    # 2. Title-based removal
    if not remove:
        for word in REMOVE_IF_TITLE_CONTAINS:
            if word in title:
                remove = True
                reason = f"title contains '{word}'"
                break

    # 3. Author-based removal
    if not remove:
        for word in REMOVE_IF_AUTHOR_CONTAINS:
            if word in author:
                remove = True
                reason = f"author contains '{word}'"
                break

    if remove:
        delete_ids.append(book_id)

        collection.delete(ids=[book_id])

        print(f"DELETED : {metadata.get('title', 'Unknown')}")
        print(f"AUTHOR  : {metadata.get('authors', '')}")
        print(f"REASON  : {reason}")
        print("-" * 70)

print()
print(f"Total books in DB : {len(ids)}")
print(f"Would delete      : {len(delete_ids)}")
print(f"Would keep        : {len(ids) - len(delete_ids)}")