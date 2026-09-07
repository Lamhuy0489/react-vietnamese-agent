import smtplib
import socket
from pathlib import Path

import pytest

from react_agent.foundation.dev_validation import validate_dev

ROOT = Path(__file__).resolve().parents[2]


def test_all_dev_normalization_without_test_payload_or_gt_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Path.read_text

    def guarded(path: Path, *args: object, **kwargs: object) -> str:
        relative = path.relative_to(ROOT).as_posix()
        assert "ground_truth" not in relative and "/pool/" not in relative
        assert path.name not in {
            "test.jsonl",
            "test_attack.jsonl",
            "test_benign.jsonl",
            "reference_traces.jsonl.gz",
        }
        assert "private" not in path.parts or path.name == "robustness_canonical_ids.json"
        return original(path, *args, **kwargs)

    def deny(*args: object, **kwargs: object) -> None:
        raise AssertionError("primitive QA cannot access network")

    monkeypatch.setattr(Path, "read_text", guarded)
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, deny)
    monkeypatch.setattr(smtplib, "SMTP", deny)
    result = validate_dev(ROOT)
    assert result["valid"] and not result["phase4_accepted"]
    assert result["profile_checks"] == 1650
    assert result["clean_dev_instructions"] == 150 and result["adversarial_dev_payloads"] == 400
    assert result["test_payloads_parsed_by_this_validator"] == 0
    assert result["prerequisites"]["robustness_ids_presealed"] == 50
    assert not result["private_ground_truth_loaded"]
    assert result["broker_runs"] == result["model_runs"] == 0
