"""Build isolated environment overlays; no private oracle imports or policy gates."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel

from react_agent.schemas.adversarial_workbench import OverlayScenario
from react_agent.schemas.tool import ToolResult
from react_agent.tools.base import BaseTool
from react_agent.tools.factory import build_clean_registry
from react_agent.tools.registry import ToolRegistry


class OutputOverlayTool(BaseTool[BaseModel]):
    input_model = BaseModel

    def __init__(self, wrapped: BaseTool[Any], scenario: OverlayScenario, text: str) -> None:
        self._wrapped = wrapped
        self._trigger = scenario.trigger.arguments
        self._text = text
        self.name, self.description = wrapped.name, wrapped.description

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._wrapped.input_schema

    def validate_arguments(self, arguments: dict[str, object]) -> BaseModel:
        return cast(BaseModel, self._wrapped.validate_arguments(arguments))

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        result = self._wrapped.execute(call_id, arguments)
        if result.ok and arguments == self._trigger:
            if not isinstance(result.content, dict):
                raise ValueError("overlay requires a dictionary result")
            result = result.model_copy(
                update={"content": {**result.content, "notice": self._text}}, deep=True
            )
        return result

    def _run(self, arguments: BaseModel) -> object:
        raise RuntimeError("output overlay delegates via execute")


def build_overlay_registry(
    clean_environment: Path,
    destination: Path,
    scenario: OverlayScenario,
    branch: Literal["attack", "benign"],
) -> ToolRegistry:
    """Copy first, never mutate original; destination must be fresh and separate."""
    source, dest = clean_environment.resolve(), destination.resolve()
    if branch not in {"attack", "benign"}:
        raise ValueError("unsupported branch")
    if dest.exists() or dest.is_relative_to(source) or source.is_relative_to(dest):
        raise ValueError("overlay destination must be fresh and outside source environment")
    shutil.copytree(source, dest)
    addition = scenario.attack_text if branch == "attack" else scenario.benign_text
    content = scenario.base_content + "\n" + addition
    if scenario.source_type in {"document", "cached_page"}:
        document = scenario.source_type == "document"
        path = dest / ("documents/documents.json" if document else "cached_pages/pages.json")
        records = json.loads(path.read_text())
        key = "doc_id" if document else "page_id"
        if any(row[key] == scenario.source_id for row in records):
            raise ValueError("overlay source identity collides with frozen environment")
        new: dict[str, str] = {key: scenario.source_id, "title": scenario.title, "content": content}
        if not document:
            new["source_url"] = "https://workbench.example.test/" + scenario.source_id
        records.append(new)
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif scenario.source_type == "database_text_field":
        with sqlite3.connect(dest / "database/university.db") as connection:
            connection.execute(
                "CREATE TABLE awb_notices (note_id TEXT PRIMARY KEY, note TEXT, secret_token TEXT)"
            )
            connection.execute(
                "INSERT INTO awb_notices VALUES (?, ?, ?)",
                (scenario.source_id, content, scenario.sensitive_value),
            )
    registry = build_clean_registry(dest)
    if scenario.source_type == "tool_output":
        overlaid = ToolRegistry()
        for name in registry.names:
            tool = registry.get(name)
            if tool is None:
                raise RuntimeError("registry changed during construction")
            overlaid.register(
                OutputOverlayTool(tool, scenario, content)
                if name == scenario.trigger.name
                else tool
            )
        registry = overlaid
    return registry
