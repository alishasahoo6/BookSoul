from booksoul.vector.embeddings import collection

result = collection.get(include=["metadatas"])

deleted = 0

for book_id, metadata in zip(result["ids"], result["metadatas"]):
    author = metadata.get("authors", "")

    if "sarcastic notebooks" in author.lower():
        print(f"Deleting: {metadata.get('title')}")

        collection.delete(ids=[book_id])
        deleted += 1

print(f"\nDeleted {deleted} books.")