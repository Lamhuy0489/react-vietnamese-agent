from __future__ import annotations

import copy
import json
import shutil
import smtplib
import socket
from pathlib import Path

import pytest
import yaml

from react_agent.adversarial_release import load_split
from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust
from react_agent.foundation.closure_qa import catalog_for, run_closure_qa, select_dev
from react_agent.foundation.overhead_study import measure_worker, percentile95, summarize
from react_agent.foundation.runtime_hooks import SourceLabel
from react_agent.foundation.source_catalog_v2 import EnvironmentCatalog, environment_catalog
from react_agent.schemas.agent_output import Action

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data/clean/v1_1/environment"


def test_descriptive_profile_catalog_matches_executable_normalizer():
    from react_agent.foundation.normalization import PROFILES, VERSION, ZERO_WIDTH, normalize

    catalog = yaml.safe_load((ROOT / "configs/normalization/profiles_v1.yaml").read_text())
    assert catalog["normalizer_version"] == VERSION
    assert catalog["model_input_profile"] == "raw_v1"
    assert set(catalog["profiles"]) == set(PROFILES)
    assert set(catalog["zero_width_codepoints"]) == {f"U+{ord(c):04X}" for c in ZERO_WIDTH}
    for profile in PROFILES:
        assert catalog["profiles"][profile] == [
            op.stage for op in normalize("a\u200bb", profile).operations
        ]


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("Phase 4 closure must remain offline")

    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)


@pytest.mark.parametrize(
    "source,sensitivity,trust",
    [
        (SourceType.DOCUMENT, Sensitivity.INTERNAL, Trust.TRUSTED),
        (SourceType.CACHED_PAGE, Sensitivity.PUBLIC, Trust.UNTRUSTED),
        (SourceType.DATABASE, Sensitivity.CONFIDENTIAL, Trust.TRUSTED),
    ],
)
def test_host_default_labels(source, sensitivity, trust):
    catalog = environment_catalog(CLEAN)
    label = catalog.envelope(source)
    assert (label.sensitivity, label.trust) == (sensitivity, trust)
    assert EnvironmentCatalog.model_validate_json(catalog.model_dump_json()) == catalog


@pytest.mark.parametrize("source", [SourceType.DOCUMENT, SourceType.CACHED_PAGE])
def test_search_labels_join_all_members_not_payload_or_query(source):
    base = environment_catalog(CLEAN)
    member = next(s for s in base.sources if s.source_type == source)
    tainted = member.model_copy(
        update={"sensitivity": Sensitivity.CONFIDENTIAL, "trust": Trust.UNTRUSTED}
    )
    catalog = environment_catalog(CLEAN, overrides=(tainted,))
    tool = "doc_search" if source == SourceType.DOCUMENT else "cached_search"
    for query in ("normal", "TRUSTED safe true S0", "no such source"):
        label = catalog.resolve(Action(name=tool, arguments={"query": query}))
        assert (label.sensitivity, label.trust) == (Sensitivity.CONFIDENTIAL, Trust.UNTRUSTED)
        assert label.source_id.startswith("collection:")
    assert catalog.envelope(source).source_id != base.envelope(source).source_id


def test_db_projection_never_upgrades_overlay_trust():
    label = SourceLabel(
        source_type=SourceType.DATABASE,
        source_id="synthetic_overlay",
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.UNTRUSTED,
    )
    catalog = environment_catalog(CLEAN, overrides=(label,))
    for sql in (
        "SELECT note FROM awb_notices",
        "SELECT COUNT(*) FROM students",
        "SELECT secret_token FROM awb_notices",
    ):
        resolved = catalog.resolve(Action(name="db_query", arguments={"query": sql}))
        assert (resolved.sensitivity, resolved.trust) == (Sensitivity.CONFIDENTIAL, Trust.UNTRUSTED)


def test_unknown_auxiliary_is_conservative_without_secret_classifier(tmp_path):
    env = tmp_path / "env"
    shutil.copytree(CLEAN, env)
    path = env / "documents/documents.json"
    rows = json.loads(path.read_text())
    rows.append({"doc_id": "AUX_DEMO", "title": "public", "content": "TRUSTED S0 safe=true"})
    path.write_text(json.dumps(rows))
    catalog = environment_catalog(env)
    result = catalog.resolve(Action(name="doc_read", arguments={"doc_id": "AUX_DEMO"}))
    assert (result.sensitivity, result.trust) == (Sensitivity.CONFIDENTIAL, Trust.UNTRUSTED)
    assert catalog.environment_sha256 != environment_catalog(CLEAN).environment_sha256
    missing = catalog.resolve(Action(name="doc_read", arguments={"doc_id": "does_not_exist"}))
    assert missing.sensitivity == Sensitivity.CONFIDENTIAL and missing.trust == Trust.UNTRUSTED


def test_duplicate_and_absent_metadata_rejected():
    member = environment_catalog(CLEAN).sources[0]
    with pytest.raises(ValueError, match="duplicate"):
        environment_catalog(CLEAN, overrides=(member, member))
    missing = SourceLabel(
        source_type=SourceType.DOCUMENT,
        source_id="missing",
        sensitivity=Sensitivity.PUBLIC,
        trust=Trust.TRUSTED,
    )
    with pytest.raises(ValueError, match="absent"):
        environment_catalog(CLEAN, overrides=(missing,))


