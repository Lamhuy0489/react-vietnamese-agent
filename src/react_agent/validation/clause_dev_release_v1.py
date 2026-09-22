"""Verify exact public worker bytes against an externally pinned package record."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.validation.context_stress_audit_v1 import equal

PROTOCOL = "clause_dev32_source_v1"


def digest(path: Path) -> str:
    no_links(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or path.as_posix() != name
        or ".." in path.parts
        or "\\" in name
        or ":" in name
        or "credential" in name.casefold()
        or any(p.casefold() in {"private", "pool", "reviews", "tests"} for p in path.parts)
        or any(p.casefold().startswith("test") for p in path.parts)
    ):
        raise ValueError("public relative source path required")
    return name


def admit(
    project: Path, manifest: Path, expected_sha256: str, commit: str, *, native: bool
) -> dict[str, Any]:
    """The launcher/release audit authenticates the expected hash; never self-certify."""
    no_links(project)
    equal(digest(manifest), expected_sha256, "external source manifest pin")
    value: dict[str, Any] = json.loads(manifest.read_text())
    equal(
        sorted(value),
        sorted(
            {
                "protocol",
                "source_mode",
                "source_commit",
                "git_base_commit",
                "source_sha256",
                "archive_sha256",
            }
        ),
        "source manifest fields",
    )
    equal(value["protocol"], PROTOCOL, "source protocol")
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("exact source commit required")
    equal(value["git_base_commit"], commit, "source base")
    mode = value["source_mode"]
    if mode not in {"working_tree", "committed"} or (native and mode != "committed"):
        raise ValueError("native requires committed source; development is CPU only")
    equal(value["source_commit"], commit if mode == "committed" else None, "source commit")
    if re.fullmatch(r"[0-9a-f]{64}", value["archive_sha256"]) is None:
        raise ValueError("archive pin required")
    files = value["source_sha256"]
    if not isinstance(files, dict) or not files:
        raise ValueError("nonempty source inventory required")
    for name, expected in files.items():
        safe_name(name)
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise ValueError("file hash required")
    # Exact tree prevents an undeclared module from shadowing packaged imports.
    actual = {}
    for path in project.rglob("*"):
        no_links(path)
        if path.is_file():
            name = safe_name(path.relative_to(project).as_posix())
            actual[name] = digest(path)
    equal(actual, files, "exact admitted project")
    return value
