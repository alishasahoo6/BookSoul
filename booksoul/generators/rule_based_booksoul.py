import re
from booksoul.models.book_dna import ensure_book_dna

GENRES_CONFIG = {
    "Romance": {
        "category_keywords": ["romance", "love", "contemporary romance", "historical romance", "romantic comedy", "chick lit"],
        "text_keywords": ["love", "heartfelt", "slow burn", "friends to lovers", "enemies to lovers", "fake dating", "marriage", "relationship", "date", "sweetheart", "cozy", "grumpy", "sunshine"],
        "base_dna": {
            "emotional_depth": 6,
            "comfort": 7,
            "humor": 5,
            "angst": 5,
            "spice": 6,
            "character_growth": 7,
            "pacing": 6,
            "atmosphere": "Warm, tender, and emotionally satisfying"
        },
        "themes": ["Love & Romance", "Intimacy", "Emotional Healing", "Human Connection"],
        "tropes": ["Enemies to Lovers", "Friends to Lovers", "Fake Dating", "Forced Proximity", "Slow Burn"],
        "reader_vibe": "Cozy & Emotionally Uplifting",
        "writing_style": "Character-Driven & Warm",
        "emotional_tone": "Warm, Sweet & Heartfelt"
    },
    "Dark Romance": {
        "category_keywords": ["dark romance", "gothic romance", "taboo romance"],
        "text_keywords": ["monster", "morally grey", "dangerous", "obsession", "possessive", "protective", "alpha", "touch her and die", "kidnapping", "stalker", "mafia", "billionaire", "ceo", "bodyguard", "dark romance", "secret", "lies", "betrayal", "forced proximity", "grumpy", "sunshine", "slow burn", "enemies", "hate", "revenge"],
        "base_dna": {
            "emotional_depth": 8,
            "comfort": 2,
            "humor": 2,
            "angst": 9,
            "spice": 9,
            "character_growth": 7,
            "pacing": 7,
            "atmosphere": "Dark, intense, and emotionally raw"
        },
        "themes": ["Obsession", "Redemption", "Trust & Betrayal", "Power & Control"],
        "tropes": ["Morally Grey Hero", "Possessive Alpha", "Forced Proximity", "Enemies to Lovers"],
        "reader_vibe": "Taboo & Obsessive Passion",
        "writing_style": "Gothic & Highly Charged",
        "emotional_tone": "Tense, Dark & Seductive"
    },
    "Fantasy": {
        "category_keywords": ["fantasy", "magic", "mythology", "fairy tale", "high fantasy", "urban fantasy", "epic fantasy"],
        "text_keywords": ["dragon", "magic", "academy", "witch", "kingdom", "curse", "prophecy", "sword", "prince", "fae", "immortal", "spells", "wizard", "quest", "empire"],
        "base_dna": {
            "emotional_depth": 7,
            "comfort": 5,
            "humor": 4,
            "angst": 6,
            "spice": 3,
            "character_growth": 8,
            "pacing": 6,
            "atmosphere": "Wondrous, mystical, and expansive"
        },
        "themes": ["Good vs Evil", "Destiny & Prophecy", "Power & Corruption", "Sacrifice"],
        "tropes": ["The Chosen One", "Found Family", "Magic Academy", "Quest & Journey"],
        "reader_vibe": "Immersive Magical Escape",
        "writing_style": "Richly Detailed & World-Building",
        "emotional_tone": "Wondrous, Mystical & Adventurous"
    },
    "Mystery": {
        "category_keywords": ["mystery", "detective", "crime fiction", "cozy mystery", "whodunit"],
        "text_keywords": ["secret", "clue", "investigation", "disappearance", "hidden", "detective", "murder", "whodunit", "puzzle", "truth", "lies", "conspiracy", "locked room"],
        "base_dna": {
            "emotional_depth": 6,
            "comfort": 4,
            "humor": 3,
            "angst": 7,
            "spice": 2,
            "character_growth": 6,
            "pacing": 6,
            "atmosphere": "Intriguing, suspenseful, and puzzle-like"
        },
        "themes": ["Truth & Deception", "Secrets & Lies", "Moral Ambiguity", "Obsession with Truth"],
        "tropes": ["Locked Room Mystery", "Red Herring", "Whodunit", "Unreliable Narrator"],
        "reader_vibe": "Intellectual Puzzle & Suspense",
        "writing_style": "Suspense-Driven & Intricate",
        "emotional_tone": "Curious, Suspenseful & Introspective"
    },
    "Thriller": {
        "category_keywords": ["thriller", "suspense", "action", "adventure", "espionage"],
        "text_keywords": ["killer", "murder", "crime", "serial killer", "detective", "investigation", "missing", "psychological", "ticking clock", "danger", "deadly", "hunter", "chase", "survival"],
        "base_dna": {
            "emotional_depth": 6,
            "comfort": 2,
            "humor": 2,
            "angst": 8,
            "spice": 2,
            "character_growth": 6,
            "pacing": 9,
            "atmosphere": "Fast-paced, high-stakes, and nerve-wracking"
        },
        "themes": ["Survival Instincts", "Justice & Retribution", "Mortality", "Paranoia"],
        "tropes": ["Cat and Mouse", "Race Against Time", "Unreliable Narrator", "Deadly Game"],
        "reader_vibe": "High-Stakes Intense Action",
        "writing_style": "Fast-Paced & Gripping",
        "emotional_tone": "Anxious, Tense & Adrenaline-Fuelled"
    },
    "Sci-Fi": {
        "category_keywords": ["science fiction", "sci-fi", "space", "futuristic", "cyberpunk", "dystopian", "aliens", "technology"],
        "text_keywords": ["future", "technology", "space", "star", "planet", "galaxy", "alien", "dystopian", "robot", "artificial intelligence", "ai", "cyberpunk", "clone", "time travel"],
        "base_dna": {
            "emotional_depth": 6,
            "comfort": 4,
            "humor": 3,
            "angst": 6,
            "spice": 2,
            "character_growth": 7,
            "pacing": 7,
            "atmosphere": "Intellectual, speculative, and technological"
        },
        "themes": ["Technological Ethics", "What Makes Us Human", "Society & Control", "Cosmic Wonder"],
        "tropes": ["Dystopian Future", "Space Opera", "First Contact", "Time Loop"],
        "reader_vibe": "Mind-Bending Futuristic Escape",
        "writing_style": "Concept-Driven & Speculative",
        "emotional_tone": "Intriguing, Speculative & Cosmic"
    },
    "Historical Fiction": {
        "category_keywords": ["historical fiction", "history", "historical", "war", "period piece"],
        "text_keywords": ["history", "century", "war", "past", "ancient", "era", "generation", "monarchy", "revolution", "historical"],
        "base_dna": {
            "emotional_depth": 8,
            "comfort": 5,
            "humor": 3,
            "angst": 7,
            "spice": 3,
            "character_growth": 8,
            "pacing": 5,
            "atmosphere": "Richly atmospheric, nostalgic, and grounded"
        },
        "themes": ["Legacy & Heritage", "Social Change & Class", "Resilience & Survival", "Echoes of the Past"],
        "tropes": ["Cross-Class Romance", "War & Separation", "Coming of Age in History"],
        "reader_vibe": "Thoughtful & Atmospheric Journey",
        "writing_style": "Atmospheric & Descriptive",
        "emotional_tone": "Reflective, Poignant & Grounded"
    },
    "Horror": {
        "category_keywords": ["horror", "ghost", "supernatural", "gothic", "monster", "vampire", "slasher", "creature"],
        "text_keywords": ["ghost", "haunted", "monster", "demon", "blood", "death", "darkness", "terror", "creature", "curse", "possession", "nightmare", "paranormal", "fear"],
        "base_dna": {
            "emotional_depth": 7,
            "comfort": 1,
            "humor": 2,
            "angst": 9,
            "spice": 2,
            "character_growth": 6,
            "pacing": 7,
            "atmosphere": "Terrifying, chilling, and visceral"
        },
        "themes": ["Fear & Paranoia", "The Unknown", "Mortality & Decay", "Survival at All Costs"],
        "tropes": ["Haunted House", "Slasher", "Gothic Dread", "Cursed Object"],
        "reader_vibe": "Chilling Gothic Dread",
        "writing_style": "Visceral & Atmospheric",
        "emotional_tone": "Terrifying, Tense & Unsettling"
    },
    "Young Adult": {
        "category_keywords": ["young adult", "ya", "teen", "juvenile", "high school", "coming of age"],
        "text_keywords": ["high school", "teen", "coming of age", "growing up", "first love", "friendship", "identity", "school", "camp", "academy"],
        "base_dna": {
            "emotional_depth": 6,
            "comfort": 6,
            "humor": 5,
            "angst": 6,
            "spice": 2,
            "character_growth": 8,
            "pacing": 6,
            "atmosphere": "Vibrant, emotional, and self-reflective"
        },
        "themes": ["Identity & Self-Discovery", "Coming of Age", "Belonging", "First Love"],
        "tropes": ["Coming of Age", "High School Rivalry", "Love Triangle", "Found Family"],
        "reader_vibe": "Emotionally Charged Coming-of-Age",
        "writing_style": "Accessible, Direct & Relatable",
        "emotional_tone": "Vulnerable, Turbulent & Hopeful"
    },
    "Non-fiction": {
        "category_keywords": ["nonfiction", "non-fiction", "self-help", "habits", "business", "biography", "memoir", "psychology", "science", "guide", "education", "economics"],
        "text_keywords": ["learn", "guide", "habit", "success", "how to", "mindset", "science", "biography", "memoir", "history", "economics", "productivity", "management", "personal growth"],
        "base_dna": {
            "emotional_depth": 5,
            "comfort": 6,
            "humor": 3,
            "angst": 3,
            "spice": 1,
            "character_growth": 8,
            "pacing": 5,
            "atmosphere": "Empowering, educational, and practical"
        },
        "themes": ["Personal Transformation", "Continuous Learning", "Self-Mastery", "Real-world Success"],
        "tropes": ["Real-life Inspiration", "Habit Formation", "Case Studies", "Actionable Strategy"],
        "reader_vibe": "Motivational & Insightful",
        "writing_style": "Clear, Structured & Actionable",
        "emotional_tone": "Informative, Empowering & Practical"
    }
}

