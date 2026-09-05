import json

import pytest

from react_agent.parser import ParseError, StructuredParser
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.tools.registry import ToolRegistry


def test_parser_accepts_exact_action(registry: ToolRegistry) -> None:
    raw = json.dumps({"action": {"name": "doc_search", "arguments": {"query": "học phí"}}})
    parsed = StructuredParser(registry).parse(raw)
    assert isinstance(parsed, ActionTurn)
    assert parsed.action.name == "doc_search"


def test_parser_accepts_exact_final(registry: ToolRegistry) -> None:
    parsed = StructuredParser(registry).parse('{"final_answer":{"answer":"Hoàn tất."}}')
    assert isinstance(parsed, FinalTurn)


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("not json", "INVALID_JSON"),
        ('{"tool":"doc_search"}', "INVALID_SCHEMA"),
        (
            '{"action":{"name":"doc_search","arguments":{}},"final_answer":{"answer":"x"}}',
            "INVALID_SCHEMA",
        ),
        (
            '{"thought":"hidden","action":{"name":"doc_search","arguments":{"query":"x"}}}',
            "INVALID_SCHEMA",
        ),
        ('{"action":{"name":"google_search","arguments":{}}}', "UNKNOWN_TOOL"),
        ('{"action":{"name":"doc_read","arguments":{"path":"x"}}}', "INVALID_ARGUMENTS"),
    ],
)
def test_parser_rejects_invalid_output(registry: ToolRegistry, raw: str, code: str) -> None:
    with pytest.raises(ParseError) as error:
        StructuredParser(registry).parse(raw)
    assert error.value.code == code
