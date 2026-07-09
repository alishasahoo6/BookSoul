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

    ,
"dark academia": {
    "mood": [
        "dark",
        "atmospheric",
        "intellectual",
        "mysterious"
    ],

    "genres": [
        "Dark Academia",
        "Psychological Thriller",
        "Mystery"
    ],

    "tone": "Gothic",

    "reader_intent":
        "The reader wants an atmospheric mystery set in an academic environment with secrets, intellectual tension, and morally complex characters.",

    "search_terms": [
        "dark academia fiction novel",
        "gothic campus mystery",
        "secret society thriller",
        "elite university mystery novel",
        "psychological dark academia fiction",
        "literary campus thriller",
        "academic conspiracy novel",
        "college murder mystery fiction"
    ]
}
,
"mystery": {
    "mood": [
        "suspenseful",
        "curious"
    ],

    "genres": [
        "Mystery"
    ],

    "tone": "Suspenseful",

    "reader_intent":
        "The reader wants an engaging mystery with clues, investigation, and satisfying twists.",

    "search_terms": [
        "murder mystery novel",
        "detective fiction",
        "whodunit novel",
        "investigative mystery fiction",
        "crime mystery thriller",
        "psychological mystery novel",
        "locked room mystery",
        "suspense mystery fiction"
    ]
}

}