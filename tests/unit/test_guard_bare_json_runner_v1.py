"""CLI boundary tests for candidate backend/condition admission."""

from pathlib import Path

import pytest

from react_agent.llm.guard_bare_json_probe_v1 import fixed_identity


def test_hf_injection_conditions_are_rejected() -> None:
    for condition in ("fenced", "trailing_comma"):
        with pytest.raises(ValueError, match="injection"):
            fixed_identity("hf", condition)


def test_candidate_has_distinct_prompt_identity() -> None:
    identity = fixed_identity("stub", "valid")
    assert identity["protocol"] == "guard_bare_json_probe_v1"
    assert identity["guard_prompt"]["version"] == "guard_prompt_bare_json_v1"
    assert identity["guard_prompt"]["sha256"] != identity["guard_prompt"]["baseline_sha256"]
    assert Path("scripts/run_phase5_guard_bare_json_probe_v1.py").is_file()
