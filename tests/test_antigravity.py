import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from booksoul.generators.rule_based_booksoul import generate_book_soul

def test_antigravity():
    print("Testing GRAVITATIONAL_PULL (Thriller)...")
    book1 = {
        "title": "The Silent Killer",
        "description": "A dark thriller about a detective investigating a serial killer on a clock ticking race.",
        "categories": ["Thriller", "Mystery"]
    }
    soul1 = generate_book_soul(book1)
    import pprint
    pprint.pprint(soul1)
    
    assert soul1["is_fallback"] is True
    assert soul1["is_antigravity"] is True
    assert "Cat and Mouse" in soul1["tropes"]
    assert "Survival Instincts" in soul1["themes"]
    assert soul1["reader_vibe"] == "High-Stakes Intense Action"
    assert 8 <= soul1["dna"]["pacing"] <= 10
    
    print("\nTesting ZERO_G_FLOAT (Fantasy)...")
    book2 = {
        "title": "The Dragon's Legacy",
        "description": "An epic fantasy quest about a chosen one who joins a magic academy to discover their power and defeat the dark lord.",
        "categories": ["Fantasy"]
    }
    soul2 = generate_book_soul(book2)
    pprint.pprint(soul2)
    
    assert soul2["is_fallback"] is True
    assert soul2["is_antigravity"] is True
    assert "The Chosen One" in soul2["tropes"]
    assert "Good vs Evil" in soul2["themes"]
    assert soul2["reader_vibe"] == "Immersive Magical Escape"
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_antigravity()
