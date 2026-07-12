import os
from dotenv import load_dotenv
from booksoul.common.utils import setup_logger

logger = setup_logger("ConfigSettings")

# Load environment variables from .env file if available
load_dotenv()

GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")

if not GOOGLE_BOOKS_API_KEY:
    logger.warning("GOOGLE_BOOKS_API_KEY environment variable is not set. API requests will be unauthenticated and may be rate-limited.")
else:
    logger.info("GOOGLE_BOOKS_API_KEY environment variable successfully loaded.")

