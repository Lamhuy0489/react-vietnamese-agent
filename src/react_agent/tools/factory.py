"""Build the fixed eight-tool registry from a smoke environment."""

from __future__ import annotations

from pathlib import Path

from react_agent.environment import CacheStore, DatabaseStore, DocumentStore
from react_agent.tools.cached_fetch import CachedFetchTool
from react_agent.tools.cached_search import CachedSearchTool
from react_agent.tools.calculator import CalculatorTool
from react_agent.tools.db_query import DbQueryTool
from react_agent.tools.doc_read import DocReadTool
from react_agent.tools.doc_search import DocSearchTool
from react_agent.tools.post_webhook_mock import PostWebhookMockTool
from react_agent.tools.registry import ToolRegistry
from react_agent.tools.send_email_mock import SendEmailMockTool


def build_smoke_registry(data_root: Path) -> ToolRegistry:
    documents = DocumentStore.from_json(data_root / "documents" / "documents.json")
    pages = CacheStore.from_json(data_root / "cached_pages" / "pages.json")
    database = DatabaseStore(data_root / "database" / "university.db")
    registry = ToolRegistry()
    for tool in (
        DocSearchTool(documents),
        DocReadTool(documents),
        DbQueryTool(database),
        CachedSearchTool(pages),
        CachedFetchTool(pages),
        CalculatorTool(),
        SendEmailMockTool(),
        PostWebhookMockTool(),
    ):
        registry.register(tool)
    return registry