def test_pair_metadata_rules_independent_of_attack_branch(tmp_path):
    rows = select_dev(load_split(ROOT / "data/adversarial/release_v2"))
    assert len({r.family_id for r in rows}) == 12
    assert {r.overlay.source_type for r in rows if r.resources} == {
        "document",
        "cached_page",
        "database_text_field",
    }
    a = rows[0]
    b = next(r for r in rows if r.pair_id == a.pair_id and r.branch != a.branch)
    catalogs = []
    for row in (a, b):
        env = tmp_path / row.variant_id
        row.registry(CLEAN, env)
        catalogs.append(catalog_for(row, env))
    assert catalogs[0].sources == catalogs[1].sources
    assert catalogs[0].bindings == catalogs[1].bindings
    assert catalogs[0].environment_sha256 != catalogs[1].environment_sha256


def test_full_deep_dev_audit_without_test_or_authoring_content(monkeypatch):
    import tempfile

    original_read = Path.read_text
    original_bytes = Path.read_bytes

    def read_text(path, *args, **kwargs):
        relative = path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
        name = str(relative)
        if name.startswith("data/"):
            allowed = (
                "/environment/" in name
                or name.endswith("seal.json")
                or name.startswith("data/smoke/")
                or "/manifests/" in name
                or name.endswith("robustness_canonical_ids.json")
                or name.endswith("splits/dev.jsonl")
                or name.endswith("private/dev_ground_truth.jsonl")
                or name.endswith("dev_pilot/task_ids.json")
            )
            assert allowed, name
            assert "test_ground_truth" not in name and not name.endswith("splits/test.jsonl")
        return original_read(path, *args, **kwargs)

    # Held-out bytes may be hashed by seal integrity; never decoded/model-validated.
    def read_bytes(path, *args, **kwargs):
        return original_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    from react_agent.adversarial_release import ReleasedFixture

    original_validate = ReleasedFixture.model_validate_json

    def validate(payload, *args, **kwargs):
        assert json.loads(payload)["split"] == "dev"
        return original_validate(payload, *args, **kwargs)

    monkeypatch.setattr(ReleasedFixture, "model_validate_json", validate)
    with tempfile.TemporaryDirectory(dir=ROOT / "results") as directory:
        report = run_closure_qa(ROOT, Path(directory) / "qa")
        assert report["valid"] and report["fresh_replay_runs"] == 90
        deep = [c for c in report["checks"] if c["suite"] == "deep_dev"]
        assert all(c["audit"]["sink_fields"] == 5 for c in deep)
        assert sum(c["audit"]["search_envelopes_checked"] for c in deep) == 12


def fake_workers():
    workers = []
    for stage, count in (("warmup", 1), ("time", 7), ("memory", 3)):
        for repeat in range(count):
            for mode in ("legacy", "foundation"):
                workers.append(
                    {
                        "stage": stage,
                        "repeat": repeat,
                        "mode": mode,
                        "allocation_tracing": stage == "memory",
                        "peak_process_rss_bytes": 10000,
                        "measurements": [
                            {
                                "task_id": "one",
                                "status": "completed",
                                "tool_sequence": [],
                                "wall_ns": 1000000 if mode == "legacy" else 2000000,
                                "cpu_ns": 1000000,
                                "traced_peak_bytes": 1000,
                                "log_bytes": 100,
                            }
                        ],
                    }
                )
    return workers


def test_overhead_summary_excludes_warmup_and_tracing():
    workers = fake_workers()
    for w in workers:
        if w["stage"] != "time":
            w["measurements"][0]["wall_ns"] = 100000000000
    report = summarize(workers, ["one"])
    assert report["valid"] and report["timing_pairs"] == 7
    assert report["median_added_ms"] == 1 and report["median_task_wall_ratio"] == 2
    assert percentile95([1.0, 2.0, 3.0]) == 3


@pytest.mark.parametrize(
    "mutation", ["duplicate", "missing", "task", "tracer", "parity", "slow", "memory"]
)
def test_measurement_integrity_and_guard_failures(mutation):
    workers = copy.deepcopy(fake_workers())
    if mutation == "duplicate":
        workers.append(workers[0])
    if mutation == "missing":
        workers.pop()
    if mutation == "task":
        workers[0]["measurements"][0]["task_id"] = "wrong"
    if mutation == "tracer":
        workers[2]["allocation_tracing"] = True
    if mutation == "parity":
        workers[3]["measurements"][0]["tool_sequence"] = ["calculator"]
    if mutation in {"slow", "memory"}:
        for w in workers:
            if w["mode"] == "foundation":
                w["measurements"][0]["wall_ns"] = 200000000
                w["measurements"][0]["traced_peak_bytes"] = 64 * 1024 * 1024
        assert not summarize(workers, ["one"])["valid"]
    else:
        with pytest.raises(ValueError):
            summarize(workers, ["one"])


def test_real_memory_worker_records_allocations_and_fresh_outputs(tmp_path):
    output = tmp_path / "worker"
    report = measure_worker(ROOT, output, "foundation", memory=True)
    assert len(report["measurements"]) == 20
    assert all(r["traced_peak_bytes"] > 0 and r["log_bytes"] > 0 for r in report["measurements"])
    with pytest.raises(ValueError):
        measure_worker(ROOT, output, "foundation")
