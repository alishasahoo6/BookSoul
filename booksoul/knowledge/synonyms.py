"""
Knowledge registry for rule-based query interpretation.

This file maps common reader words to richer book-reading intent.
The Query Interpreter uses this whenever AI is unavailable.
"""

QUERY_SYNONYMS = {

    "funny": {
        "mood": [
            "humorous",
            "lighthearted"
        ],

        "genres": [
        "Comedy"
        ],

        "tone": "Witty",

        "reader_intent":
            "The reader wants an entertaining, humorous story that is easy to enjoy.",

        "search_terms": [
            "humorous fiction novel",
            "comedy novel",
            "satirical fiction",
            "laugh out loud novel"
        ]
    }

}