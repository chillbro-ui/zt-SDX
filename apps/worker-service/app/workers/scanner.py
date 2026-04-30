import re
from typing import Tuple


# DLP Pattern definitions
PATTERNS = {
    "PAN": {
        "regex": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
        "description": "Payment Card Number (Visa, Mastercard, Amex)",
    },
    "AADHAAR": {
        "regex": r"\b[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4}\b",
        "description": "Aadhaar Number (India)",
    },
    "API_KEY": {
        "regex": r"\b(eyJ[A-Za-z0-9_-]{1,100}\.eyJ[A-Za-z0-9_-]{1,100})\b",
        "description": "JWT / Bearer token in content",
    },
    "PASSWORD": {
        "regex": r"(?i)(password|passwd|pwd)\s*[=:]\s*[^\s]+",
        "description": "Password literal in text",
    },
    "SSN": {
        "regex": r"\b\d{3}-\d{2}-\d{4}\b",
        "description": "Social Security Number (US)",
    },
}


def scan_content(content: str) -> Tuple[bool, list]:
    """
    Scan text content for DLP patterns.
    Returns (is_clean, matches_list).
    is_clean=True means no sensitive patterns found.
    """
    matches = []

    for pattern_name, pattern_info in PATTERNS.items():
        found = re.findall(pattern_info["regex"], content, re.IGNORECASE)
        if found:
            matches.append({
                "pattern": pattern_name,
                "description": pattern_info["description"],
                "count": len(found),
            })

    return len(matches) == 0, matches
