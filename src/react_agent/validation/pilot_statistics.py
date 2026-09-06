"""Descriptive statistics and group bootstrap for a small paired Dev pilot."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Sequence
from statistics import mean, median, stdev


def percentile(values: Sequence[float], quantile: float) -> float:
    if not values or not 0 <= quantile <= 1:
        raise ValueError("nonempty values and quantile in [0,1] required")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def distribution(values: Sequence[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("finite nonnegative measurements required")
    return {
        "n": len(values),
        "mean": mean(values),
        "median": median(values),
        "sample_sd": stdev(values) if len(values) > 1 else 0.0,
        "p95": percentile(values, 0.95),
        "total": sum(values),
    }


def cluster_mean_interval(
    values: Sequence[float],
    groups: Sequence[str],
    *,
    draws: int = 5000,
    seed: int = 2026,
) -> tuple[float, float]:
    """Resample semantic groups together; paired differences use the same function."""
    if len(values) != len(groups) or not values or draws < 100:
        raise ValueError("aligned nonempty observations and >=100 bootstrap draws required")
    clusters: dict[str, list[float]] = defaultdict(list)
    for value, group in zip(values, groups, strict=True):
        if not math.isfinite(value):
            raise ValueError("nonfinite observation")
        clusters[group].append(value)
    keys = sorted(clusters)
    rng = random.Random(seed)  # noqa: S311 - reproducible statistical resampling
    bootstrap = []
    for _ in range(draws):
        sampled = rng.choices(keys, k=len(keys))
        observation = [v for group in sampled for v in clusters[group]]
        bootstrap.append(mean(observation))
    return percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)