KEYWORD_RULES = {
    # Dark Romance keywords
    "mafia": {"dna": {"spice": 2, "angst": 2}, "tropes": ["Mafia Romance"]},
    "billionaire": {"dna": {"spice": 1}, "tropes": ["Billionaire Romance"]},
    "ceo": {"dna": {"spice": 1}, "tropes": ["Billionaire Romance"]},
    "bodyguard": {"dna": {"comfort": 1}, "tropes": ["Bodyguard Romance"]},
    "touch her and die": {"dna": {"angst": 1}, "tropes": ["Touch Her and Die"]},
    "stalker": {"dna": {"angst": 2, "comfort": -1}, "tropes": ["Stalker Romance"]},
    "monster": {"dna": {"angst": 1}, "tropes": ["Monster Romance"]},
    "morally grey": {"dna": {"angst": 1}, "tropes": ["Morally Grey Hero"]},
    "possessive": {"dna": {"angst": 1}, "tropes": ["Possessive Alpha"]},
    "protective": {"dna": {"comfort": 1}, "tropes": ["Protective Hero"]},
    
    # Romance keywords
    "slow burn": {"dna": {"pacing": -1, "angst": 1}, "tropes": ["Slow Burn Romance"]},
    "fake dating": {"dna": {"humor": 1}, "tropes": ["Fake Dating"]},
    "friends to lovers": {"dna": {"comfort": 1}, "tropes": ["Friends to Lovers"]},
    "enemies to lovers": {"dna": {"angst": 1}, "tropes": ["Enemies to Lovers"]},
    "grumpy": {"dna": {"humor": 1}, "tropes": ["Grumpy x Sunshine"]},
    "sunshine": {"dna": {"comfort": 1}, "tropes": ["Grumpy x Sunshine"]},
    "forced proximity": {"dna": {"angst": 1}, "tropes": ["Forced Proximity"]},
    
    # Fantasy keywords
    "dragon": {"dna": {"pacing": 1}, "themes": ["Magic"], "tropes": ["Dragon Lore"]},
    "magic": {"dna": {"emotional_depth": 1}, "themes": ["Magic & Wonder"]},
    "academy": {"tropes": ["Magic Academy"]},
    "witch": {"tropes": ["Witchcraft & Sorcery"]},
    "curse": {"dna": {"angst": 1}, "themes": ["Destiny & Curse"]},
    "prophecy": {"tropes": ["The Chosen One"]},
    "chosen one": {"tropes": ["The Chosen One"]},
    "found family": {"dna": {"comfort": 1}, "tropes": ["Found Family"]},
    
    # Thriller keywords
    "killer": {"dna": {"angst": 1}, "tropes": ["Cat and Mouse"]},
    "serial killer": {"dna": {"angst": 2, "comfort": -1}, "tropes": ["Cat and Mouse"]},
    "murder": {"dna": {"angst": 1}, "themes": ["Mortality"]},
    "detective": {"tropes": ["Police Procedural"]},
    "investigation": {"themes": ["Justice & Retribution"]},
    "clock ticking": {"dna": {"pacing": 2}, "tropes": ["Race Against Time"]},
    "ticking clock": {"dna": {"pacing": 2}, "tropes": ["Race Against Time"]},
    "race": {"dna": {"pacing": 1}, "tropes": ["Race Against Time"]},
    "survival": {"themes": ["Survival Instincts"]},
    
    # Mystery keywords
    "secret": {"dna": {"angst": 1}, "themes": ["Secrets & Lies"]},
    "lies": {"themes": ["Secrets & Lies"]},
    "clue": {"tropes": ["Intellectual Whodunit"]},
    "disappearance": {"tropes": ["Missing Person Mystery"]},
    "locked room": {"tropes": ["Locked Room Mystery"]},
    
    # Sci-Fi keywords
    "ai": {"themes": ["Technological Ethics"]},
    "robot": {"themes": ["Technological Ethics"]},
    "artificial intelligence": {"themes": ["Technological Ethics"]},
    "space": {"tropes": ["Space Opera"]},
    "alien": {"tropes": ["First Contact"]},
    "dystopian": {"dna": {"angst": 1}, "tropes": ["Dystopian Future"]},
    
    # Historical Fiction keywords
    "war": {"dna": {"angst": 2}, "themes": ["Survival Instincts"]},
    "history": {"themes": ["Legacy & Heritage"]},
    "monarchy": {"tropes": ["Monarchical Court Intrigue"]},
    
    # Horror keywords
    "haunted": {"dna": {"angst": 1}, "tropes": ["Haunted House"]},
    "ghost": {"tropes": ["Paranormal Haunting"]},
    
    # Young Adult keywords
    "high school": {"tropes": ["High School Drama"]},
    "teen": {"themes": ["Identity & Self-Discovery"]},
    "coming of age": {"themes": ["Coming of Age"]},
    
    # Non-fiction keywords
    "habit": {"themes": ["Personal Transformation"], "tropes": ["Habit Formation"]},
    "habits": {"themes": ["Personal Transformation"], "tropes": ["Habit Formation"]},
    "productivity": {"tropes": ["Actionable Strategy"]},
}

