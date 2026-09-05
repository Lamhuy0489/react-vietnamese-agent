"""File-backed synthetic document store."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from react_agent.environment.search import lexical_score


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    title: str
    content: str


class DocumentStore:
    def __init__(self, documents: list[Document]) -> None:
        self._documents = {document.doc_id: document for document in documents}

    @classmethod
    def from_json(cls, path: Path) -> DocumentStore:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([Document.model_validate(item) for item in raw])

    def get(self, doc_id: str) -> Document | None:
        return self._documents.get(doc_id)

    def search(self, query: str, top_k: int) -> list[dict[str, object]]:
        scored = []
        for document in self._documents.values():
            score = lexical_score(query, document.title, document.content)
            if score > 0:
                scored.append((score, document.doc_id, document))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            {
                "doc_id": document.doc_id,
                "title": document.title,
                "score": score,
                "snippet": document.content[:180],
            }
            for score, _, document in scored[:top_k]
        ]
