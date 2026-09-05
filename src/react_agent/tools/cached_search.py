"""Search static cached pages without Internet access."""

from pydantic import BaseModel, ConfigDict, Field

from react_agent.environment.cache import CacheStore
from react_agent.tools.base import BaseTool


class CachedSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class CachedSearchTool(BaseTool[CachedSearchInput]):
    name = "cached_search"
    description = "Tìm trong các trang thông tin đã lưu cục bộ."
    input_model = CachedSearchInput

    def __init__(self, store: CacheStore) -> None:
        self._store = store

    def _run(self, arguments: CachedSearchInput) -> object:
        return {"results": self._store.search(arguments.query, arguments.top_k)}
