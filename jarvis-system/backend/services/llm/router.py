"""Query router for hybrid model selection."""

from __future__ import annotations

import re
from typing import Iterable

COMMAND = "COMMAND"
SIMPLE = "SIMPLE"
FAST = "FAST"
COMPLEX = "COMPLEX"

COMMAND_KEYWORDS = {"open", "close", "play", "launch", "search"}
FAST_KEYWORDS = {"quick", "fast", "latest", "current"}
COMPLEX_KEYWORDS = {"explain", "why", "how", "optimize", "code", "architecture"}


def _tokenize(query: str) -> list[str]:
    return re.findall(r"\b\w+\b", query.lower())


def _contains_any(tokens: Iterable[str], keywords: set[str]) -> bool:
    return any(token in keywords for token in tokens)


def _is_command_query(query: str) -> bool:
    """Match actionable command phrasing, not incidental keyword mentions."""
    pattern = (
        r"^(?:hey\s+jarvis\s+|jarvis\s+)?"
        r"(?:please\s+)?"
        r"(?:(?:can|could|would)\s+you\s+)?"
        r"(?:please\s+)?"
        r"(?:open|close|play|launch|search)\b"
    )
    return re.match(pattern, query.strip(), flags=re.IGNORECASE) is not None


def classify_query(query: str) -> str:
    """Classify a query into COMMAND, SIMPLE, FAST, or COMPLEX."""
    tokens = _tokenize(query)
    word_count = len(tokens)

    if _is_command_query(query):
        return COMMAND
    if word_count < 8:
        return SIMPLE
    if _contains_any(tokens, FAST_KEYWORDS):
        return FAST
    if _contains_any(tokens, COMPLEX_KEYWORDS) or word_count > 15:
        return COMPLEX
    return SIMPLE
