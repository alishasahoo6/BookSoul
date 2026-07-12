import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend_api.main import app

client = TestClient(app)

def test_get_root():
    """
    Verify GET / returns a 200 status code and the correct status message.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "BookSoul Backend Running 🚀"

def test_post_recommend():
    """
    Verify POST /recommend/ accepts a query and return recommendations matching the expected schema.
    """
    payload = {"query": "cozy romance set in a small town", "n_results": 2}
    # Test POST /recommend/ (with slash) and/or check if redirects work or POST /recommend works
    response = client.post("/recommend/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    results = data["results"]
    assert isinstance(results, list)
    
    # If there are results, check their keys and nested structure
    if len(results) > 0:
        book = results[0]
        # Top-level fields
        required_fields = ["title", "authors", "description", "cover_image", "subject", "quality_score", "soul", "distance_score", "soul_match", "hybrid_score", "relevance_confidence", "relevance_reason", "match_reasons"]
        for field in required_fields:
            assert field in book, f"Missing field: {field}"
            
        # Soul fields
        soul = book["soul"]
        assert isinstance(soul, dict)
        soul_fields = ["themes", "tropes", "emotional_tone", "writing_style", "pacing", "character_dynamics", "reader_vibe", "emotional_arc", "dna", "is_fallback", "is_antigravity"]
        for field in soul_fields:
            assert field in soul, f"Missing soul field: {field}"
            
        # DNA fields
        dna = soul["dna"]
        assert isinstance(dna, dict)
        dna_fields = ["emotional_depth", "comfort", "humor", "angst", "spice", "character_growth", "pacing", "atmosphere"]
        for field in dna_fields:
            assert field in dna, f"Missing DNA field: {field}"
            
        # Types and values checking
        assert isinstance(soul["themes"], list)
        assert isinstance(soul["tropes"], list)
        assert isinstance(dna["emotional_depth"], (int, float))
        assert 1 <= dna["emotional_depth"] <= 10
        assert isinstance(soul["is_fallback"], bool)
        assert isinstance(soul["is_antigravity"], bool)
