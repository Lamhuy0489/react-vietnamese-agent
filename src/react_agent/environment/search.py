"""Small deterministic lexical search shared by local stores."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def tokens(text: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(text)}


def lexical_score(query: str, title: str, content: str) -> float:
    query_tokens = tokens(query)
    if not query_tokens:
        return 0.0
    title_overlap = len(query_tokens & tokens(title))
    content_overlap = len(query_tokens & tokens(content))
    return float(title_overlap * 2 + content_overlap)
