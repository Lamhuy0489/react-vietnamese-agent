#!/usr/bin/env python3
"""Verify the repository scaffold and secret-exclusion guardrails."""

from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parents[1]
GIT = which("git")

REQUIRED_PATHS = (
    "AGENTS.md",
    "ARCHITECTURE.md",
    "README.md",
    "pyproject.toml",
    "docs/project/research_contract.md",
    "docs/project/phase_map.md",
    "docs/project/invariants.md",
    ".agents/skills/react-vn-capstone/SKILL.md",
    ".agents/skills/benchmark-authoring/SKILL.md",
    ".agents/skills/experiment-repro/SKILL.md",
    ".agents/skills/research-evidence/SKILL.md",
)

SENSITIVE_RELATIVE_PATHS = (
    "credential kaggle/kaggle.json",
    "credential kaggle/kaggle1.json",
    "credential kaggle/kaggle2.json",
    "credential kaggle/kaggle3.json",
)


def git_is_initialized() -> bool:
    if GIT is None:
        return False
    result = subprocess.run(  # noqa: S603 - fixed executable and arguments
        [GIT, "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def ignored_by_git(path: str) -> bool:
    if GIT is None:
        return False
    result = subprocess.run(  # noqa: S603 - fixed executable; path is passed without a shell
        [GIT, "check-ignore", "--quiet", "--", path],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).is_file():
            failures.append(f"missing required file: {relative_path}")

    if git_is_initialized():
        for relative_path in SENSITIVE_RELATIVE_PATHS:
            if (ROOT / relative_path).exists() and not ignored_by_git(relative_path):
                failures.append(f"credential is not ignored by Git: {relative_path}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: repository setup and credential guardrails are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
