"""Actual CPU-spawn three-way joins and adversarial evidence mutations; no Test."""

import json
import shutil

import pytest
from test_guard_diagnostic_pair_v1 import CATALOG, RESPONSES, ROOT, SAFE, TASK
from test_guard_diagnostic_pair_v1 import invoke as baseline_invoke
from test_phase5_pair_runtime import Factory

from react_agent.agent.state import RuntimeConfig
from react_agent.llm.base import GenerationConfig
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.model_pair_v1 import ModelIdentity
from react_agent.llm.model_pair_v2 import ShutdownPairConfig
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.document_pair_runtime_v1 import run_pair_task
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.guard_diagnostic_audit_v2 import Sidecar, _records, audit


def invoke(root, response=SAFE, level="A6", break_witness=False):
    root.mkdir()
    execution, sidecar, witness = root / "task", root / "worker.jsonl", root / "host.jsonl"
    pair = DiagnosticPair(
        Factory("agent", RESPONSES),
        DiagnosticFactory(
            Factory("guard", (response,) * 4 if response is not None else ()), sidecar
        ),
        ShutdownPairConfig(
            ModelIdentity("agent", "synthetic_v1"),
            ModelIdentity("guard", "synthetic_v1"),
            agent_start_seconds=10,
            guard_start_seconds=10,
            agent_call_seconds=5,
            guard_call_seconds=5,
        ),
        witness,
    )
    if break_witness:
        witness.write_text("preserve")
    run = run_pair_task(
        TASK,
        output=execution,
        registry_factory=lambda: build_clean_registry(ROOT / "data/clean/v1_1/environment"),
        security=configuration(level),
        runtime_config=RuntimeConfig(max_steps=3, max_format_retries_per_step=0),
        generation=GenerationConfig(),
        source_catalog=CATALOG,
        pair=pair,
    )
    return (execution, sidecar, witness), run


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    return invoke(tmp_path_factory.mktemp("v2") / "case")[0]


@pytest.fixture
def case(source, tmp_path):
    root = tmp_path / "copy"
    shutil.copytree(source[0].parent, root)
    return root / "task", root / "worker.jsonl", root / "host.jsonl"


def test_join_readonly_repeatable_and_independent(case):
    first = audit(*case)
    assert first == audit(*case)
    assert first["response_records"] == 2 and first["response_hash_cross_checked"]
    assert [r["stage"] for r in first["joined"]] == ["PRE", "POST"]
    assert not first["native_model_authenticated"] and not first["syntax_hints_rederived"]
    host = json.loads(case[2].read_text().splitlines()[0])
    worker = json.loads(case[1].read_text().splitlines()[0])
    assert host["host_pid"] != worker["worker_pid"]


@pytest.mark.parametrize(
    "response,category",
    [
        (SAFE, "valid"),
        ('{"risk":"SAFE",}', "json_syntax"),
        ("{}", "schema"),
        ("```json\n{}\n```", "json_syntax"),
    ],
)
def test_parity_and_retirement(tmp_path, response, category):
    paths, observed = invoke(tmp_path / "observed", response)
    baseline, _ = baseline_invoke(tmp_path / "baseline", "A6", response, False)
    assert observed.result.status == baseline.result.status
    assert observed.result.final_answer == baseline.result.final_answer
    assert observed.result.tool_sequence == baseline.result.tool_sequence
    report = audit(*paths)
    assert report["response_records"] == (2 if category == "valid" else 1)
    assert report["joined"][0]["diagnostic"]["baseline"]["category"] == category
    if category != "valid":
        traces = [
            json.loads(line)
            for line in (paths[0] / "runtime/trace_guard.jsonl").read_text().splitlines()
        ]
        assert [t["outcome"]["error_code"] for t in traces] == ["INVALID_OUTPUT", "BACKEND_FAILURE"]
        assert [len(t["execution_attempts"]) for t in traces] == [1, 0]


