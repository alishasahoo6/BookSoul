"""Environment-backed settings for BookSoul."""

import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")

