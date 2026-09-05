"""Read one synthetic document by stable ID."""

from pydantic import BaseModel, ConfigDict, Field

from react_agent.environment.documents import DocumentStore
from react_agent.tools.base import BaseTool, ToolExecutionError


class DocReadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)


class DocReadTool(BaseTool[DocReadInput]):
    name = "doc_read"
    description = "Đọc tài liệu nội bộ bằng doc_id; không nhận đường dẫn file."
    input_model = DocReadInput

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def _run(self, arguments: DocReadInput) -> object:
        document = self._store.get(arguments.doc_id)
        if document is None:
            raise ToolExecutionError(
                "NOT_FOUND", f"Document not found: {arguments.doc_id}", retryable=True
            )
        return document.model_dump()
