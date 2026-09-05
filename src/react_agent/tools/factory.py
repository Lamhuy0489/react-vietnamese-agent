"""Build the fixed eight-tool registry from a smoke environment."""

from __future__ import annotations

from pathlib import Path

from react_agent.environment import CacheStore, DatabaseStore, DocumentStore
from react_agent.schemas.clean_task import FaultSpec
from react_agent.tools.cached_fetch import CachedFetchTool
from react_agent.tools.cached_search import CachedSearchTool
from react_agent.tools.calculator import CalculatorTool
from react_agent.tools.db_query import DbQueryTool
from react_agent.tools.doc_read import DocReadTool
from react_agent.tools.doc_search import DocSearchTool
from react_agent.tools.fault_injection import FaultInjectingTool
from react_agent.tools.post_webhook_mock import PostWebhookMockTool
from react_agent.tools.registry import ToolRegistry
from react_agent.tools.send_email_mock import SendEmailMockTool


def _build_registry(data_root: Path, fault_plan: list[FaultSpec]) -> ToolRegistry:
    documents = DocumentStore.from_json(data_root / "documents" / "documents.json")
    pages = CacheStore.from_json(data_root / "cached_pages" / "pages.json")
    database = DatabaseStore(data_root / "database" / "university.db")
    tools = (
        DocSearchTool(documents),
        DocReadTool(documents),
        DbQueryTool(database),
        CachedSearchTool(pages),
        CachedFetchTool(pages),
        CalculatorTool(),
        SendEmailMockTool(),
        PostWebhookMockTool(),
    )
    faults_by_tool: dict[str, list[FaultSpec]] = {}
    for fault in fault_plan:
        faults_by_tool.setdefault(fault.tool, []).append(fault)
    registry = ToolRegistry()
    for tool in tools:
        faults = faults_by_tool.get(tool.name, [])
        if faults:
            registry.register(FaultInjectingTool(tool, faults))
            continue
        registry.register(tool)
    return registry


def build_smoke_registry(data_root: Path) -> ToolRegistry:
    return _build_registry(data_root, [])


def build_clean_registry(
    data_root: Path, *, fault_plan: list[FaultSpec] | None = None
) -> ToolRegistry:
    """Build the eight tools with optional deterministic Phase 2 faults."""

    return _build_registry(data_root, fault_plan or [])
