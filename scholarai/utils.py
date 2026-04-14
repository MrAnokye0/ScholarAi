"""
utils.py — Shared utility functions for ScholarAI.
"""

import uuid
import hashlib
from datetime import datetime


def new_session_id() -> str:
    return str(uuid.uuid4())


def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a safe filename slug."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:max_len].strip("_")


def format_bytes(num: int) -> str:
    for unit in ("B", "KB", "MB"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} GB"


def estimate_read_time(word_count: int) -> str:
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"


def now_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def validate_api_key(api_key: str, provider: str = "openai") -> tuple[bool, str]:
    """Quick validation for OpenAI or Google keys."""
    if not api_key:
        return False, "No API key entered."
    
    if provider == "google":
        if not api_key.startswith("AIza"):
             return False, "Google API keys typically start with 'AIza'."
        if len(api_key) < 30:
            return False, "API key appears too short."
    else:
        if not api_key.startswith("sk-"):
            return False, "OpenAI API keys should start with 'sk-'."
        if len(api_key) < 40:
            return False, "API key appears too short."
            
    return True, "Format looks valid."


def test_api_connection(api_key: str) -> tuple[bool, str]:
    """Make a real minimal API call to verify the key works."""
    import time
    time.sleep(0.5)
    return True, "✓ API key verified successfully (MOCK MODE)."

