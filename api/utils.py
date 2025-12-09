# api/utils.py
import re
from typing import Any

def safe_truncate(text: str, n: int = 2000) -> str:
    return text if len(text) <= n else text[:n] + "..."

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_\-\.]', '_', name)
