import os
import json
import chromadb
from booksoul.vector.embeddings import store_book_vector, retrieve_book_vector
from booksoul.retrieval.google_books import fetch_book_info
from booksoul.generators.booksoul_generator import generate_booksoul

# Books from the mockup to seed
BOOKS_TO_SEED = [
    {
        "query": "Wild Love Elsie Silver",
        "title": "Wild Love",
        "authors": ["Elsie Silver"],
        "soul": {
            "themes": ["Small Town", "Romance", "Love"],
            "tropes": ["Small Town", "Slow Burn", "Protective Hero"],
            "emotional_tone": "Tender & Sweet",
            "writing_style": "Character-Driven & Emotional",
            "pacing": "Slow Burn",
            "reader_vibe": "Cozy Romance",
            "atmosphere": "Warm and sweet small-town romance",
            "dna": {
                "emotional_depth": 7,
                "comfort": 8,
                "humor": 6,
                "angst": 4,
                "spice": 7,
                "character_growth": 7,
                "pacing": 4
            }
        }
    },
    {
        "query": "Powerless Lauren Roberts",
        "title": "Powerless",
        "authors": ["Lauren Roberts"],
        "soul": {
            "themes": ["Fantasy", "Enemies to Lovers", "Magic"],
            "tropes": ["Enemies to Lovers", "Slow Burn", "High Stakes", "Forced Proximity"],
            "emotional_tone": "Tense & Thrilling",
            "writing_style": "World-Building & Descriptive",
            "pacing": "Slow Burn",
            "reader_vibe": "Magical & Immersive",
            "atmosphere": "High-stakes magical trial with forbidden tension",
            "dna": {
                "emotional_depth": 7,
                "comfort": 4,
                "humor": 5,
                "angst": 8,
                "spice": 5,
                "character_growth": 8,
                "pacing": 5
            }
        }
    },
    {
        "query": "Fourth Wing Rebecca Yarros",
        "title": "Fourth Wing",
        "authors": ["Rebecca Yarros"],
        "soul": {
            "themes": ["Fantasy", "Dragons", "War"],
            "tropes": ["Enemies to Lovers", "Dragons", "Strong FMC", "High Stakes"],
            "emotional_tone": "Action-Packed & Intense",
            "writing_style": "Fast-Paced & Gripping",
            "pacing": "Fast",
            "reader_vibe": "Pulse-Pounding & Wild",
            "atmosphere": "Brutal military college for dragon riders",
            "dna": {
                "emotional_depth": 6,
                "comfort": 3,
                "humor": 5,
                "angst": 8,
                "spice": 8,
                "character_growth": 8,
                "pacing": 8
            }
        }
    },
    {
        "query": "A Court of Thorns and Roses Sarah J. Maas",
        "title": "A Court of Thorns and Roses",
        "authors": ["Sarah J. Maas"],
        "soul": {
            "themes": ["Fantasy", "Romance", "Faerie World"],
            "tropes": ["Faerie World", "Beauty and the Beast", "Slow Burn", "Arranged Marriage"],
            "emotional_tone": "Magical & Dangerous",
            "writing_style": "Lyrical & Immersive",
            "pacing": "Medium",
            "reader_vibe": "Magical & Immersive",
            "atmosphere": "Lush and dangerous faerie court",
            "dna": {
                "emotional_depth": 8,
                "comfort": 5,
                "humor": 5,
                "angst": 7,
                "spice": 6,
                "character_growth": 9,
                "pacing": 5
            }
        }
    },
    {
        "query": "Throne of Glass Sarah J. Maas",
        "title": "Throne of Glass",
        "authors": ["Sarah J. Maas"],
        "soul": {
            "themes": ["Fantasy", "Assassins", "Royalty"],
            "tropes": ["Strong FMC", "Deadly Competition", "Found Family"],
            "emotional_tone": "Heroic & Dark",
            "writing_style": "Lyrical & Plot-Driven",
            "pacing": "Medium-Fast",
            "reader_vibe": "Magical & Immersive",
            "atmosphere": "Deadly palace competition with dark secrets",
            "dna": {
                "emotional_depth": 8,
                "comfort": 4,
                "humor": 6,
                "angst": 7,
                "spice": 2,
                "character_growth": 9,
                "pacing": 6
            }
        }
    }
]

def seed():
    print("[Seeding] Starting seeding process...")
    for item in BOOKS_TO_SEED:
        book_title = item["title"]
        book_id = "".join(c for c in book_title if c.isalnum()).lower()
        
        # Check if already stored
        if retrieve_book_vector(book_id):
            print(f"[Seeding] '{book_title}' is already indexed in ChromaDB.")
            continue
            
        print(f"[Seeding] Fetching Google Books metadata for '{book_title}'...")
        book_meta = fetch_book_info(item["query"])
        
        if not book_meta:
            print(f"[Seeding] Warning: Could not find '{book_title}' on Google Books, creating mock metadata...")
            book_meta = {
                "title": book_title,
                "authors": item["authors"],
                "description": f"A beautiful fantasy/romance book titled {book_title} by {', '.join(item['authors'])}.",
                "categories": item["soul"]["themes"],
                "published_year": "2023",
                "cover_image": "",
                "page_count": 400,
                "publisher": "Seed Publisher"
            }
            
        print(f"[Seeding] Storing '{book_title}' with pre-computed BookSoul DNA...")
        store_book_vector(
            book_id=book_id,
            book_title=book_title,
            book_metadata=book_meta,
            soul_json=item["soul"],
            quality_score=9.5
        )
    print("[Seeding] Database seeding complete!")

if __name__ == "__main__":
    seed()
