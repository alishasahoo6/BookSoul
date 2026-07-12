"""Environment-backed settings for BookSoul."""

import os

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")
