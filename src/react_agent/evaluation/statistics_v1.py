"""Statistics frozen in docs/metrics_spec.md: family bootstrap CI and exact McNemar."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from react_agent.validation.pilot_statistics import cluster_mean_interval

DRAWS, SEED = 10_000, 42


def rate_with_ci(values: Sequence[bool], families: Sequence[str]) -> dict[str, Any]:
    """Share of True with a 95% percentile bootstrap CI that resamples families."""
    numbers = [1.0 if value else 0.0 for value in values]
    low, high = cluster_mean_interval(numbers, families, draws=DRAWS, seed=SEED)
    return {"n": len(numbers), "k": int(sum(numbers)), "rate": sum(numbers) / len(numbers),
            "ci95": [low, high]}


def mcnemar_exact(before: Sequence[bool], after: Sequence[bool]) -> dict[str, float | int]:
    """Two-sided exact McNemar on paired outcomes; b = True→False, c = False→True."""
    if len(before) != len(after) or not before:
        raise ValueError("aligned nonempty paired outcomes required")
    b = sum(1 for x, y in zip(before, after, strict=True) if x and not y)
    c = sum(1 for x, y in zip(before, after, strict=True) if y and not x)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p_value": 1.0}
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return {"b": b, "c": c, "p_value": min(1.0, 2 * tail)}
