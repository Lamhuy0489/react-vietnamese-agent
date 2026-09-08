"""Publisher/content binding on synthetic bytes; no model downloads in tests."""

import hashlib
import json
from pathlib import Path

import pytest

from react_agent.llm.guard_acquisition_v1 import (
    UpstreamFile,
    UpstreamSnapshot,
    verify_acquisition,
    verify_upstream_file,
)
from react_agent.llm.guard_snapshot_v1 import CANDIDATE_REVISION, MODEL_ID, REQUIRED


@pytest.fixture
def acquired(tmp_path: Path) -> tuple[Path, UpstreamSnapshot]:
    root = tmp_path / "snapshot"
    root.mkdir()
    entries = []
    for name in sorted(REQUIRED | {"LICENSE"}):
        raw = b"synthetic fixture"
        if name == "config.json":
            raw = json.dumps(
                {"model_type": "qwen2", "architectures": ["Qwen2ForCausalLM"]}
            ).encode()
        (root / name).write_bytes(raw)
        digest = hashlib.sha1(
            f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False
        ).hexdigest()
        entries.append(
            UpstreamFile(
                name=name,
                size=len(raw),
                **(
                    {"sha256": hashlib.sha256(raw).hexdigest()}
                    if name == "model.safetensors"
                    else {"git_blob_sha1": digest}
                ),
            )
        )
    return root, UpstreamSnapshot(
        model_id=MODEL_ID,
        revision=CANDIDATE_REVISION,
        access_date="synthetic",
        metadata_url=f"https://huggingface.co/api/models/{MODEL_ID}/revision/{CANDIDATE_REVISION}?blobs=true",
        files=tuple(entries),
    )


def test_verified_snapshot(acquired: tuple[Path, UpstreamSnapshot]) -> None:
    root, upstream = acquired
    pin = verify_acquisition(root, upstream)
    assert pin.upstream_revision == CANDIDATE_REVISION
    assert len(pin.files) == len(upstream.files)
    for entry in upstream.files:
        assert upstream.url(entry).startswith(f"https://huggingface.co/{MODEL_ID}/resolve/")


@pytest.mark.parametrize("name", sorted(REQUIRED | {"LICENSE"}))
def test_tampered_bytes(acquired: tuple[Path, UpstreamSnapshot], name: str) -> None:
    root, upstream = acquired
    raw = (root / name).read_bytes()
    (root / name).write_bytes(b"X" * len(raw))
    with pytest.raises(ValueError):
        verify_acquisition(root, upstream)


@pytest.mark.parametrize("change", ["short", "extra", "missing", "link"])
def test_bad_download(acquired: tuple[Path, UpstreamSnapshot], change: str, tmp_path: Path) -> None:
    root, upstream = acquired
    if change == "short":
        (root / "model.safetensors").write_bytes(b"short")
    elif change == "extra":
        (root / "unlisted.json").write_text("extra")
    else:
        path = root / "model.safetensors"
        moved = tmp_path / "moved"
        path.rename(moved)
        if change == "link":
            path.symlink_to(moved)
    with pytest.raises(ValueError):
        verify_acquisition(root, upstream)


@pytest.mark.parametrize("name", ["../model.safetensors", "/absolute/file", "evil.py"])
def test_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError):
        UpstreamFile(name=name, size=1, sha256="a" * 64)


def test_git_hash_is_not_plain_file_sha1(acquired: tuple[Path, UpstreamSnapshot]) -> None:
    root, upstream = acquired
    entry = next(f for f in upstream.files if f.name == "config.json")
    wrong = UpstreamFile(
        name=entry.name,
        size=entry.size,
        git_blob_sha1=hashlib.sha1(
            (root / entry.name).read_bytes(),
            usedforsecurity=False,
        ).hexdigest(),
    )
    with pytest.raises(ValueError, match="Git blob"):
        verify_upstream_file(root / entry.name, wrong)


@pytest.mark.parametrize(
    "hashes",
    [
        {},
        {"sha256": "a" * 64, "git_blob_sha1": "b" * 40},
        {"git_blob_sha1": "b" * 40},
    ],
)
def test_weights_require_one_sha256(hashes: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        UpstreamFile(name="model.safetensors", size=1, **hashes)


@pytest.mark.parametrize("condition", ["duplicate", "no_license", "mutable", "other_url"])
def test_bad_upstream_manifest(acquired: tuple[Path, UpstreamSnapshot], condition: str) -> None:
    _, upstream = acquired
    raw = upstream.model_dump()
    if condition == "duplicate":
        raw["files"] += raw["files"][:1]
    if condition == "no_license":
        raw["files"] = tuple(f for f in raw["files"] if f["name"] != "LICENSE")
    if condition == "mutable":
        raw["revision"] = "main"
    if condition == "other_url":
        raw["metadata_url"] = "https://example.invalid/model"
    with pytest.raises(ValueError):
        UpstreamSnapshot.model_validate(raw)


def test_recorded_publisher_pin_is_well_formed() -> None:
    path = Path(__file__).resolve().parents[2] / "configs/guard_hf_v1/qwen_1_5b_upstream.json"
    pin = UpstreamSnapshot.model_validate_json(path.read_text())
    assert len(pin.files) == 10
    assert pin.revision == CANDIDATE_REVISION
    assert next(f.size for f in pin.files if f.name == "model.safetensors") == 3087467144
