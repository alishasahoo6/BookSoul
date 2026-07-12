import json
import re
import logging
import time
import requests


def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def parse_json_text(text, fallback=None):
    """
    Robust JSON parser for LLM / API output.
    - Removes markdown fences
    - Removes trailing commas
    - Strips whitespace
    """
    if not text:
        return fallback or {}

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
            logger.error(f"Failed to parse JSON: {e}")
            return fallback or {}


# Keep backward-compatible alias so any remaining callers still work
parse_gemini_json = parse_json_text


def request_with_retry(method, url, max_retries=3, initial_backoff=1.0, **kwargs):
    """
    Wrapper around requests with connection error retry and exponential backoff
    for rate-limiting (429) or temporary server errors (503).
    """
    logger = setup_logger("HTTPRetry")
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)

            if response.status_code in (429, 503):
                if attempt < max_retries - 1:
                    logger.warning(
                        f"HTTP {response.status_code} received. Retrying in {backoff:.1f}s... "
                        f"(Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Request failed with {type(e).__name__}. Retrying in {backoff:.1f}s... "
                    f"(Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                raise

    return requests.request(method, url, **kwargs)
