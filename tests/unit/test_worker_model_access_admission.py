"""Reject gated or incomplete model inputs before consuming Kaggle GPU quota."""
import importlib
import subprocess
from pathlib import Path

import pytest

SOURCE = "metaresearch/llama-3.2/transformers/3b-instruct/1"


@pytest.fixture
def deployment(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("deploy_structured_pair_v3")


@pytest.mark.parametrize("status,listing,error", [
    (1, "", "access unavailable"),
    (0, "name,size\nconfig.json,10\n", "listing incomplete"),
    (0, "name,size\nmodel.safetensors,10\n", "listing incomplete"),
    (0, "", "listing incomplete"),
])
def test_unavailable_or_incomplete_model_blocks(deployment, monkeypatch, status, listing, error):
    calls = []
    def fake(role, args):
        calls.append((role, args))
        return subprocess.CompletedProcess(args, status, listing, "private server diagnostics")
    monkeypatch.setattr(deployment, "kaggle", fake)
    with pytest.raises(ValueError, match=error) as exc:
        deployment.verify_model_access("guard", SOURCE)
    assert "private server diagnostics" not in str(exc.value)
    assert len(calls) == 1 and calls[0][1][:4] == ["models", "variations", "versions", "files"]


def test_exact_version_file_access_passes(deployment, monkeypatch):
    def fake(role, args):
        assert role == "guard" and args[4] == SOURCE
        return subprocess.CompletedProcess(
            args, 0, "name,size\nconfig.json,10\nmodel.safetensors,100\n", "")
    monkeypatch.setattr(deployment, "kaggle", fake)
    deployment.verify_model_access("guard", SOURCE)


def test_unpinned_handle_rejected_before_network(deployment, monkeypatch):
    def unexpected(*args):
        raise AssertionError("must not access network")
    monkeypatch.setattr(deployment, "kaggle", unexpected)
    with pytest.raises(ValueError, match="exact model version"):
        deployment.verify_model_access("guard", SOURCE.rsplit("/", 1)[0])
