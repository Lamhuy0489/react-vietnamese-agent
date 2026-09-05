"""Fetch one static cached page by stable ID."""

from pydantic import BaseModel, ConfigDict, Field

from react_agent.environment.cache import CacheStore
from react_agent.tools.base import BaseTool, ToolExecutionError


class CachedFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_id: str = Field(min_length=1)


class CachedFetchTool(BaseTool[CachedFetchInput]):
    name = "cached_fetch"
    description = "Đọc trang đã cache bằng page_id; không thực hiện HTTP."
    input_model = CachedFetchInput

    def __init__(self, store: CacheStore) -> None:
        self._store = store

    def _run(self, arguments: CachedFetchInput) -> object:
        page = self._store.get(arguments.page_id)
        if page is None:
            raise ToolExecutionError(
                "NOT_FOUND", f"Cached page not found: {arguments.page_id}", retryable=True
            )
        return page.model_dump()
