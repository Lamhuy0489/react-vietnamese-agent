#!/usr/bin/env python3
"""Check memory navigation and handoff structure, not semantic truth or acceptance."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("README.md", "current_status.md", "handoff.md", "runbook.md")
SECTIONS = ("Đang làm", "Bước tiếp theo", "Bằng chứng", "Giới hạn")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    memory = root / "knowledge"
    failures = [f"missing:{name}" for name in REQUIRED if not (memory / name).is_file()]
    handoff = memory / "handoff.md"
    if handoff.is_file():
        text = handoff.read_text(encoding="utf-8")
        for section in SECTIONS:
            if f"## {section}\n" not in text:
                failures.append(f"handoff_section:{section}")
        if not re.search(r"^Cập nhật: \d{4}-\d{2}-\d{2}\.", text, re.MULTILINE):
            failures.append("handoff_date")
    paths = list(memory.glob("*.md"))
    dashboard = root / "START_HERE.md"
    if dashboard.is_file():
        paths.append(dashboard)
    for path in sorted(paths):
        # This repository uses inline links; code fences are not navigation.
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for link in re.findall(r"\]\(([^)]+)\)", text):
            target = link.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme in {"http", "https", "mailto"}:
                continue  # No network lookup or remote content loading.
            if parsed.scheme or parsed.netloc:
                failures.append(f"unsupported_link:{path.name}:{target}")
                continue
            if not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(root):
                failures.append(f"outside_repository:{path.name}:{target}")
                continue
            relative = resolved.relative_to(root)
            if (
                "credential kaggle" in relative.parts
                or "private" in relative.parts
                or (
                    relative.parts
                    and relative.parts[0] == "data"
                    and "test" in relative.name.casefold()
                )
            ):
                failures.append(f"restricted_memory_link:{path.name}:{target}")
            elif not resolved.exists():
                failures.append(f"broken_link:{path.name}:{target}")
    return sorted(set(failures))


def main() -> int:
    failures = validate(ROOT)
    for failure in failures:
        print(f"FAIL: {failure}")
    if not failures:
        print(
            "PASS: knowledge links and handoff structure; semantic freshness needs evidence review"
        )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
