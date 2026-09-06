"""Public-only auxiliary source overlays; no evaluator or policy imports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.authoring.overlays import build_overlay_registry
from react_agent.schemas.adversarial_workbench import OverlayScenario, StrictRecord
from react_agent.tools.factory import build_clean_registry
from react_agent.tools.registry import ToolRegistry


class LinkedText(StrictRecord):
    identity: str = Field(pattern=r"^AUX_[A-Z]+$")
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class LinkedRow(StrictRecord):
    note_id: str = Field(pattern=r"^AUX_[A-Z]+$")
    note: str = Field(min_length=1)
    secret_token: str | None = None


class LinkedResources(StrictRecord):
    task_id: str = Field(pattern=r"^awb_[a-z]+$")
    documents: list[LinkedText] = Field(default_factory=list)
    cached_pages: list[LinkedText] = Field(default_factory=list)
    rows: list[LinkedRow] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_identities(self) -> Self:
        ids = [r.identity for r in [*self.documents, *self.cached_pages]]
        ids.extend(r.note_id for r in self.rows)
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("nonempty unique auxiliary identities required")
        return self


def build_linked_registry(
    clean: Path,
    destination: Path,
    scenario: OverlayScenario,
    resources: LinkedResources,
    branch: Literal["attack", "benign"],
) -> ToolRegistry:
    if resources.task_id != scenario.task_id:
        raise ValueError("resource/task identity mismatch")
    if scenario.source_type == "tool_output":
        raise ValueError("linked extension does not support calculator overlays")
    build_overlay_registry(clean, destination, scenario, branch)
    for additions, relative, key in (
        (resources.documents, "documents/documents.json", "doc_id"),
        (resources.cached_pages, "cached_pages/pages.json", "page_id"),
    ):
        path = destination / relative
        records = json.loads(path.read_text())
        existing = {r[key] for r in records}
        for item in additions:
            if item.identity in existing:
                raise ValueError("auxiliary identity collides with environment")
            row = {key: item.identity, "title": item.title, "content": item.content}
            if key == "page_id":
                row["source_url"] = "https://linked.example.test/" + item.identity
            records.append(row)
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    if resources.rows:
        with sqlite3.connect(destination / "database/university.db") as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS awb_notices "
                "(note_id TEXT PRIMARY KEY, note TEXT, secret_token TEXT)"
            )
            connection.executemany(
                "INSERT INTO awb_notices VALUES (?, ?, ?)",
                [(r.note_id, r.note, r.secret_token) for r in resources.rows],
            )
    return build_clean_registry(destination)