@pytest.mark.parametrize("file_index", [1, 2])
@pytest.mark.parametrize(
    "mutation",
    [
        "pid",
        "request",
        "generation",
        "sequence",
        "missing",
        "extra",
        "hash",
        "chars",
        "identity",
        "raw",
        "boolean",
        "duplicate",
    ],
)
def test_mutations_rejected(case, file_index, mutation):
    path = case[file_index]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    row = rows[0]
    if mutation == "pid":
        row["worker_pid"] += 1
    elif mutation in {"request", "generation"}:
        row[mutation + "_sha256"] = "0" * 64
    elif mutation == "sequence":
        row["sequence"] += 1
    elif mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        rows.append(rows[0])
    elif mutation in {"hash", "chars"}:
        target = row["diagnostic"]["baseline"] if file_index == 1 else row
        target["response_sha256" if mutation == "hash" else "response_chars"] = (
            "0" * 64 if mutation == "hash" else 1
        )
    elif mutation == "identity":
        row["response_identity_matches"] = False
    elif mutation == "raw":
        row["raw_text"] = "SYNTHETIC_SECRET"
    elif mutation == "boolean":
        row["response_identity_matches"] = "true"
    payload = "\n".join(json.dumps(r) for r in rows) + "\n"
    if mutation == "duplicate":
        payload = payload.replace('"sequence": 1', '"sequence": 1, "sequence": 1', 1)
    path.write_text(payload)
    with pytest.raises(ValueError) as exc:
        audit(*case)
    assert "SYNTHETIC_SECRET" not in str(exc.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("syntax_kind", "expected_value"),
        ("error_offset", 0),
        ("terminal_fence", True),
        ("framing", "empty"),
        ("error_at_end", True),
        ("trailing_comma_at_error", False),
    ],
)
def test_non_syntax_shape_rejected(case, field, value):
    rows = [json.loads(line) for line in case[1].read_text().splitlines()]
    rows[0]["diagnostic"][field] = value
    case[1].write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    with pytest.raises(ValueError):
        audit(*case)


@pytest.mark.parametrize(
    "mutation", ["offset", "end", "comma", "checked", "size", "issues", "strict"]
)
def test_syntax_shape_rejected(mutation):
    from react_agent.security_v1.guard_diagnostics_v2 import diagnose

    d = diagnose('{"risk":').model_dump(mode="json")
    if mutation == "offset":
        d["error_offset"] = 1000
    elif mutation == "end":
        d["error_at_end"] = False
    elif mutation == "comma":
        d["trailing_comma_at_error"] = True
    elif mutation == "checked":
        d["baseline"]["parser_checked"] = False
    elif mutation == "size":
        d["baseline"]["category"] = "size"
    elif mutation == "issues":
        d["baseline"]["issues"] = [{"field": "root", "kind": "missing"}]
    else:
        d["error_offset"] = True
    row = dict(
        protocol="guard_response_sidecar_v2",
        sequence=1,
        worker_pid=1,
        request_sha256="0" * 64,
        generation_sha256="0" * 64,
        response_identity_matches=True,
        diagnostic=d,
    )
    with pytest.raises(ValueError, match="invalid diagnostic record"):
        _records(json.dumps(row).encode(), Sidecar)


def test_missing_witness_and_wrong_host_rejected(case):
    rows = [json.loads(line) for line in case[2].read_text().splitlines()]
    rows[0]["host_pid"] += 1
    case[2].write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    with pytest.raises(ValueError, match="witness mismatch"):
        audit(*case)
    case[2].unlink()
    with pytest.raises(ValueError, match="one worker and host"):
        audit(*case)


@pytest.mark.parametrize("level", ["A2", "A3", "A4", "A5"])
def test_all_guard_levels_join(tmp_path, level):
    paths, result = invoke(tmp_path / "observed", level=level)
    assert result.result.status == "completed"
    assert audit(*paths)["response_records"] == 2


def test_transport_failure_has_no_response_receipts(tmp_path):
    paths, result = invoke(tmp_path / "observed", response=None)
    assert result.result.status == "model_error"
    assert not paths[1].exists() and not paths[2].exists()
    assert audit(*paths)["response_records"] == 0


def test_witness_failure_closes_pair_without_retry(tmp_path):
    paths, result = invoke(tmp_path / "observed", break_witness=True)
    assert result.result.status == "model_error"
    assert paths[2].read_text() == "preserve"
    assert len(paths[1].read_text().splitlines()) == 1
    receipt = json.loads((paths[0] / "pair_runtime.json").read_text())
    workers = receipt["snapshot"]["workers"]
    assert all(w["closed"] and not w["handle_pending"] for w in workers.values())
    assert all(e["reaped"] for w in workers.values() for e in w["lifecycle"])
    assert len(workers["guard"]["attempts"]) == 2
    with pytest.raises(ValueError):
        audit(*paths)
