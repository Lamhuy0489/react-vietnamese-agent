from pathlib import Path

import pytest

from react_agent.schemas.clean_task import FaultSpec
from react_agent.schemas.tool import ToolResult
from react_agent.tools.factory import build_clean_registry
from react_agent.tools.registry import ToolRegistry


def execute(registry: ToolRegistry, name: str, arguments: dict[str, object]) -> ToolResult:
    tool = registry.get(name)
    assert tool is not None
    return tool.execute("call_000001", arguments)


def test_registry_contains_exact_tool_set(registry: ToolRegistry) -> None:
    assert set(registry.names) == {
        "doc_search",
        "doc_read",
        "db_query",
        "cached_search",
        "cached_fetch",
        "calculator",
        "send_email_mock",
        "post_webhook_mock",
    }


def test_document_search_is_deterministic(registry: ToolRegistry) -> None:
    arguments = {"query": "đăng ký học phần", "top_k": 3}
    first = execute(registry, "doc_search", arguments)
    second = execute(registry, "doc_search", arguments)
    assert first.ok and second.ok
    assert first.content == second.content


def test_document_read_uses_id_and_returns_not_found(registry: ToolRegistry) -> None:
    valid = execute(registry, "doc_read", {"doc_id": "DOC_001"})
    missing = execute(registry, "doc_read", {"doc_id": "DOC_999"})
    invalid = execute(registry, "doc_read", {"path": "../../secret.txt"})
    assert valid.ok
    assert not missing.ok and missing.error is not None
    assert missing.error.code == "NOT_FOUND"
    assert not invalid.ok and invalid.error is not None
    assert invalid.error.code == "INVALID_ARGUMENTS"


def test_database_is_select_only(registry: ToolRegistry) -> None:
    valid = execute(
        registry,
        "db_query",
        {"query": "SELECT room FROM course_sections WHERE course_code='CS101'"},
    )
    write = execute(registry, "db_query", {"query": "DELETE FROM course_sections"})
    assert valid.ok
    assert valid.content == {"columns": ["room"], "rows": [["A301"]]}
    assert not write.ok and write.error is not None
    assert write.error.code == "INVALID_QUERY"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 2 * 3", 7),
        ("(3200000 * 15) / 100", 480000.0),
        ("2 ** 10", 1024),
        ("7 % 4", 3),
    ],
)
def test_calculator_valid_expressions(
    registry: ToolRegistry, expression: str, expected: int | float
) -> None:
    result = execute(registry, "calculator", {"expression": expression})
    assert result.ok
    assert result.content == {"value": expected}


@pytest.mark.parametrize(
    "expression",
    ["__import__('os').system('id')", "open('/tmp/x')", "1 / 0", "2 ** 999"],
)
def test_calculator_rejects_unsafe_or_invalid_expressions(
    registry: ToolRegistry, expression: str
) -> None:
    result = execute(registry, "calculator", {"expression": expression})
    assert not result.ok
    assert result.error is not None
    assert result.error.code == "INVALID_EXPRESSION"


def test_cached_tools_never_fetch_real_url(registry: ToolRegistry) -> None:
    search = execute(registry, "cached_search", {"query": "Quốc khánh"})
    fetch = execute(registry, "cached_fetch", {"page_id": "CACHE_001"})
    assert search.ok and fetch.ok
    assert "02/09/2026" in str(fetch.content)


def test_mock_sinks_work_when_socket_creation_is_forbidden(
    registry: ToolRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("network access attempted")

    monkeypatch.setattr("socket.socket", fail_socket)
    email = execute(
        registry,
        "send_email_mock",
        {"to": "sv@example.edu", "subject": "Test", "body": "Synthetic"},
    )
    webhook = execute(
        registry,
        "post_webhook_mock",
        {"endpoint": "https://collector.example/mock", "payload": {"x": 1}},
    )
    assert email.ok and webhook.ok
    assert email.content["status"] == "simulated"
    assert webhook.content["status"] == "simulated"


def test_database_fixture_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "data" / "smoke" / "database" / "university.db").is_file()


def test_clean_registry_injects_fault_once_then_delegates() -> None:
    root = Path(__file__).resolve().parents[2]
    registry = build_clean_registry(
        root / "data" / "clean" / "v1" / "environment",
        fault_plan=[
            FaultSpec(
                tool="calculator",
                occurrence=1,
                error_code="TIMEOUT_SIMULATED",
                retryable=True,
            )
        ],
    )
    tool = registry.get("calculator")
    assert tool is not None
    first = tool.execute("call_000001", {"expression": "2 + 3"})
    second = tool.execute("call_000002", {"expression": "2 + 3"})
    assert not first.ok and first.error is not None
    assert first.error.code == "TIMEOUT_SIMULATED"
    assert first.metadata["injected"] is True
    assert second.ok and second.content == {"value": 5}
