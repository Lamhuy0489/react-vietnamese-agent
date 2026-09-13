"""Reuse frozen package mutation probes against the new versioned wrapper."""

import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def builder(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("prepare_phase5_security_runtime")


@pytest.fixture
def wrapper(builder):
    return builder.load(ROOT / builder.TEMPLATE)


def test_source_allowlist_and_pins(builder, wrapper):
    prior = builder.check_pins()
    assert set(prior["overlay_sha256"]) < wrapper.OVERLAY_PATHS
    assert len(wrapper.OVERLAY_PATHS) == 82
    # Preserve the worker namespace package; repository __init__ imports pool QA.
    assert "src/react_agent/validation/__init__.py" not in wrapper.OVERLAY_PATHS
    assert "src/react_agent/security_v1/pair_runtime_v2.py" in wrapper.OVERLAY_PATHS
    for name in wrapper.OVERLAY_PATHS:
        assert (ROOT / name).is_file()
        assert not any(s in name.lower() for s in ("credential", "/private/", "/test", "/pool/"))


@pytest.mark.parametrize("fault", ["hash", "missing", "extra", "overwrite"])
def test_overlay_mutations(wrapper, tmp_path, fault):
    helper = importlib.import_module("test_policy_native_compat_v1")
    helper.test_overlay_rejects_mutations(wrapper, tmp_path, fault)


@pytest.mark.parametrize("failure", [None, "collector", "runner", "audit"])
def test_native_route_no_retry(wrapper, tmp_path, failure):
    from types import SimpleNamespace

    output, project, inputs = (tmp_path / name for name in ("output", "project", "input"))
    output.mkdir()
    pubs = project / "docs/evaluation/publisher_policy_v1"
    pubs.mkdir(parents=True)
    for role in ("agent", "guard"):
        (pubs / f"{role}_generation_config.json").write_text("{}")
    agent = inputs / "qwen2.5/transformers/7b-instruct/1"
    agent.mkdir(parents=True)
    (agent / "config.json").write_text("{}")
    seen = []
    expected = [
        "scripts/collect_phase5_tokenizer_metadata.py",
        "scripts/run_phase5_security_runtime_probe.py",
        "scripts/audit_phase5_security_runtime_probe.py",
    ]
    failed = {"collector": 0, "runner": 1, "audit": 2}.get(failure)

    def run(*args):
        command = args[4:]
        seen.append(command)
        assert command[0] == expected[len(seen) - 1]
        if failed == len(seen) - 1:
            raise RuntimeError("synthetic routing failure")

    args = (
        SimpleNamespace(run=run),
        Path("python"),
        project,
        None,
        "a" * 40,
        tmp_path / "guard",
        tmp_path / "snapshot",
        output,
        inputs,
    )
    if failure:
        with pytest.raises(RuntimeError):
            wrapper.run_payload(*args)
        assert len(seen) == failed + 1
    else:
        wrapper.run_payload(*args)
        assert len(seen) == 3
        assert seen[1][1:3] == ("--backend", "hf")
