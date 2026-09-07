from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import smtplib
import socket
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from react_agent.adversarial_release import ReleasedFixture, load_split
from react_agent.agent import AgentRuntime
from react_agent.authoring import release_v2 as release
from react_agent.authoring.selected_runtime import load_selected
from react_agent.authoring.workbench_qa import RecordingReplay, file_hashes
from react_agent.schemas.trace import TraceEvent

ROOT = Path(__file__).resolve().parents[2]
TASKS = sorted(
    json.loads(
        (ROOT / "data/adversarial/linguistic_authoring_v1/paraphrase_edits.json").read_text()
    )
)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("release QA must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.fixture(scope="module")
def assembled() -> tuple:
    with TemporaryDirectory(prefix="release_qa_", dir=ROOT / "data/adversarial") as directory:
        destination = Path(directory) / "snapshot"
        report = release.assemble(ROOT, destination)
        _, cases = load_selected(ROOT)
        rows = release.selected_rows(ROOT, cases)
        yield destination, report, cases, rows


def test_complete_integration_reuses_and_archives_exact_references(assembled: tuple) -> None:
    directory, report, _, rows = assembled
    assert release.validate_integration(ROOT, directory) == report
    assert len(rows) == 700 and report["reused_reference_paths"] == 1692
    assert report["fresh_replay_runs"] == report["real_model_runs"] == 0
    assert report["test_assigned_reference_paths"] == 732
    assert not report["phase3_accepted"] and not report["test_sealed"]
    assert not report["independent_human_review"]
    assert not (directory / "seal.json").exists()


@pytest.mark.parametrize("task", TASKS)
def test_all_released_payloads_execute_safe_path_via_public_registry(
    assembled: tuple, task: str, tmp_path: Path
) -> None:
    _, _, cases, rows = assembled
    case = cases[task]
    for row in (r for r in rows if r.task.task_id == task):
        output = tmp_path / row.variant_id
        registry = row.registry(ROOT / "data/clean/v1_1/environment", output / "environment")
        assert len(registry.names) == 8
        backend = RecordingReplay(
            case.candidate.oracle.safe_actions, case.candidate.oracle.safe_final
        )
        run = AgentRuntime(backend, registry).run(row.task, trace_path=output / "trace.jsonl")
        assert run.status == "completed" and not run.parse_errors
        events = [
            TraceEvent.model_validate_json(s)
            for s in (output / "trace.jsonl").read_text().splitlines()
        ]
        assert (
            case.score(events, output / "environment/database/university.db")
            == case.expected[row.branch, "safe"]
        )
        initial = json.dumps(backend.contexts[0], ensure_ascii=False)
        assert "safe_actions" not in initial and "negative_actions" not in initial
        assert all(a.value not in initial for a in case.candidate.oracle.sensitive_artifacts)


@pytest.mark.parametrize(
    "change",
    ["split_file", "payload", "mapping", "schema", "qa", "count_type", "source_map", "archive"],
)
def test_release_cannot_be_accepted_after_mutation(
    assembled: tuple, tmp_path: Path, change: str
) -> None:
    directory, _, _, _ = assembled
    target = tmp_path / "copy"
    shutil.copytree(directory, target)
    if change == "split_file":
        first, second = target / "dev_attack.jsonl", target / "dev_benign.jsonl"
        a, b = first.read_bytes(), second.read_bytes()
        first.write_bytes(b)
        second.write_bytes(a)
    elif change == "payload":
        path = target / "dev_attack.jsonl"
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        rows[0]["task"]["instruction"] = "Đã thay đổi tác vụ."
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    elif change in {"mapping", "schema"}:
        (target / (change + ".json")).write_text("{}")
    else:
        path = target / "qa.json"
        qa = json.loads(path.read_text())
        if change == "qa":
            qa["phase3_accepted"] = True
        elif change == "count_type":
            qa["variants"] = 700.0
        elif change == "source_map":
            qa["source_sha256"].pop(next(iter(qa["source_sha256"])))
        else:
            archive = target / "reference_traces.jsonl.gz"
            rows = [json.loads(s) for s in gzip.decompress(archive.read_bytes()).splitlines()]
            rows[0]["events"] = rows[1]["events"]
            raw = ("\n".join(release.encoded(r) for r in rows) + "\n").encode()
            archive.write_bytes(gzip.compress(raw, mtime=0))
            qa["reference_archive_sha256"] = hashlib.sha256(raw).hexdigest()
        path.write_text(json.dumps(qa))
    with pytest.raises(ValueError):
        release.validate_integration(ROOT, target)


def test_dev_loader_never_opens_test_or_private_inputs(
    assembled: tuple, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory, _, _, _ = assembled
    target = tmp_path / "copy"
    shutil.copytree(directory, target)
    # Isolated loader fixture, not a real acceptance seal.
    (target / "seal.json").write_text(
        json.dumps(
            {
                "test_sealed": True,
                "phase3_accepted": True,
                "release_sha256": file_hashes(target),
            }
        )
    )
    original = Path.open

    def guard(path: Path, *args: object, **kwargs: object) -> object:
        assert path.parent == target
        assert path.name in {"seal.json", "dev_attack.jsonl", "dev_benign.jsonl"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    assert len(load_split(target)) == 400
    with pytest.raises(ValueError, match="held-out"):
        load_split(target, "test")


def test_public_fixture_forbids_oracle_fields(assembled: tuple) -> None:
    _, _, _, rows = assembled
    data = rows[0].model_dump()
    data["safe_actions"] = []
    with pytest.raises(ValueError):
        ReleasedFixture.model_validate(data)


def test_seal_requires_committed_sources(assembled: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, _, _, _ = assembled
    monkeypatch.setattr(release.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="Git"):
        release.seal(ROOT, directory)


def test_fresh_output_and_default_unsealed_rejection(assembled: tuple) -> None:
    directory, _, _, _ = assembled
    with pytest.raises(ValueError, match="fresh"):
        release.assemble(ROOT, directory)
    with pytest.raises(ValueError, match="sealed"):
        load_split(directory)
