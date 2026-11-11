import json
import sqlite3
from pathlib import Path

from react_agent.environment import DocumentStore
from react_agent.tools.calculator import CalculatorTool
from react_agent.tools.doc_search import DocSearchTool
from react_agent.tools.doc_search_v2 import DocSearchV2Tool, apply_e2
from react_agent.tools.registry import ToolRegistry


def _environment(root: Path) -> Path:
    (root / "documents").mkdir(parents=True)
    (root / "cached_pages").mkdir()
    (root / "database").mkdir()
    (root / "documents/documents.json").write_text(json.dumps(
        [{"doc_id": "AWB_DOCX", "title": "Lịch thi", "content": "Thi ngày 5/12."}]))
    (root / "cached_pages/pages.json").write_text(json.dumps(
        [{"page_id": "AWB_PAGEX", "title": "Sân", "content": "Sân trống 19h.",
          "source_url": "https://workbench.example.test/AWB_PAGEX"}]))
    with sqlite3.connect(root / "database/university.db") as connection:
        connection.execute(
            "CREATE TABLE awb_notices (note_id TEXT PRIMARY KEY, note TEXT, secret_token TEXT)")
        connection.execute("INSERT INTO awb_notices VALUES ('AWB_NOTEX', 'Giờ xe 6h', 'S3CRET')")
    return root


def _tool(root: Path) -> DocSearchV2Tool:
    store = DocumentStore.from_json(root / "documents/documents.json")
    return DocSearchV2Tool(DocSearchTool(store), root)


def test_identity_matches_point_to_the_reading_tool(tmp_path: Path) -> None:
    tool = _tool(_environment(tmp_path))
    result = tool.execute("c1", {"query": "đọc awb_docx, AWB_PAGEX và AWB_NOTEX"})
    assert result.ok
    assert result.content["results"] == []  # lexical part is the pinned tool's
    assert result.content["id_matches"] == [
        {"id": "AWB_DOCX", "source": "document", "read_with": "doc_read",
         "arguments": {"doc_id": "AWB_DOCX"}},
        {"id": "AWB_PAGEX", "source": "cached_page", "read_with": "cached_fetch",
         "arguments": {"page_id": "AWB_PAGEX"}},
        {"id": "AWB_NOTEX", "source": "database_row", "read_with": "db_query",
         "table": "awb_notices", "column": "note_id"},
    ]


def test_no_content_leaks_through_identity_matches(tmp_path: Path) -> None:
    result = _tool(_environment(tmp_path)).execute("c1", {"query": "AWB_NOTEX AWB_PAGEX"})
    text = json.dumps(result.content["id_matches"], ensure_ascii=False)
    assert "S3CRET" not in text and "Giờ xe" not in text and "19h" not in text


def test_unknown_identifiers_and_plain_words_add_nothing(tmp_path: Path) -> None:
    query = "lịch thi AWB_NONE secret_token"
    result = _tool(_environment(tmp_path)).execute("c1", {"query": query})
    assert result.content["id_matches"] == []
    assert [r["doc_id"] for r in result.content["results"]] == ["AWB_DOCX"]


def test_interface_is_the_pinned_tool(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    pinned = DocSearchTool(DocumentStore.from_json(root / "documents/documents.json"))
    tool = DocSearchV2Tool(pinned, root)
    assert (tool.name, tool.description, tool.input_schema) == (
        pinned.name, pinned.description, pinned.input_schema)


def test_invalid_arguments_pass_through_unchanged(tmp_path: Path) -> None:
    result = _tool(_environment(tmp_path)).execute("c1", {"query": ""})
    assert not result.ok and result.error is not None
    assert result.error.code == "INVALID_ARGUMENTS"


def test_apply_e2_wraps_only_doc_search(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    registry = ToolRegistry()
    calculator = CalculatorTool()
    registry.register(DocSearchTool(DocumentStore.from_json(root / "documents/documents.json")))
    registry.register(calculator)
    wrapped = apply_e2(registry, root)
    assert wrapped.names == registry.names
    assert wrapped.get("calculator") is calculator
    assert isinstance(wrapped.get("doc_search"), DocSearchV2Tool)
    assert wrapped.definitions() == registry.definitions()
