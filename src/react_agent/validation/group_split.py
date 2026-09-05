"""Exact quota assignment with indivisible cross-category semantic groups."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from functools import cache

from react_agent.schemas.clean_task import CleanPublicTask


def assign_groups(
    tasks: list[CleanPublicTask], dev_quotas: dict[str, int], *, seed: int
) -> dict[str, str]:
    categories = tuple(sorted(dev_quotas))
    groups: dict[str, list[CleanPublicTask]] = defaultdict(list)
    for task in tasks:
        if task.category not in dev_quotas:
            raise ValueError(f"unknown category: {task.category}")
        groups[task.instance_group_id].append(task)
    ordered = sorted(groups)
    random.Random(seed).shuffle(ordered)  # noqa: S311 - deterministic sampling
    coupled = [key for key in ordered if len(groups[key]) > 1]
    singles = [key for key in ordered if len(groups[key]) == 1]
    capacity: Counter[str] = Counter(groups[key][0].category for key in singles)
    vectors: list[Counter[str]] = [
        Counter(task.category for task in groups[key]) for key in coupled
    ]
    visited = 0

    @cache
    def solve(index: int, remaining: tuple[int, ...]) -> tuple[bool, ...] | None:
        nonlocal visited
        visited += 1
        if visited > 200_000:
            raise ValueError("group assignment search limit exceeded; revise the pre-split pool")
        if any(value < 0 for value in remaining):
            return None
        if index == len(coupled):
            return (
                ()
                if all(n <= capacity[c] for c, n in zip(categories, remaining, strict=True))
                else None
            )
        vector = vectors[index]
        take = solve(
            index + 1, tuple(n - vector[c] for c, n in zip(categories, remaining, strict=True))
        )
        if take is not None:
            return (True, *take)
        leave = solve(index + 1, remaining)
        return None if leave is None else (False, *leave)

    choices = solve(0, tuple(dev_quotas[category] for category in categories))
    if choices is None:
        raise ValueError("no group-wise assignment satisfies the exact category quotas")
    assignments: dict[str, str] = {}
    used: Counter[str] = Counter()
    for key, use_dev in zip(coupled, choices, strict=True):
        for task in groups[key]:
            assignments[task.task_id] = "dev" if use_dev else "test"
            if use_dev:
                used[task.category] += 1
    for key in singles:
        task = groups[key][0]
        use_dev = used[task.category] < dev_quotas[task.category]
        assignments[task.task_id] = "dev" if use_dev else "test"
        if use_dev:
            used[task.category] += 1
    if used != Counter(dev_quotas):
        raise ValueError("assignment did not satisfy Dev quotas")
    return assignments