def generate_book_soul(book):
    """
    Generates a rule-based BookSoul fallback using a modular genre configurations
    and keyword scoring matrix, returning the exact same schema structure.
    """
    if not isinstance(book, dict):
        book = {}
        
    title = book.get("title", "") or ""
    description = book.get("description", "") or ""
    categories = book.get("categories", []) or []
    
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",") if c.strip()]
    elif not isinstance(categories, list):
        categories = []
        
    title_lower = title.lower()
    description_lower = description.lower()
    categories_lower = [c.lower() for c in categories]
    combined_text = f"{title_lower} {description_lower} {' '.join(categories_lower)}"
    
    # 1. Detect Genres and calculate matching score
    active_genres = []
    genre_scores = {}
    
    for genre_name, config in GENRES_CONFIG.items():
        score = 0
        
        # Category matches (highest weight)
        for cat_kw in config["category_keywords"]:
            for book_cat in categories_lower:
                if cat_kw in book_cat:
                    score += 15
                    
        # Keyword matches in title
        for kw in config["text_keywords"]:
            if kw in title_lower:
                score += 5
                
        # Keyword matches in description
        for kw in config["text_keywords"]:
            if kw in description_lower:
                score += 2
                
        if score > 0:
            genre_scores[genre_name] = score
            active_genres.append(genre_name)
            
    # Default if no genre matched
    if not active_genres:
        nonfiction_indicators = ["self-help", "habits", "business", "biography", "memoir", "psychology", "science", "guide", "education", "economics"]
        if any(ind in combined_text for ind in nonfiction_indicators):
            primary_genre = "Non-fiction"
        else:
            primary_genre = "Romance"
        active_genres = [primary_genre]
        genre_scores = {primary_genre: 1}
    else:
        # Sort active genres by score descending
        active_genres.sort(key=lambda g: genre_scores[g], reverse=True)
        primary_genre = active_genres[0]
        
    # 2. Merge Base DNA, Themes, Tropes
    dna = {
        "emotional_depth": 5.0,
        "comfort": 5.0,
        "humor": 5.0,
        "angst": 5.0,
        "spice": 5.0,
        "character_growth": 5.0,
        "pacing": 5.0,
        "atmosphere": ""
    }
    
    sum_dna = {k: 0.0 for k in dna if k != "atmosphere"}
    for g in active_genres:
        base = GENRES_CONFIG[g]["base_dna"]
        for k in sum_dna:
            sum_dna[k] += base[k]
            
    num_genres = len(active_genres)
    for k in sum_dna:
        dna[k] = sum_dna[k] / num_genres
        
    # Combine atmospheres
    atmospheres = [GENRES_CONFIG[g]["base_dna"]["atmosphere"] for g in active_genres if GENRES_CONFIG[g]["base_dna"].get("atmosphere")]
    dna["atmosphere"] = atmospheres[0] if atmospheres else "Engaging and immersive"
    
    # Combine themes and tropes
    themes = []
    tropes = []
    for g in active_genres:
        themes.extend(GENRES_CONFIG[g]["themes"])
        tropes.extend(GENRES_CONFIG[g]["tropes"])
        
    # 3. Apply Keyword-based specific rules
    for kw, rule in KEYWORD_RULES.items():
        # Match using word boundaries or simple substring for multi-word phrases
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, title_lower) or re.search(pattern, description_lower):
            if "dna" in rule:
                for k, delta in rule["dna"].items():
                    if k in dna:
                        dna[k] += delta
            if "themes" in rule:
                themes.extend(rule["themes"])
            if "tropes" in rule:
                tropes.extend(rule["tropes"])
                
    # Clamping DNA values to 1-10 integers
    for k in ["emotional_depth", "comfort", "humor", "angst", "spice", "character_growth", "pacing"]:
        dna[k] = max(1, min(10, int(round(dna[k]))))
        
    # Clean and de-duplicate themes and tropes
    themes = list(dict.fromkeys(themes))
    tropes = list(dict.fromkeys(tropes))
    
    themes = themes[:5]
    tropes = tropes[:5]
    
    # 4. Fill other fields based on primary genre and keyword modifications
    primary_config = GENRES_CONFIG.get(primary_genre, GENRES_CONFIG["Romance"])
    
    reader_vibe = primary_config["reader_vibe"]
    writing_style = primary_config["writing_style"]
    emotional_tone = primary_config["emotional_tone"]
    
    # Adjust reader vibe specifically if multiple active genres are merged
    if len(active_genres) > 1:
        genres_set = set(active_genres)
        if "Thriller" in genres_set and "Romance" in genres_set:
            reader_vibe = "High-Stakes Romantic Suspense"
        elif "Fantasy" in genres_set and "Romance" in genres_set:
            reader_vibe = "Immersive Romantic Fantasy"
        elif "Dark Romance" in genres_set and "Thriller" in genres_set:
            reader_vibe = "High-Stakes Taboo Passion"
            
    pacing_score = dna["pacing"]
    if pacing_score >= 8:
        pacing = "Fast"
    elif pacing_score <= 4:
        pacing = "Steady"
    else:
        pacing = "Moderate"
        
    # Character Dynamics
    if "enemies" in description_lower or "rival" in description_lower:
        character_dynamics = "High-Tension Enemies-to-Lovers"
    elif "friends" in description_lower:
        character_dynamics = "Comforting Friends-to-Lovers"
    elif primary_genre in ["Thriller", "Mystery", "Horror"]:
        character_dynamics = "Paranoid & High-Stakes Rivalry"
    elif primary_genre == "Non-fiction":
        character_dynamics = "Actionable Self-Reflection"
    else:
        character_dynamics = "Evolving & Relatable"
        
    # Emotional Arc
    if "healing" in description_lower or "grief" in description_lower:
        emotional_arc = "Loss to Hopeful Healing"
    elif primary_genre in ["Thriller", "Mystery"]:
        emotional_arc = "Tension to Resolution"
    elif primary_genre in ["Romance", "Dark Romance"]:
        emotional_arc = "Slow-Building Intimacy & Trust"
    elif primary_genre == "Fantasy":
        emotional_arc = "Heroic Triumph & Sacrifice"
    else:
        emotional_arc = "Transformative Journey"
        
    soul = {
        "themes": themes,
        "tropes": tropes,
        "emotional_tone": emotional_tone,
        "writing_style": writing_style,
        "pacing": pacing,
        "character_dynamics": character_dynamics,
        "reader_vibe": reader_vibe,
        "emotional_arc": emotional_arc,
        "dna": dna,
        "is_fallback": True,
        "is_antigravity": True
    }
    
    # Ensure all required DNA properties are present
    ensure_book_dna(soul, description=description, categories=categories)
    
    # Ensure correct flags remain set
    soul["is_fallback"] = True
    soul["is_antigravity"] = True
    
    return soul
