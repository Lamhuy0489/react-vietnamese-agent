# Tool Contracts

The approved tool set is fixed:

1. `doc_search`
2. `doc_read`
3. `db_query`
4. `cached_search`
5. `cached_fetch`
6. `calculator`
7. `send_email_mock`
8. `post_webhook_mock`

All calls use a typed ToolCall/ToolResult contract and pass through the Tool
Broker. Tools are deterministic for a frozen environment. The two external
sinks only append an event to the run trace; they never send network traffic.

Exact argument/result schemas are frozen in Phase 1 before parallel coding.
