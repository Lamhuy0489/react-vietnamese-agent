"""Read-only SQLite query tool for the synthetic database."""

from __future__ import annotations

import sqlite3

from pydantic import BaseModel, ConfigDict, Field

from react_agent.environment.database import DatabaseStore
from react_agent.tools.base import BaseTool, ToolExecutionError


class DbQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)


class DbQueryTool(BaseTool[DbQueryInput]):
    name = "db_query"
    description = "Chạy đúng một câu SELECT trên SQLite giả lập chỉ đọc."
    input_model = DbQueryInput

    def __init__(self, store: DatabaseStore) -> None:
        self._store = store

    def _run(self, arguments: DbQueryInput) -> object:
        query = arguments.query.strip()
        if not query.upper().startswith("SELECT") or ";" in query.rstrip(";"):
            raise ToolExecutionError(
                "INVALID_QUERY", "Only one SELECT statement is supported.", retryable=True
            )
        uri = f"file:{self._store.path}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True) as connection:
                cursor = connection.execute(query)
                columns = [description[0] for description in cursor.description or ()]
                rows = cursor.fetchmany(101)
        except sqlite3.Error as exc:
            raise ToolExecutionError("INVALID_QUERY", str(exc), retryable=True) from exc
        if len(rows) > 100:
            raise ToolExecutionError(
                "RESULT_LIMIT", "Query returned more than 100 rows.", retryable=True
            )
        return {"columns": columns, "rows": [list(row) for row in rows]}
