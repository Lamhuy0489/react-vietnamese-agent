"""Explicit synthetic receipts with real spawned transport; no native/model claims."""

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from react_agent.foundation.artifacts import canonical_json
from react_agent.foundation.normalization import text_hash
from react_agent.llm.agent_mount_v1 import write_receipt
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.llm.document_runtime_probe_v1 import GENERATION, RUNTIME
from react_agent.llm.guard_diagnostic_backend_v2 import DiagnosticFactory
from react_agent.llm.guard_diagnostic_pair_v2 import DiagnosticPair
from react_agent.llm.guard_observer_probe_v2 import PROFILE, SAFE, StubFactory, case, config
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend, native_root
from react_agent.security_v1.constrained_runtime_v1 import (
    HostClassifier,
    run_pair_task,
    run_synthetic_pair_task,
)
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.guard import GuardInput
from react_agent.security_v1.guard_bare_json_v1 import PROMPT
from react_agent.tools.factory import build_clean_registry
from react_agent.validation.constrained_runtime_audit_v1 import audit_join, cache_encoding
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY, LANGUAGE, POLICY, complete

REQUEST = GuardInput(
    user_instruction="Read public synthetic content.",
    source_type="DOCUMENT",
    candidate_content="Synthetic public content.",
)


def emit(root, binding, fault="none"):
    counts = dict(generate=1, processors=1, callbacks=28)
    records = dict(
        entered=dict(execution_identity=IDENTITY),
        admitted=dict(
            input_tokens=7,
            language_sha256=LANGUAGE,
            policy_sha256=POLICY,
            processor_types=[
                "RepetitionPenaltyLogitsProcessor",
                "PrefixConstrainedLogitsProcessor",
            ],
        ),
        restored=dict(methods_restored=True, counts=counts),
        completed=dict(
            counts=counts,
            output_tokens=28,
            output_token_sha256="b" * 64,
            response_sha256=text_hash(SAFE),
            execution_identity=IDENTITY,
        ),
    )
    if fault == "backend":
        records.pop("completed")
        records["error"] = dict(error_class="RuntimeError", counts=counts)
    if fault == "pid":
        binding = dict(binding, pid=binding["pid"] + 1)
    root.mkdir(parents=True)
    for stage, values in records.items():
        if fault == "missing" and stage == "restored":
            continue
        write_receipt(
            root / (stage + ".json"),
            dict(protocol="constrained_policy_worker_v1", stage=stage, **binding, **values),
        )


@dataclass(frozen=True)
class SyntheticFactory:
    root: Path
    fault: str = "none"

    def __call__(self):
        return SyntheticBackend(self)


class SyntheticBackend:
    model_id = "synthetic-guard"
    model_revision = PROFILE

    def __init__(self, factory):
        self.factory, self.index = factory, 0

    def generate(self, messages, generation):
        assert messages[0] == dict(role="system", content=PROMPT)
        assert generation == GenerationConfig(max_new_tokens=128)
        self.index += 1
        emit(
            self.factory.root / f"request_{self.index:06d}",
            dict(
                pid=os.getpid(),
                model_id=self.model_id,
                model_revision=self.model_revision,
                request_index=self.index,
                request_sha256=text_hash(canonical_json(messages)),
                generation_sha256=text_hash(canonical_json(generation.model_dump())),
            ),
            self.factory.fault,
        )
        if self.factory.fault == "backend":
            raise RuntimeError("synthetic error")
        return ModelResponse(text=SAFE, model_id=self.model_id, model_revision=self.model_revision)


def pair_for(root, key="CALC_A2", fault="none"):
    return DiagnosticPair(
        StubFactory("agent", key, "valid"),
        DiagnosticFactory(SyntheticFactory(root / "constraints", fault), root / "sidecar.jsonl"),
        config("stub"),
        root / "witness.jsonl",
    )


def test_classifier_cache_has_no_extra_ipc_and_rejects_evidence_drift(tmp_path):
    pair = pair_for(tmp_path)
    try:
        pair.start()
        backend = ConstrainedRoleBackend(pair, tmp_path / "constraints")
        guard = HostClassifier(backend)
        first = guard.classify(REQUEST)
        assert first.status == "OK" and not first.cache_hit
        assert guard.classify(REQUEST).cache_hit
        assert len(backend.attempts) == 1 and len(backend.host_attempts) == 1
        path = tmp_path / "constraints/request_000001/restored.json"
        path.write_text(path.read_text() + " ")
        failure = guard.classify(REQUEST)
        assert failure.error_code == "IDENTITY_CHANGED" and not failure.cache_hit
        assert not guard._cache and backend.retired
        assert len(backend.attempts) == 1
    finally:
        pair.close()


