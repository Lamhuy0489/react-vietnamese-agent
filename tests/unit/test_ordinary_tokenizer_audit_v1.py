"""Public metadata and synthetic joined evidence only; no native model imports."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from test_ordinary_pair_audit_v1 import ROOT
from test_ordinary_pair_audit_v1 import native as native  # noqa: F401 - pytest fixture
from test_ordinary_pair_audit_v1 import sample as sample  # noqa: F401 - pytest fixture
from test_ordinary_pair_audit_v1 import template as template  # noqa: F401 - pytest fixture

from react_agent.llm.agent_runtime_input_v1 import INVENTORY_SHA256
from react_agent.validation import ordinary_tokenizer_audit_v1 as impl
from react_agent.validation import tokenizer_metadata_v1 as metadata


@pytest.fixture
def tokenizers(tmp_path: Path) -> Path:
    raw = json.loads((ROOT / "docs/evaluation/tokenizer_config_v1_source.json").read_text())[
        "source_utf8"
    ].encode()
    root = tmp_path / "tokenizers"
    root.mkdir()
    for role in impl.ROLES:
        (root / f"{role}_tokenizer_config.json").write_bytes(raw)
    return root


@pytest.fixture
def inputs(native: dict[str, Any], tokenizers: Path) -> dict[str, Any]:
    return {k: v for k, v in native.items() if k != "pad_token_ids"} | {"tokenizers": tokenizers}


@pytest.mark.parametrize("role", impl.ROLES)
def test_public_metadata_identity_and_expected_ids(tokenizers: Path, role: Any) -> None:
    result = metadata.authenticate(tokenizers / f"{role}_tokenizer_config.json", role)
    assert result["pad_token_id"] == 151643 and result["eos_token_id"] == 151645
    assert result["metadata_authenticated"] and not result["native_tokenizer_executed"]
    pin = json.loads((ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json").read_text())
    scan = json.loads(
        (ROOT / "experiments/manifests/phase5_agent_mount_v1_scan01.json").read_text()
    )
    for inventory in (pin, scan):
        entry = next(r for r in inventory["files"] if r["name"] == "tokenizer_config.json")
        assert entry["sha256"] == metadata.SHA256 and entry["size"] == metadata.SIZE
    raw = (ROOT / "docs/evaluation/qwen7b_upstream_inventory_v1.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == INVENTORY_SHA256
    entry = next(r for r in json.loads(raw)["files"] if r["name"] == "tokenizer_config.json")
    assert entry["git_blob_sha1"] == metadata.BLOB


@pytest.mark.parametrize("case", ["byte", "short", "long", "newline", "directory", "link"])
def test_metadata_rejects_unauthenticated_bytes(tokenizers: Path, case: str) -> None:
    path = tokenizers / "agent_tokenizer_config.json"
    raw = path.read_bytes()
    if case == "byte":
        path.write_bytes(raw.replace(b"151643", b"151642"))
    elif case == "short":
        path.write_bytes(raw[:-1])
    elif case == "long":
        path.write_bytes(raw + b" " * 100000)
    elif case == "newline":
        path.write_bytes(raw + b"\n")
    else:
        path.unlink()
        if case == "directory":
            path.mkdir()
        else:
            path.symlink_to(tokenizers / "guard_tokenizer_config.json")
    with pytest.raises(ValueError):
        metadata.authenticate(path, "agent")


def test_joined_repeatable_readonly(inputs: dict[str, Any]) -> None:
    result = impl.audit(**inputs)
    assert result == impl.audit(**inputs)
    assert result["tokenizer_metadata_authenticated"] and result["tokenizer_ids_bound_to_policy"]
    assert not result["joined"]["tokenizer_metadata_authenticated"]  # frozen inner scope
    for key in (
        "source_authenticated",
        "native_validated",
        "phase5_accepted",
        "native_tokenizer_executed",
    ):
        assert result[key] is False
    assert len(result["joined"]["calls"]) == 6
    assert len(result["input_sha256"]["tokenizers"]) == 2


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "extra",
        "empty_dir",
        "nested",
        "root_link",
        "pad_policy",
        "agent_admission",
        "guard_pin",
        "source",
    ],
)
def test_join_rejects_mutations(inputs: dict[str, Any], case: str, tmp_path: Path) -> None:
    root = inputs["tokenizers"]
    if case == "missing":
        (root / "guard_tokenizer_config.json").unlink()
    elif case == "extra":
        (root / "extra.json").write_text("{}")
    elif case == "empty_dir":
        (root / "empty").mkdir()
    elif case == "nested":
        inputs["tokenizers"] = inputs["publishers"]
    elif case == "root_link":
        link = tmp_path / "linked"
        link.symlink_to(root, target_is_directory=True)
        inputs["tokenizers"] = link
    elif case in ("pad_policy", "agent_admission"):
        path = inputs["probe"] / "agent_hf_metrics.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if case == "agent_admission":
            entry = next(
                r
                for r in rows[0]["runtime_admission"]["files"]
                if r["name"] == "tokenizer_config.json"
            )
            entry["sha256"] = "0" * 64
        else:
            # The observer sidecar is independently checked against derived IDs.
            path = next((inputs["policy"] / "agent").rglob("resolved.json"))
            row = json.loads(path.read_text())
            text = json.dumps(row)
            assert "151643" in text
            path.write_text(text.replace("151643", "151642"))
        if case == "agent_admission":
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    elif case == "guard_pin":
        data = inputs["pin"].model_dump()
        next(r for r in data["files"] if r["name"] == "tokenizer_config.json")["size"] += 1
        inputs["pin"] = type(inputs["pin"]).model_validate(data)
    else:
        inputs["commit"] = "b" * 40
    with pytest.raises((ValueError, KeyError)):
        impl.audit(**inputs)


@pytest.mark.parametrize("case", ["bytes", "empty_directory"])
def test_inputs_changing_during_join_rejected(
    inputs: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    original = impl.audit_native

    def changed(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        if case == "bytes":
            with (inputs["tokenizers"] / "guard_tokenizer_config.json").open("ab") as stream:
                stream.write(b"\n")
        else:
            (inputs["tokenizers"] / "empty").mkdir()
        return result

    monkeypatch.setattr(impl, "audit_native", changed)
    with pytest.raises(ValueError, match="changed"):
        impl.audit(**inputs)


def test_cli_fresh_receipt_and_readonly(inputs: dict[str, Any], tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    command = [sys.executable, str(ROOT / "scripts/audit_phase5_ordinary_tokenizer.py")]
    for name in ("probe", "policy", "attention", "publishers", "tokenizers"):
        command.extend(["--" + name, str(inputs[name])])
    command.extend(
        [
            "--snapshot",
            str(ROOT / "tests/fixtures/ordinary_pair_guard_snapshot.json"),
            "--source-commit",
            inputs["commit"],
            "--output",
            str(output),
        ]
    )
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    result = subprocess.run(command, env=env, capture_output=True, timeout=30)  # noqa: S603
    assert result.returncode == 0, result.stderr.decode()
    assert json.loads(output.read_text())["tokenizer_metadata_authenticated"]
    before = output.read_bytes()
    again = subprocess.run(command, env=env, capture_output=True, timeout=30)  # noqa: S603
    assert again.returncode != 0 and output.read_bytes() == before


def test_metadata_import_does_not_load_native_libraries() -> None:
    code = (
        "import sys; import react_agent.validation.ordinary_tokenizer_audit_v1; "
        "assert not {'torch', 'transformers', 'tokenizers'} & sys.modules.keys()"
    )
    subprocess.run(  # noqa: S603 - fixed import-only code
        [sys.executable, "-c", code],
        check=True,
        timeout=30,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
    )


@pytest.mark.parametrize("case", ["valid", "corrupt", "nested_output", "existing_output"])
def test_metadata_collector(tokenizers: Path, tmp_path: Path, case: str) -> None:
    models = {}
    for role in impl.ROLES:
        models[role] = tmp_path / (role + "_model")
        models[role].mkdir()
        (models[role] / "tokenizer_config.json").write_bytes(
            (tokenizers / f"{role}_tokenizer_config.json").read_bytes()
        )
        # Unknown files, including anything named like weights, are not collected.
        (models[role] / "model.safetensors").write_text("never read as model weights")
    output = tmp_path / "collected"
    if case == "corrupt":
        (models["guard"] / "tokenizer_config.json").write_text("{}")
    elif case == "nested_output":
        output = models["agent"] / "output"
    elif case == "existing_output":
        output.mkdir()
    before = {role: impl.inventory(path) for role, path in models.items()}
    command = [sys.executable, str(ROOT / "scripts/collect_phase5_tokenizer_metadata.py")]
    for role, path in models.items():
        command.extend([f"--{role}-path", str(path)])
    command.extend(["--output", str(output)])
    result = subprocess.run(  # noqa: S603 - fixed metadata-only collector
        command,
        capture_output=True,
        timeout=30,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")),
    )
    assert {role: impl.inventory(path) for role, path in models.items()} == before
    if case == "valid":
        assert result.returncode == 0, result.stderr.decode()
        assert impl.inventory(output) == impl.inventory(tokenizers)
    else:
        assert result.returncode != 0
        assert not output.exists() or list(output.iterdir()) == []
