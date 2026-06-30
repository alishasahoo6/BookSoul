"""
BookSoul DNA Visualization
Generates ASCII bar charts for BookSoul attributes.
"""

from services.book_dna import ensure_book_dna, get_dna_values, infer_dna_from_soul

__all__ = [
    "ensure_book_dna",
    "get_dna_values",
    "infer_dna_from_soul",
    "render_dna_bars",
    "format_dna_display",
]


def render_dna_bars(dna_dict: dict) -> dict:
    """
    Converts BookSoul DNA numeric values to visual bar representations.

    Args:
        dna_dict: {"emotional_depth": 8, "comfort": 6, ...}

    Returns:
        {
            "bars": ["Emotional Depth    ##########", ...],
            "atmosphere": "Cozy Small Town"
        }
    """
    if not dna_dict:
        return {"bars": [], "atmosphere": ""}

    emojis = {
        "emotional_depth": "❤️",
        "comfort": "🏡",
        "humor": "😂",
        "angst": "💔",
        "spice": "🌶",
        "character_growth": "✨",
        "pacing": "⚡",
    }

    labels = {
        "emotional_depth": "Emotional Depth",
        "comfort": "Comfort",
        "humor": "Humor",
        "angst": "Angst",
        "spice": "Spice",
        "character_growth": "Character Growth",
        "pacing": "Pacing",
    }

    bars = []
    for key, emoji in emojis.items():
        if key in dna_dict:
            score = dna_dict[key]
            if isinstance(score, (int, float)):
                score = int(max(0, min(10, score)))
                bar = "█" * score + "░" * (10 - score)
                label = labels.get(key, key)
                bars.append(f"{emoji} {label:<20} {bar}")

    return {
        "bars": bars,
        "atmosphere": dna_dict.get("atmosphere", ""),
    }


def format_dna_display(dna_dict: dict) -> str:
    """Format DNA data as a readable string for UI display."""
    viz = render_dna_bars(dna_dict)
    output = "**BookSoul DNA**\n\n"
    for bar in viz["bars"]:
        output += f"`{bar}`\n"
    if viz["atmosphere"]:
        output += f"\n🌍 **Atmosphere**: {viz['atmosphere']}"
    return output