@pytest.mark.parametrize("fault", ["missing", "pid", "backend"])
def test_failed_receipt_or_worker_never_cached_or_retried(tmp_path, fault):
    pair = pair_for(tmp_path, fault=fault)
    try:
        pair.start()
        backend = ConstrainedRoleBackend(pair, tmp_path / "constraints")
        guard = HostClassifier(backend)
        outcome = guard.classify(REQUEST)
        assert outcome.status == "ERROR" and not guard._cache and backend.retired
        assert guard.classify(REQUEST).status == "ERROR"
        assert len(backend.attempts) == 1
    finally:
        pair.close()


@pytest.mark.parametrize("key", ["CALC_A2", "CALC_A6", "DOC_A2", "DOC_A6"])
def test_spawned_runtime_and_readonly_join(tmp_path, key):
    from react_agent.security_v1 import guard_bare_json_v1, pair_runtime_v3, runtime_v5

    namespaces = [
        (module, dict(vars(module))) for module in (guard_bare_json_v1, pair_runtime_v3, runtime_v5)
    ]
    pair = pair_for(tmp_path, key)
    task, catalog, level = case(key)
    result = run_synthetic_pair_task(
        task,
        pair=pair,
        constrained=tmp_path / "constraints",
        output=tmp_path / "execution",
        registry_factory=lambda: build_clean_registry(Path("data/clean/v1_1/environment")),
        security=configuration(level),
        runtime_config=RUNTIME,
        generation=GENERATION,
        source_catalog=catalog,
    )
    assert result.result.status == "completed"
    args = (
        tmp_path / "execution",
        tmp_path / "sidecar.jsonl",
        tmp_path / "witness.jsonl",
        tmp_path / "constraints",
    )
    first = audit_join(*args)
    assert first == audit_join(*args)
    assert first["valid"] and len(first["completed"]) == 2 and not first["incomplete"]
    assert not first["native_model_authenticated"]
    assert all(
        vars(module)[name] is value
        for module, before in namespaces
        for name, value in before.items()
    )
    assert all(w["closed"] for w in pair.snapshot()["workers"].values())
    path = tmp_path / "execution/runtime/trace_guard.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["outcome"]["cache_key"] = "a" * 64
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="cache identity"):
        audit_join(*args)


def test_native_entry_rejects_synthetic_factory_before_start(tmp_path):
    pair = pair_for(tmp_path)
    try:
        with pytest.raises(ValueError, match="native constrained"):
            run_pair_task(case("CALC_A2")[0], pair=pair)
        assert pair.state == "NEW" and not pair.snapshot()["workers"]["guard"]["attempts"]
    finally:
        pair.close()


def test_failed_runtime_preserves_partial_receipts_and_local_rejection(tmp_path):
    pair = pair_for(tmp_path, fault="backend")
    task, catalog, level = case("CALC_A2")
    result = run_synthetic_pair_task(
        task,
        pair=pair,
        constrained=tmp_path / "constraints",
        output=tmp_path / "execution",
        registry_factory=lambda: build_clean_registry(Path("data/clean/v1_1/environment")),
        security=configuration(level),
        runtime_config=RUNTIME,
        generation=GENERATION,
        source_catalog=catalog,
    )
    assert result.result.status == "model_error"
    audit = audit_join(
        tmp_path / "execution",
        tmp_path / "sidecar.jsonl",
        tmp_path / "witness.jsonl",
        tmp_path / "constraints",
    )
    assert not audit["completed"] and len(audit["incomplete"]) == 1
    receipt = json.loads((tmp_path / "execution/pair_runtime.json").read_text())
    hosts = receipt["host_role_attempts"]["guard"]
    assert len(hosts) == 2
    assert hosts[-1]["error_class"] == "ConstrainedHostAdmissionError"
    assert hosts[-1]["worker_attempts_before"] == hosts[-1]["worker_attempts_after"] == 1


