#!/usr/bin/env python3
"""Test-4 supplementary baselines: ``run_v3_api_v4.py`` with one widened check.

The pinned runner refuses any (model, configuration) pair outside the ``final_config_v5``
matrix. The supplementary baselines R1 (PhraseRules), D2 (BG-Rules), P1 (Spotlight),
MEL (MELON*) and G1 (Prompt Guard 2) ran only on the old Dev; to put every table on the same
data the owner added them on Dev v4.1 and Test-4 for the three open backbones (decision log
2026-11-19, declared before the run). This wrapper allows exactly the pairs in
``SUPPLEMENTARY``; every other check of the pinned runner runs unchanged and no pinned file
is edited. The results are descriptive and outside H1-H4.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_v3_api_v4 as runner  # noqa: E402

from react_agent.evaluation import final_config_v5  # noqa: E402

_BASELINES = frozenset({"R1", "D2", "P1", "MEL", "G1"})
SUPPLEMENTARY: dict[str, frozenset[str]] = {
    "qwen35_9b": _BASELINES,
    "gemma4_12b": _BASELINES,
    "llama31_8b": _BASELINES,
}

_pinned_allowed = final_config_v5.allowed


def allowed(manifest: dict[str, Any], model_key: str, config: str) -> bool:
    if _pinned_allowed(manifest, model_key, config):
        return True
    return config in SUPPLEMENTARY.get(model_key, frozenset())


final_config_v5.allowed = allowed  # the module object the pinned runner calls

if __name__ == "__main__":
    raise SystemExit(runner.main())
