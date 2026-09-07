from pathlib import Path

import pytest

from react_agent.adversarial_release import load_split
from react_agent.authoring.release_v2 import verify_seal

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/adversarial/release_v2"


@pytest.mark.skipif(not (RELEASE / "seal.json").exists(), reason="release not yet sealed")
def test_sealed_release_integrity_without_parsing_test() -> None:
    assert verify_seal(ROOT, RELEASE) == {
        "valid": True,
        "mode": "sealed_read_only",
        "phase3_accepted": True,
        "test_sealed": True,
        "variants": 700,
    }


@pytest.mark.skipif(not (RELEASE / "seal.json").exists(), reason="release not yet sealed")
def test_sealed_dev_loading_opens_only_dev_and_seal(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.open

    def guard(path: Path, *args: object, **kwargs: object) -> object:
        assert path.parent == RELEASE
        assert path.name in {"seal.json", "dev_attack.jsonl", "dev_benign.jsonl"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    rows = load_split(RELEASE)
    assert len(rows) == 400 and {r.split for r in rows} == {"dev"}
    with pytest.raises(ValueError, match="held-out"):
        load_split(RELEASE, "test")
