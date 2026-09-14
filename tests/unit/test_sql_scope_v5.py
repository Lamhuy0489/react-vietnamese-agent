"""SQL parser and row grants are pure; no DB connection, oracle or model needed."""

import pytest

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import Effect
from react_agent.security_v1.processing_scope import ScopeError
from react_agent.security_v1.processing_scope_v4 import ProcessingScope as V4
from react_agent.security_v1.processing_scope_v5 import ProcessingScope, describe_action
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.sql_rows_v1 import RowBinding, RowBindings, parse_rows

ROWS = RowBindings(
    rows=(
        RowBinding(table="notices", key="note_id", value="AWB_A"),
        RowBinding(table="notices", key="note_id", value="AWB_B"),
    )
)
RESOURCES = ResourceBindings()
RAW = "Đọc note của AWB_A trong notices. Đọc secret_token của AWB_B trong notices."


def query(sql="SELECT note FROM notices WHERE note_id = 'AWB_A'"):
    return Action(name="db_query", arguments={"query": sql})


def scope(raw=RAW):
    return ProcessingScope(raw, resources=RESOURCES, rows=ROWS)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT note FROM notices WHERE note_id = 'AWB_A'",
        "select NOTE from NOTICES where NOTE_ID in ('AWB_A')",
        "SELECT secret_token, note FROM notices WHERE note_id IN ('AWB_B', 'AWB_A')",
    ],
)
def test_pure_grammar_tracks_projection_predicate_rows(sql):
    result = parse_rows(sql)
    assert result is not None
    assert result.table == "notices" and result.key == "note_id"
    assert "note_id" in result.accessed_columns and "note_id" not in result.columns
    assert result.values == tuple(sorted(result.values))
    assert describe_action(query(sql), resources=RESOURCES).resource_ids == result.values


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM notices WHERE note_id = 'AWB_A'",
        "SELECT note AS x FROM notices WHERE note_id = 'AWB_A'",
        "SELECT lower(note) FROM notices WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices WHERE note_id = 'AWB_A' OR 1=1",
        "SELECT note FROM notices WHERE note_id IN (SELECT note_id FROM notices)",
        "SELECT note FROM notices WHERE note_id IN ('AWB_A','awb_b')",
        "SELECT note FROM notices WHERE note_id = 'awb_a'",
        "SELECT note FROM notices WHERE note_id = 'AWB_A';",
        "SELECT note FROM notices WHERE note_id = 'AWB_A' -- comment",
        "SELECT note FROM notices WHERE note_id = 'AWB_A' COLLATE NOCASE",
        "SELECT note FROM notices WHERE note_id = ?",
        "SELECT note FROM notices WHERE note_id IN ('AWB_A','AWB_A')",
        "SELECT note,NOTE FROM notices WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices WHERE note_id = 'AWB_A\u200b'",
        'SELECT note FROM notices WHERE note_id = "AWB_A"',
        "SELECT note FROM notices WHERE note_id = 'AWB_A'' OR ''x'",
        "SELECT note FROM notices WHERE note_id = 'AWB_A' LIMIT 1",
        "SELECT note FROM main.notices WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices JOIN other WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices WHERE note_id IN ()",
        "SELECT note FROM notices WHERE note_id IN ('AWB_A', 'AUX_BAD/../x')",
        None,
        1,
        "x" * 2001,
    ],
)
def test_unsupported_sql_never_becomes_assessed(sql):
    assert parse_rows(sql) is None
    if isinstance(sql, str):
        assert scope().pre(query(sql)).effect == Effect.DENY


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT note FROM notices",
        "SELECT secret_token FROM notices WHERE note_id = 'AWB_A'",
        "SELECT note_id FROM notices WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices WHERE note_id IN ('AWB_A','AWB_B')",
        "SELECT note FROM notices WHERE note_id = 'AWB_UNKNOWN'",
        "SELECT note FROM other WHERE note_id = 'AWB_A'",
        "SELECT note FROM notices WHERE secret_token = 'AWB_A'",
    ],
)
def test_row_column_cartesian_expansion_denied(sql):
    assert scope().pre(query(sql)).effect == Effect.DENY


@pytest.mark.parametrize(
    "raw",
    [
        "Không đọc trường note AWB_A",
        "Nếu cần đọc trường note AWB_A",
        'Đọc "note của AWB_A"',
        "> Đọc note của AWB_A",
        "Tra số ghế ở AWB_A",
        "Đọc note của AWB_A trong other",
        "Đọc trường note AWB_A và trường secret_token AWB_B",
        "Đọc trường note AWB_A và trường secret_token AWB_UNKNOWN",
        "Đọc trường note AWB_A và trường secret_token awb_unknown",
        "Đọc trường note AWB_A và trường secret_token DOC_001",
        "Đọc note của AWB_A\u200b",
        "Đọc note của xAWB_A",
    ],
)
def test_ambiguous_negative_or_incomplete_raw_user_does_not_grant(raw):
    assert not scope(raw).row_grants
    assert scope(raw).pre(query()).effect == Effect.DENY


def test_valid_pairs_union_same_row_and_no_cross_task_state():
    raw = "Đọc note và secret_token của AWB_A. Tra trường note dòng AWB_B."
    s = scope(raw)
    assert s.pre(query()).effect == Effect.ALLOW
    assert (
        s.pre(query("SELECT note FROM notices WHERE note_id IN ('AWB_A','AWB_B')")).effect
        == Effect.ALLOW
    )
    s.observe(
        query(),
        artifact_id="ART_row",
        source_type=SourceType.DATABASE,
        source_id="AWB_A",
        trust=Trust.UNTRUSTED,
    )
    assert s.row_observations[0].values == ("AWB_A",)
    assert scope(raw).row_observations == []
    assert (
        s.pre(query("SELECT secret_token FROM notices WHERE note_id = 'AWB_B'")).effect
        == Effect.DENY
    )
    assert s.pre(query("SELECT note FROM notices")).effect == Effect.DENY


