from booksoul.vector.embeddings import prepare_soul_text

soul_json = {
    "genre": "Dark Academia Thriller",
    "themes": ["Secret Society", "Murder", "Privilege"],
    "tropes": ["Campus Mystery", "Elite University"],
    "writing_style": "Atmospheric",
    "emotional_tone": "Dark",
    "pacing": "Slow Burn",
    "character_dynamics": "Strong Female Lead",
    "reader_vibe": "Psychological suspense",
    "emotional_arc": "Truth vs Deception",
    "atmosphere": "Gothic University",
    "setting": "Elite College",
    "core_premise": "A student uncovers a deadly secret society.",
    "character_archetypes": ["Investigator", "Morally Grey Students"],
    "emotional_depth": 8,
    "comfort": 2,
    "humor": 1,
    "angst": 8,
    "spice": 2,
    "character_growth": 7,
}

print(prepare_soul_text("Society of Lies", soul_json))