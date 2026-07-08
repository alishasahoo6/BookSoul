"""BookSoul DNA scoring and guarantee helpers."""

_DNA_KEYS = (
    "emotional_depth", "comfort", "humor", "angst",
    "spice", "character_growth", "pacing",
)

_INFER_RULES = {
    "emotional_depth": {
        "pos": ["heartbreaking", "emotional", "deeply", "raw", "vulnerable",
                "poignant", "moving", "grief", "loss", "longing", "profound",
                "resonant", "introspective", "charged", "heartfelt"],
        "neg": ["light", "surface", "informative", "neutral"],
    },
    "comfort": {
        "pos": ["cozy", "comfort", "warm", "heartwarming", "wholesome",
                "gentle", "tender", "uplifting", "hopeful", "safe"],
        "neg": ["dark", "horror", "gritty", "disturbing", "bleak",
                "violent", "unsettling", "brutal", "intense"],
    },
    "humor": {
        "pos": ["funny", "humor", "humour", "witty", "comedy", "laugh",
                "banter", "playful", "lighthearted", "hilarious", "sharp"],
        "neg": ["serious", "grim", "somber", "tragic", "dark"],
    },
    "angst": {
        "pos": ["angst", "turmoil", "conflict", "tension", "anxious",
                "heartbreak", "betrayal", "forbidden", "drama", "tragic",
                "grief", "trauma", "longing", "unresolved"],
        "neg": ["peaceful", "cozy", "wholesome", "lighthearted", "optimistic"],
    },
    "spice": {
        "pos": ["steamy", "spicy", "passionate", "explicit", "sensual",
                "chemistry", "seduction", "heat", "intimate", "romance",
                "desire", "slow burn", "slow-burn"],
        "neg": ["clean", "wholesome", "fade to black", "innocent", "chaste",
                "family friendly"],
    },
    "character_growth": {
        "pos": ["growth", "arc", "transformation", "coming-of-age",
                "self-discovery", "redemption", "journey", "evolve",
                "character-driven", "development", "empowering"],
        "neg": ["static", "episodic", "plot-driven only"],
    },
    "pacing": {
        "pos": ["fast-paced", "fast paced", "gripping", "page-turner",
                "propulsive", "breathless", "non-stop", "kinetic"],
        "neg": ["slow", "deliberate", "leisurely", "contemplative",
                "measured", "steady"],
    },
}


def get_dna_values(dna_dict: dict) -> dict:
    """Return normalized DNA values with safe defaults."""
    dna_dict = dna_dict if isinstance(dna_dict, dict) else {}
    return {
        "emotional_depth": dna_dict.get("emotional_depth", 5),
        "comfort": dna_dict.get("comfort", 5),
        "humor": dna_dict.get("humor", 5),
        "angst": dna_dict.get("angst", 5),
        "spice": dna_dict.get("spice", 5),
        "character_growth": dna_dict.get("character_growth", 5),
        "pacing": dna_dict.get("pacing", 5),
        "atmosphere": dna_dict.get("atmosphere", ""),
    }


def _score_from_text(text: str, pos: list, neg: list, baseline: int = 5) -> int:
    score = baseline
    for kw in pos:
        if kw in text:
            score += 1
    for kw in neg:
        if kw in text:
            score -= 1
    return max(0, min(10, score))


def _pacing_from_label(pacing: str) -> int:
    p = (pacing or "").lower()
    if "fast" in p or "gripping" in p or "propulsive" in p:
        return 8
    if "slow" in p or "deliberate" in p or "steady" in p:
        return 4
    if "varied" in p or "moderate" in p:
        return 6
    return 5


def infer_dna_from_soul(soul: dict, description: str = "", categories=None) -> dict:
    """Infer numeric DNA scores from soul metadata and book text."""
    categories = categories or []
    soul = soul if isinstance(soul, dict) else {}

    parts = [
        description or "",
        " ".join(categories),
        " ".join(soul.get("themes", [])),
        " ".join(soul.get("tropes", [])),
        soul.get("reader_vibe", ""),
        soul.get("writing_style", ""),
        soul.get("emotional_tone", ""),
        soul.get("pacing", ""),
        soul.get("emotional_arc", ""),
        soul.get("character_dynamics", ""),
    ]
    text = " ".join(str(p) for p in parts).lower()

    dna = {}
    for key in _DNA_KEYS:
        rules = _INFER_RULES[key]
        dna[key] = _score_from_text(text, rules["pos"], rules["neg"])

    if soul.get("pacing"):
        dna["pacing"] = _pacing_from_label(soul.get("pacing", ""))

    dna["atmosphere"] = (
        soul.get("emotional_tone")
        or soul.get("reader_vibe")
        or (categories[0] if categories else "")
        or "Balanced"
    )
    return dna


def ensure_book_dna(soul: dict, description: str = "", categories=None) -> dict:
    """Guarantee a complete DNA dict on the soul object."""
    if not isinstance(soul, dict):
        soul = {}

    existing = soul.get("dna")
    if isinstance(existing, dict):
        has_scores = any(
            isinstance(existing.get(k), (int, float)) for k in _DNA_KEYS
        )
        if has_scores:
            dna = get_dna_values(existing)
            soul["dna"] = dna
            return dna

    dna = infer_dna_from_soul(soul, description, categories)
    soul["dna"] = dna
    return dna
