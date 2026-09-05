"""Offline cached-page store; never performs HTTP requests."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from react_agent.environment.search import lexical_score


class CachedPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_id: str
    title: str
    content: str
    source_url: str


class CacheStore:
    def __init__(self, pages: list[CachedPage]) -> None:
        self._pages = {page.page_id: page for page in pages}

    @classmethod
    def from_json(cls, path: Path) -> CacheStore:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([CachedPage.model_validate(item) for item in raw])

    def get(self, page_id: str) -> CachedPage | None:
        return self._pages.get(page_id)

    def search(self, query: str, top_k: int) -> list[dict[str, object]]:
        scored = []
        for page in self._pages.values():
            score = lexical_score(query, page.title, page.content)
            if score > 0:
                scored.append((score, page.page_id, page))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            {
                "page_id": page.page_id,
                "title": page.title,
                "score": score,
                "snippet": page.content[:180],
            }
            for score, _, page in scored[:top_k]
        ]
