"""Host identity/environment validation only; never imports actual model libraries."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from react_agent.llm.guard_snapshot_v1 import (
    CANDIDATE_REVISION,
    REQUIRED,
    GuardSnapshot,
    SnapshotFile,
)
from react_agent.llm.model_pair_hf_v1 import AGENT_CONTENT, hf_pair, verify_gpu_environment

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case", ["valid", "torch", "cuda", "transformers"])
def test_exact_environment(monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    torch = SimpleNamespace(__version__="2.10.0+cu128", version=SimpleNamespace(cuda="12.8"))
    transformers = SimpleNamespace(__version__="5.5.0")
    if case == "torch":
        torch.__version__ = "other"
    elif case == "cuda":
        torch.version.cuda = "other"
    elif case == "transformers":
        transformers.__version__ = "other"
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    if case == "valid":
        assert verify_gpu_environment()["torch"] == torch.__version__
    else:
        with pytest.raises(ValueError):
            verify_gpu_environment()


def test_hf_factory_is_lazy_and_identity_bound(tmp_path: Path) -> None:
    prior = json.loads(
        (ROOT / "experiments/manifests/phase5_agent_loader_v1_validation01.json").read_text()
    )
    assert prior["saved_scan_admission"]["content_sha256"] == AGENT_CONTENT
    pin = GuardSnapshot(
        upstream_revision=CANDIDATE_REVISION,
        files=tuple(SnapshotFile(name=n, size=1, sha256="a" * 64) for n in sorted(REQUIRED)),
    )
    instance = hf_pair(
        tmp_path / "agent", tmp_path / "inventory", tmp_path / "guard", pin, tmp_path
    )
    assert instance.state == "NEW" and instance.config.agent.model_revision.endswith(AGENT_CONTENT)
    instance.close()
