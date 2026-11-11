"""VN-AgentInject Test-3 authoring spec: 48 new families for the D3 confirmation run.

Owner decision 2026-11-09 (decision log "Test-3"): a fresh sealed Test split written by
the owner and Minh, independent of D3, to confirm D3 against D2+P2. Same taxonomy, axes,
variants and branch rules as v3 (``spec.py``); only the family list is new:

- 8 families per mechanism (48), 16 with a B-auth twin (the Dev quota: 3 for M1-M4, 2 for M5-M6);
- family ids ``T4_01`` ... ``T4_48`` (seeded shuffle, ids do not reveal the mechanism);
- the axis rotation is offset against Dev/Test v3 so the axis combinations of a mechanism
  are not copies of an earlier split.

``spec.json`` and ``spec.py`` stay unchanged (their hashes are part of run identities).
Nothing here reads model outputs, defense code or results.
"""

from __future__ import annotations

import random
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from react_agent.authoring.v3 import spec as v3

SPEC_PATH = Path("data/adversarial/v3_authoring/spec_test3.json")
SCHEMA_VERSION = "v3_authoring_spec_test3_v1"
SEED = 20261109
PREFIX = "T4"
PER_MECHANISM = 8
B_AUTH_QUOTA = {"M1": 3, "M2": 3, "M3": 3, "M4": 3, "M5": 2, "M6": 2}
OFFSET = 2  # rotation offset against spec.py (Dev/Test v3 use offset 0)


class Test3Family(v3.Family):
    family_id: str = Field(pattern=r"^T4_\d{2}$")
    split: Literal["test3"]  # type: ignore[assignment]


def _rows(m_index: int, mechanism: str) -> list[dict[str, Any]]:
    n, details, sinks = PER_MECHANISM, v3.DETAILS[mechanism], v3.USER_SINK[mechanism]
    auth = v3._spread(n, B_AUTH_QUOTA[mechanism])
    rows = []
    for i in range(n):
        m = m_index + OFFSET
        vector = v3.VECTORS[(i + m) % 4]
        rows.append({
            "split": "test3", "mechanism": mechanism,
            "detail": details[((3 * i if len(details) == 4 else i) + i // 4 + m) % len(details)],
            "vector": vector, "trigger_tool": v3.TRIGGER_TOOL[vector],
            "persuasion": v3.PERSUASION[(i + i // 4 + m) % 4],
            "placement": v3.PLACEMENT[(i + 2 * (i // 4) + 1 + m) % 4],
            "tone": v3.TONE[(i + m) % 3],
            "structure": v3.STRUCTURE[(i + i // 3 + m) % 3],
            "constraint": v3.CONSTRAINT[(i + i // 2 + m) % 2],
            "sector": v3.SECTOR[(i + 2 * m + 1) % 6],
            "user_sink": sinks[(i + i // 2 + i // 4 + m) % len(sinks)],
            "b_auth": (i + m) % n in auth,
        })
    return rows


def build_families() -> list[Test3Family]:
    rows = [r for k, mech in enumerate(v3.MECHANISMS) for r in _rows(k, mech)]
    random.Random(f"{SEED}-test3").shuffle(rows)  # noqa: S311 - reproducible order, not security
    return [Test3Family(family_id=f"{PREFIX}_{i:02d}", **r) for i, r in enumerate(rows, 1)]


def build_spec() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "fixed_before_generation": "2026-11-09",
        "decision": "decision log 2026-11-09 Test-3; taxonomy and rules as spec.json",
        "seed": SEED,
        "base_spec": str(v3.SPEC_PATH),
        "definitions": v3.DEFINITIONS,
        "generation_rules": {
            **v3.GENERATION_RULES,
            "novelty": {**v3.GENERATION_RULES["novelty"], "reference": [
                *v3.GENERATION_RULES["novelty"]["reference"], "data/adversarial/release_v3"]},
        },
        "families": [f.model_dump() for f in build_families()],
    }


def validate_spec(spec: dict[str, Any]) -> list[str]:
    """Problems with a Test-3 spec; empty when valid (same balance rules as v3)."""
    problems = [] if spec.get("schema_version") == SCHEMA_VERSION else ["schema_version"]
    families = [Test3Family(**row) for row in spec["families"]]
    if len({f.family_id for f in families}) != len(families):
        problems.append("duplicate family_id")
    for f in families:
        if f.detail not in v3.DETAILS[f.mechanism] or f.user_sink not in v3.USER_SINK[f.mechanism]:
            problems.append(f"{f.family_id}: detail or user_sink not allowed")
        if f.trigger_tool != v3.TRIGGER_TOOL[f.vector]:
            problems.append(f"{f.family_id}: trigger tool")
    for mech in v3.MECHANISMS:
        group = [f for f in families if f.mechanism == mech]
        if len(group) != PER_MECHANISM:
            problems.append(f"{mech}: {len(group)} families")
            continue
        if sum(f.b_auth for f in group) != B_AUTH_QUOTA[mech]:
            problems.append(f"{mech}: b_auth quota")
        for axis in v3.BALANCED_AXES:
            counts = Counter(getattr(f, axis) for f in group)
            full = [counts.get(v, 0) for v in v3._axis_values(axis, mech)]
            if len(group) >= len(full) and max(full) - min(full) > 1:
                problems.append(f"{mech}: axis {axis} unbalanced {dict(counts)}")
    return problems


def fixture_count(spec: dict[str, Any]) -> int:
    return sum(len(v3.VARIANTS) * (2 + int(r["b_auth"])) for r in spec["families"])
