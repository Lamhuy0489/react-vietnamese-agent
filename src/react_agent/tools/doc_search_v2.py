"""Environment E2: ``doc_search`` that also reports exact identifier matches.

Decision log 2026-10-28 (decision E2). The pinned ``doc_search`` scores words only, so a
query such as ``AWB_X`` for a cached page or a table row returns ``[]`` and the agent
gives up. E2 wraps whatever ``doc_search`` the fixture registry holds (overlays and
faults included) and keeps its name, description and input schema, so prompts, tool
definitions and security policies see the same tool. A successful result keeps the
lexical ``results`` and adds ``id_matches``: for each identifier in the query that
names a document, cached page or database row exactly, where it lives and which tool
reads it. Only identities are returned, never content.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from react_agent.schemas.tool import ToolResult
from react_agent.tools.base import BaseTool
from react_agent.tools.registry import ToolRegistry

ENVIRONMENT_VERSION = "e2_doc_search_v2"
IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[_-][A-Za-z0-9]+)+")
MAX_MATCHES = 5


def _json_ids(path: Path, key: str) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {row[key].casefold(): row[key] for row in json.loads(path.read_text(encoding="utf-8"))}


def _row_matches(database: Path, identifier: str) -> list[dict[str, Any]]:
    """Tables whose primary-key or ``*_id`` text column holds the identifier."""
    if not database.is_file():
        return []
    found = []
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        tables = [r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        for table in tables:
            for _, column, kind, _, _, pk in connection.execute(f'PRAGMA table_info("{table}")'):
                if not (pk or column.endswith("_id")) or kind.upper() != "TEXT":
                    continue
                # Table and column names come from sqlite_master, not from the query.
                sql = f'SELECT "{column}" FROM "{table}" WHERE "{column}" = ? COLLATE NOCASE'  # noqa: S608
                if row := connection.execute(sql, (identifier,)).fetchone():
                    found.append({"id": row[0], "source": "database_row",
                                  "read_with": "db_query", "table": table, "column": column})
    return found


class DocSearchV2Tool(BaseTool[BaseModel]):
    input_model = BaseModel

    def __init__(self, wrapped: BaseTool[Any], environment: Path) -> None:
        if wrapped.name != "doc_search":
            raise ValueError("E2 wraps doc_search only")
        self._wrapped = wrapped
        self._environment = environment
        self.name, self.description = wrapped.name, wrapped.description
        self.input_model = wrapped.input_model

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._wrapped.input_schema

    def validate_arguments(self, arguments: dict[str, object]) -> BaseModel:
        return self._wrapped.validate_arguments(arguments)  # type: ignore[no-any-return]

    def identify(self, query: str) -> list[dict[str, Any]]:
        documents = _json_ids(self._environment / "documents/documents.json", "doc_id")
        pages = _json_ids(self._environment / "cached_pages/pages.json", "page_id")
        matches: list[dict[str, Any]] = []
        for token in dict.fromkeys(IDENTIFIER_RE.findall(query)):
            if (doc_id := documents.get(token.casefold())) is not None:
                matches.append({"id": doc_id, "source": "document", "read_with": "doc_read",
                                "arguments": {"doc_id": doc_id}})
            if (page_id := pages.get(token.casefold())) is not None:
                matches.append({"id": page_id, "source": "cached_page", "read_with": "cached_fetch",
                                "arguments": {"page_id": page_id}})
            matches += _row_matches(self._environment / "database/university.db", token)
        return matches[:MAX_MATCHES]

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        result = self._wrapped.execute(call_id, arguments)
        query = arguments.get("query")
        if result.ok and isinstance(result.content, dict) and isinstance(query, str):
            result = result.model_copy(
                update={"content": {**result.content, "id_matches": self.identify(query)}},
                deep=True)
        return result

    def _run(self, arguments: BaseModel) -> object:
        raise RuntimeError("doc_search_v2 delegates via execute")


def apply_e2(registry: ToolRegistry, environment: Path) -> ToolRegistry:
    """The same registry with ``doc_search`` wrapped; every other tool is unchanged."""
    wrapped = ToolRegistry()
    for name in registry.names:
        tool = registry.get(name)
        if tool is None:
            raise RuntimeError("registry changed during construction")
        wrapped.register(DocSearchV2Tool(tool, environment) if name == "doc_search" else tool)
    return wrapped
