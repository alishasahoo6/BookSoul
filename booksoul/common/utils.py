import json
import re
import logging
import time
from typing import Any, Optional
import requests


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a standard logger with a stream handler and custom format.
    
    If the logger already has handlers configured, returns the logger as-is
    to prevent adding duplicate handlers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def parse_json_text(text: Optional[str], fallback: Optional[Any] = None) -> Any:
    """
    Robustly parse JSON data from raw text (commonly received from LLM or API outputs).
    
    This helper cleans up markdown code blocks (fences), removes trailing commas
    before parsing, and handles parsing failures gracefully by returning the
    fallback value.
    """
    if not text:
        return fallback if fallback is not None else {}

    # Remove markdown fences
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to fix trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*\]', ']', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger = setup_logger("JSONParser")
            logger.error("Failed to parse JSON text (error: %s). Content: %r", str(e), text)
            return fallback if fallback is not None else {}
    except Exception:
        logger = setup_logger("JSONParser")
        logger.exception("Unexpected error occurred while parsing JSON text.")
        return fallback if fallback is not None else {}


# Keep backward-compatible alias so any remaining callers still work
parse_gemini_json = parse_json_text


def request_with_retry(
    method: str,
    url: str,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    **kwargs: Any
) -> requests.Response:
    """
    Perform an HTTP request with automatic retries and exponential backoff.
    
    Retries on connection issues, timeouts, rate-limiting (status 429), or temporary
    server failures (status 503).
    """
    logger = setup_logger("HTTPRetry")
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)

            if response.status_code in (429, 503):
                if attempt < max_retries - 1:
                    logger.warning(
                        "HTTP %d received. Retrying in %.1fs... (Attempt %d/%d)",
                        response.status_code,
                        backoff,
                        attempt + 1,
                        max_retries
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                logger.warning(
                    "Request failed with %s. Retrying in %.1fs... (Attempt %d/%d)",
                    type(e).__name__,
                    backoff,
                    attempt + 1,
                    max_retries
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                raise
        except Exception:
            logger.exception("Unexpected exception encountered during HTTP request.")
            raise

    return requests.request(method, url, **kwargs)

