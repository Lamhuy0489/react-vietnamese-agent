# Phase 1 Tool Contracts

Every tool is registered by name and reached only through `ToolBroker`.
Arguments use strict Pydantic models (`extra=forbid`), and every result uses the
same `ToolResult` envelope.

| Tool | Required input | Optional/default | Capability |
|---|---|---|---|
| `doc_search` | `query: str` | `top_k: int = 5` | Deterministic local search |
| `doc_read` | `doc_id: str` | — | Read by stable ID only |
| `db_query` | `query: str` | — | One read-only SELECT |
| `cached_search` | `query: str` | `top_k: int = 5` | Offline page search |
| `cached_fetch` | `page_id: str` | — | Offline read by stable ID |
| `calculator` | `expression: str` | — | Whitelisted arithmetic AST |
| `send_email_mock` | `to`, `subject`, `body` | — | Log-only simulated sink |
| `post_webhook_mock` | `endpoint`, `payload` | — | Log-only simulated sink |

The sink tools contain no SMTP/HTTP clients and execute all syntactically valid
content in A0. Content policy belongs to later A1–A6 gates, not the tool.

Error codes used in Phase 1 include `INVALID_ARGUMENTS`, `UNKNOWN_TOOL`,
`INVALID_QUERY`, `INVALID_EXPRESSION`, `NOT_FOUND`, `RESULT_LIMIT`,
`TOOL_TIMEOUT`, and `TOOL_RUNTIME_ERROR`.
