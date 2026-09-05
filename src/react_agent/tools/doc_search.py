"""Deterministic internal-document search."""

from pydantic import BaseModel, ConfigDict, Field

from react_agent.environment.documents import DocumentStore
from react_agent.tools.base import BaseTool


class DocSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class DocSearchTool(BaseTool[DocSearchInput]):
    name = "doc_search"
    description = "Tìm tài liệu nội bộ trong kho giả lập."
    input_model = DocSearchInput

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def _run(self, arguments: DocSearchInput) -> object:
        return {"results": self._store.search(arguments.query, arguments.top_k)}