def test_observe_denial_wrong_source_and_extra_arguments_do_not_mutate():
    s = scope()
    extra = query().model_copy(update={"arguments": {**query().arguments, "extra": True}})
    for proposal, kind in [
        (extra, SourceType.DATABASE),
        (query(), SourceType.DOCUMENT),
        (query("SELECT note FROM notices"), SourceType.DATABASE),
    ]:
        before = s.snapshot()
        with pytest.raises(ScopeError):
            s.observe(
                proposal,
                artifact_id="ART_row",
                source_type=kind,
                source_id="AWB_A",
                trust=Trust.UNTRUSTED,
            )
        assert s.snapshot() == before


def binding(
    sql="SELECT note FROM notices WHERE note_id = 'AWB_A'",
    identity="AWB_A",
    kind=SourceType.DATABASE,
):
    return SourceBinding(
        tool="db_query",
        arguments_json=canonical_json({"query": sql}),
        label=SourceLabel(
            source_id=identity,
            source_type=kind,
            sensitivity=Sensitivity.PUBLIC,
            trust=Trust.UNTRUSTED,
        ),
    )


def test_host_inventory_is_not_authorization_and_conflicts_fail():
    row = RowBindings.from_catalog(SourceCatalog(bindings=(binding(),)))
    assert row.rows == ROWS.rows[:1]
    assert (
        ProcessingScope("Không đọc AWB_A", resources=RESOURCES, rows=row).pre(query()).effect
        == Effect.DENY
    )
    for item in [
        binding(identity="AWB_B"),
        binding(kind=SourceType.DOCUMENT),
        binding(sql="SELECT note FROM notices"),
        binding(sql="SELECT note FROM notices WHERE note_id IN ('AWB_A','AWB_B')"),
    ]:
        with pytest.raises(ValueError):
            RowBindings.from_catalog(SourceCatalog(bindings=(item,)))
    with pytest.raises(ValueError):
        RowBindings.from_catalog(
            SourceCatalog(
                bindings=(binding(), binding(sql="SELECT note FROM other WHERE note_id = 'AWB_A'"))
            )
        )


def test_legacy_no_row_environment_and_document_namespace_stay_unchanged():
    raw = "Truy vấn bảng students cột name. Truy vấn bảng grades cột score."
    old = V4(raw, resources=RESOURCES)
    new = ProcessingScope(raw, resources=RESOURCES, rows=RowBindings())
    for sql in ["SELECT name FROM students", "SELECT score FROM students"]:
        assert new.pre(query(sql)).effect == old.pre(query(sql)).effect
    assert new.database_grants == old.database_grants


def test_prefixed_host_table_is_not_a_second_row_and_inventory_still_not_a_grant():
    rows = RowBindings(rows=(RowBinding(table="awb_notices", key="note_id", value="AWB_A"),))
    for raw in [
        "Tra trường note của dòng note_id AWB_A trong bảng awb_notices.",
        "Đọc note và secret_token của AWB_A trong awb_notices.",
    ]:
        s = ProcessingScope(raw, resources=RESOURCES, rows=rows)
        assert (
            s.pre(query("SELECT note FROM awb_notices WHERE note_id = 'AWB_A'")).effect
            == Effect.ALLOW
        )
    s = ProcessingScope(
        "Đọc trường note AWB_A và trường secret_token awb_notices", resources=RESOURCES, rows=rows
    )
    assert not s.row_grants


def test_row_column_and_inventory_budgets():
    assert (
        parse_rows(
            "SELECT note FROM notices WHERE note_id IN ("  # noqa: S608 - parser-only budget fixture
            + ",".join("'AWB_A" + str(n) + "'" for n in range(33))
            + ")"
        )
        is None
    )
    assert (
        parse_rows(
            "SELECT "  # noqa: S608 - parser-only budget fixture
            + ",".join("c" + str(n) for n in range(33))
            + " FROM notices WHERE note_id = 'AWB_A'"
        )
        is None
    )
    with pytest.raises(ValueError):
        RowBindings(
            rows=tuple(
                RowBinding(table="notices", key="note_id", value=f"AWB_A{n:03}") for n in range(257)
            )
        )
    with pytest.raises(ValueError):
        RowBinding(table="awb_a", key="note_id", value="AWB_A")


def test_selected_dev_static_coverage_and_matched_grants():
    from pathlib import Path

    from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog, selected_fixtures

    root = Path(__file__).resolve().parents[2]
    rows = selected_fixtures(root / "data/adversarial/release_v2")
    decisions = []
    for attack, benign in zip(rows[::2], rows[1::2], strict=True):
        snapshots = []
        for row in (attack, benign):
            catalog = fixture_catalog(row)
            s = ProcessingScope(
                row.task.instruction,
                resources=ResourceBindings.from_catalog(catalog),
                rows=RowBindings.from_catalog(catalog),
            )
            snapshots.append(sorted(s.row_grants))
            assert describe_action(row.overlay.trigger, resources=s.resources).assessed
            decisions.append(s.pre(row.overlay.trigger).effect)
        assert snapshots[0] == snapshots[1]
    assert decisions.count(Effect.ALLOW) == 14
    assert decisions.count(Effect.DENY) == 2
