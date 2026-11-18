#!/usr/bin/env python3
"""Test-4 reference column (Gemini 3 Flash): ``run_v3_api_v4.py`` with one widened check.

The pinned runner refuses any (model, configuration) pair outside the ``final_config_v5``
matrix. The reference column planned in the v3 design (section 5, "Gemini 3 Flash làm cột
tham khảo") is not in that matrix, so this wrapper allows exactly the pairs in ``REFERENCE``
and nothing else; every other check of the pinned runner (manifest verification, sealed
release, all branches, pinned adaptive file, no ``--max-new-tokens``) runs unchanged, and the
pinned files are not edited. Results are a separate column: not pooled with the three open
backbones and not part of H1-H4 (decision log 2026-11-18, declared before the run).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_v3_api_v4 as runner  # noqa: E402

from react_agent.evaluation import final_config_v5  # noqa: E402

REFERENCE: dict[str, frozenset[str]] = {
    "gemini3_flash": frozenset({"A0", "P2", "PRG", "D2P2", "V3P2"}),
}

_pinned_allowed = final_config_v5.allowed


def allowed(manifest: dict[str, Any], model_key: str, config: str) -> bool:
    if _pinned_allowed(manifest, model_key, config):
        return True
    return config in REFERENCE.get(model_key, frozenset())


final_config_v5.allowed = allowed  # the module object the pinned runner calls

if __name__ == "__main__":
    raise SystemExit(runner.main())
