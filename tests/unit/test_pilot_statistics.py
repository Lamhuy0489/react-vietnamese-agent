import pytest

from react_agent.validation.pilot_statistics import cluster_mean_interval, distribution, percentile


def test_latency_statistics_known_values_and_invalid_input() -> None:
    summary = distribution([1.0, 2.0, 3.0, 4.0])
    assert summary["mean"] == 2.5
    assert summary["median"] == 2.5
    assert summary["p95"] == pytest.approx(3.85)
    assert percentile([9.0], 0.95) == 9.0
    with pytest.raises(ValueError):
        distribution([float("nan")])


def test_semantically_paired_tasks_are_resampled_together() -> None:
    # Treating these rows independently would produce a spurious nonzero interval.
    assert cluster_mean_interval([0, 1, 0, 1], ["a", "a", "b", "b"]) == (0.5, 0.5)
    assert cluster_mean_interval([0, 0], ["a", "b"]) == (0.0, 0.0)
    left = cluster_mean_interval([-1, 0, 1], ["a", "b", "c"])
    assert left == cluster_mean_interval([-1, 0, 1], ["a", "b", "c"])
    with pytest.raises(ValueError):
        cluster_mean_interval([1], [])
