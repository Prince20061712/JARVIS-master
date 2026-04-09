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


def classify_query(query: str) -> str:
    """Classify a query into COMMAND, SIMPLE, FAST, or COMPLEX."""
    tokens = _tokenize(query)
    word_count = len(tokens)

    if _contains_any(tokens, COMMAND_KEYWORDS):
        return COMMAND
    if word_count < 8:
        return SIMPLE
    if _contains_any(tokens, FAST_KEYWORDS):
        return FAST
    if _contains_any(tokens, COMPLEX_KEYWORDS) or word_count > 15:
        return COMPLEX
    return SIMPLE
