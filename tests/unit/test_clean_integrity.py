"""Regression tests use toy facts, not held-out task content."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from react_agent.schemas.clean_task import AnswerFact, CleanGroundTruth, EvidenceRef
from react_agent.validation.clean_integrity import (
    FROZEN_COMPONENTS,
    assert_clean_version_writable,
    dataset_digest,
    semantic_instance_groups,
    semantic_instance_signature,
    validate_frozen_components,
)
from react_agent.validation.clean_pool import _normalize

ROOT = Path(__file__).resolve().parents[2]


def toy_ground_truth(task_id: str, fact_id: str) -> CleanGroundTruth:
    return CleanGroundTruth(
        task_id=task_id,
        expected_outcome="answer",
        required_tools=["doc_read"],
        acceptable_sequences=[["doc_read"]],
        required_answer_facts=[
            AnswerFact(fact_id=fact_id, type="number", value=42, comparator="numeric_equal")
        ],
        required_evidence=[EvidenceRef(source_type="document", source_id="TOY_DOC")],
        retrieval_targets=["TOY_DOC"],
        minimum_required_steps=1,
    )


def test_instance_identity_ignores_local_labels_and_tool_path() -> None:
    first = toy_ground_truth("clean_9001", "original_answer")
    recovery = toy_ground_truth("clean_9002", "retry_answer")
    recovery.acceptable_sequences = [["doc_read", "doc_read"]]
    assert semantic_instance_signature(first) == semantic_instance_signature(recovery)
    assert semantic_instance_groups([first, recovery]) == [["clean_9001", "clean_9002"]]


def test_instance_identity_distinguishes_sources_and_fact_values() -> None:
    first = toy_ground_truth("clean_9001", "answer_one")
    second = toy_ground_truth("clean_9002", "answer_two")
    second.required_answer_facts[0].value = 43
    assert semantic_instance_groups([first, second]) == []
    second.required_answer_facts[0].value = 42
    second.required_evidence[0].source_id = "DIFFERENT_DOC"
    assert semantic_instance_groups([first, second]) == []


def test_instance_identity_is_independent_of_fact_and_evidence_order() -> None:
    first = toy_ground_truth("clean_9001", "number_fact")
    first.required_answer_facts.append(
        AnswerFact(fact_id="name_fact", type="string", value="toy", comparator="exact_normalized")
    )
    first.required_evidence.append(EvidenceRef(source_type="document", source_id="SECOND_DOC"))
    second = first.model_copy(deep=True)
    second.required_answer_facts.reverse()
    second.required_evidence.reverse()
    assert semantic_instance_signature(first) == semantic_instance_signature(second)


def test_vietnamese_normalization_preserves_words_and_handles_stroke_d() -> None:
    assert _normalize("Đăng ký") == "đăng ký"
    assert _normalize("Đăng ký", strip_accents=True) == "dang ky"
    assert _normalize("đang", strip_accents=False) != _normalize("dang", strip_accents=False)


@pytest.mark.parametrize(
    "marker",
    [
        "manifests/benchmark_manifest.json",
        "manifests/split_manifest.json",
        "splits/dev.jsonl",
        "splits/test.jsonl",
        "private/dev_ground_truth.jsonl",
        "private/test_ground_truth.jsonl",
    ],
)
def test_seal_guard_rejects_even_partial_or_malformed_markers(tmp_path: Path, marker: str) -> None:
    path = tmp_path / marker
    path.parent.mkdir(parents=True)
    path.write_text("not valid JSON", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        assert_clean_version_writable(tmp_path)
    assert path.read_text() == "not valid JSON"


def test_unsealed_new_version_can_be_authored(tmp_path: Path) -> None:
    assert_clean_version_writable(tmp_path)


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "script", ["build_clean_environment", "author_clean_pool", "split_clean_benchmark"]
)
def test_generator_entrypoints_refuse_before_any_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script: str
) -> None:
    module = load_script(script)
    monkeypatch.setattr(module, "CLEAN_ROOT", tmp_path)
    seal = tmp_path / "manifests" / "benchmark_manifest.json"
    seal.parent.mkdir()
    seal.write_text('{"frozen": false}', encoding="utf-8")
    before = list(tmp_path.rglob("*"))
    with pytest.raises(RuntimeError, match="Refusing to overwrite"):
        module.main()
    assert list(tmp_path.rglob("*")) == before
    assert seal.read_text() == '{"frozen": false}'


def test_frozen_manifest_requires_inventory_content_and_aggregate(tmp_path: Path) -> None:
    schema_path = tmp_path / "schemas" / "clean_task.py"
    hashes: dict[str, str] = {}
    for relative in FROZEN_COMPONENTS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"toy component: {relative}", encoding="utf-8")
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"component_hashes": hashes, "dataset_hash": dataset_digest(hashes)}
    assert validate_frozen_components(tmp_path, schema_path, manifest) == []
    bad_aggregate = {**manifest, "dataset_hash": "0" * 64}
    assert "aggregate dataset hash mismatch" in validate_frozen_components(
        tmp_path, schema_path, bad_aggregate
    )
    stripped = {"component_hashes": {}, "dataset_hash": dataset_digest({})}
    assert validate_frozen_components(tmp_path, schema_path, stripped)
    schema_path.write_text("tampered", encoding="utf-8")
    assert "frozen component hash mismatch: schemas/clean_task.py" in validate_frozen_components(
        tmp_path, schema_path, manifest
    )


def test_frozen_manifest_rejects_invalid_hash_type(tmp_path: Path) -> None:
    manifest = {"component_hashes": {"splits/dev.jsonl": None}, "dataset_hash": "invalid"}
    assert validate_frozen_components(tmp_path, tmp_path / "schema.py", manifest)


def test_bundle_rejects_invalid_data_without_deleting_prior_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_script("prepare_kaggle_phase2")
    sentinel = tmp_path / "previous_bundle.json"
    sentinel.write_text(json.dumps({"preserve": True}), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["prepare", "--owner", "toy", "--dataset-version", "1", "--output", str(tmp_path)],
    )
    monkeypatch.setattr(
        module, "validate_clean_split", lambda: {"valid": False, "failures": ["toy"]}
    )
    with pytest.raises(SystemExit, match="Refusing to package an invalid"):
        module.main()
    assert json.loads(sentinel.read_text()) == {"preserve": True}
