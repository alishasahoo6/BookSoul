import json
import re
import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def parse_gemini_json(text, fallback=None):
    """
    Robust JSON parser for Gemini output.
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
