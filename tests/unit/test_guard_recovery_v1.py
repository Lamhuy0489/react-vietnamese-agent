"""Fixed sample/tolerance checks are not evidence of measured GPU recovery."""

import pytest

from react_agent.llm.guard_cancellation_v1 import SAMPLES, TOLERANCE, recovery_valid


@pytest.mark.parametrize(
    "delta,valid",
    [
        (0, True),
        (TOLERANCE, True),
        (-TOLERANCE, True),
        (TOLERANCE + 1, False),
        (-TOLERANCE - 1, False),
    ],
)
def test_tolerance(delta: int, valid: bool) -> None:
    before = {"free_bytes": 10 * 1024**3, "total_bytes": 16 * 1024**3}
    samples = [{**before, "free_bytes": before["free_bytes"] + delta} for _ in range(SAMPLES)]
    assert recovery_valid(before, samples) is valid


@pytest.mark.parametrize("change", ["missing", "extra", "late_drift", "total"])
def test_all_samples_and_late_stability(change: str) -> None:
    before = {"free_bytes": 10 * 1024**3, "total_bytes": 16 * 1024**3}
    samples = [dict(before) for _ in range(SAMPLES)]
    if change == "missing":
        samples.pop()
    elif change == "extra":
        samples.append(dict(before))
    elif change == "total":
        samples[-1]["total_bytes"] += 1
    else:
        samples[-2]["free_bytes"] -= TOLERANCE + 1
    assert not recovery_valid(before, samples)


def test_early_sample_not_cherry_picked() -> None:
    before = {"free_bytes": 10 * 1024**3, "total_bytes": 16 * 1024**3}
    samples = [dict(before) for _ in range(SAMPLES)]
    samples[0]["free_bytes"] -= TOLERANCE + 1
    assert recovery_valid(before, samples)