@pytest.mark.parametrize(
    "fault", ["identity", "model", "factory", "history", "owner", "dead", "config"]
)
def test_host_identity_and_health_gate_before_cache(tmp_path, fault):
    pair = pair_for(tmp_path)
    try:
        pair.start()
        backend = ConstrainedRoleBackend(pair, tmp_path / "constraints")
        guard = HostClassifier(backend)
        assert guard.classify(REQUEST).status == "OK"
        if fault == "identity":
            backend.constraint_identity = "f" * 64
        elif fault == "model":
            backend.model_revision = "wrong"
        elif fault == "factory":
            pair._workers["guard"].factory = SyntheticFactory(tmp_path / "other")
        elif fault == "history":
            backend._validated = 0
        elif fault == "owner":
            backend._owner = -1
        elif fault == "config":
            backend.config = pair.config.execution("agent", cold=False)
        else:
            pair._workers["guard"].retire()
        outcome = guard.classify(REQUEST)
        assert outcome.status == "ERROR" and not outcome.cache_hit and not guard._cache
        assert len(backend.attempts) == 1
    finally:
        pair.close()


def test_native_factory_admission_is_lazy(tmp_path):
    from test_native_guard_diagnostics_v1 import pin

    from react_agent.llm.native_constrained_pair_v1 import native_pair

    pair = native_pair(
        tmp_path / "agent",
        tmp_path / "inventory",
        tmp_path / "guard",
        pin(),
        tmp_path / "native",
        tmp_path / "attention",
        tmp_path / "policy",
        witness=tmp_path / "witness",
        constrained=tmp_path / "constraints",
    )
    try:
        assert native_root(pair) == tmp_path / "constraints" and not list(tmp_path.iterdir())
    finally:
        pair.close()


def test_host_classifier_lock_rejects_reentry_without_ledger_or_worker_call(tmp_path):
    pair = pair_for(tmp_path)
    try:
        backend = ConstrainedRoleBackend(pair, tmp_path / "constraints")
        guard = HostClassifier(backend)
        guard._host_lock.acquire()
        try:
            with pytest.raises(RuntimeError, match="single host classifier"):
                guard.classify(REQUEST)
        finally:
            guard._host_lock.release()
        assert not backend.host_attempts and not backend.attempts and pair.state == "NEW"
    finally:
        pair.close()


def test_cache_encoding_only_extends_cache_objects():
    item = dict(model="m", revision="r", prompt="p", generation={}, input={})
    before = copy.deepcopy(item)
    assert json.loads(cache_encoding(item)) == dict(
        item, protocol="constrained_classifier_v1", decoding=IDENTITY
    )
    assert item == before
    for other in ({}, [item], dict(item, extra=True), {"generation": {}}):
        assert cache_encoding(other) == canonical_json(other)


@pytest.fixture
def receipt_case(tmp_path):
    binding = dict(
        pid=23,
        model_id="synthetic-guard",
        model_revision=PROFILE,
        request_index=1,
        request_sha256="a" * 64,
        generation_sha256="d" * 64,
    )
    root = tmp_path / "request"
    emit(root, binding)
    return root, binding


@pytest.mark.parametrize(
    "fault",
    [
        "pid",
        "index",
        "response",
        "policy",
        "language",
        "chain",
        "counts",
        "bool",
        "identity",
        "restored",
        "extra",
        "missing",
        "duplicate",
        "directory",
        "link",
    ],
)
def test_receipt_mutations_rejected(receipt_case, fault):
    root, binding = receipt_case
    stage = "admitted" if fault in {"policy", "language", "chain"} else "completed"
    if fault == "restored":
        stage = "restored"
    path = root / (stage + ".json")
    row = json.loads(path.read_text())
    if fault == "missing":
        path.unlink()
    elif fault == "duplicate":
        path.write_text('{"stage":"completed","stage":"completed"}')
    elif fault == "directory":
        (root / "extra").mkdir()
    elif fault == "link":
        (root / "extra").symlink_to(path)
    else:
        if fault == "pid":
            row["pid"] += 1
        elif fault == "index":
            row["request_index"] += 1
        elif fault == "response":
            row["response_sha256"] = "e" * 64
        elif fault in {"policy", "language"}:
            row[fault + "_sha256"] = "e" * 64
        elif fault == "chain":
            row["processor_types"].reverse()
        elif fault == "counts":
            row["counts"]["callbacks"] = 27
        elif fault == "bool":
            row["output_tokens"] = True
        elif fault == "identity":
            row["execution_identity"] = "f" * 64
        elif fault == "restored":
            row["methods_restored"] = False
        else:
            row["extra"] = True
        path.write_text(json.dumps(row))
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        complete(root, binding, text_hash(SAFE))
