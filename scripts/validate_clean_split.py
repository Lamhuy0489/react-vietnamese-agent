#!/usr/bin/env python3
"""Validate frozen clean_v1.0 split integrity without running a model on Test."""

import csv
import json
from pathlib import Path

from react_agent.validation import validate_clean_split

ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "data" / "clean" / "v1" / "reports" / "split"


def main() -> int:
    result = validate_clean_split()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    (REPORT_ROOT / "split_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (REPORT_ROOT / "split_distribution.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["category", "dev", "test"])
        for category in sorted(result.get("dev_category_counts", {})):
            writer.writerow(
                [
                    category,
                    result["dev_category_counts"][category],
                    result["test_category_counts"][category],
                ]
            )
    if not result["valid"]:
        for failure in result["failures"]:
            print(f"FAIL: {failure}")
        return 1
    print(
        f"PASS: frozen split has {result['dev_tasks']} Dev / {result['test_tasks']} Test, "
        f"group_overlap={result['group_overlap']}, semantic_overlap={result['semantic_overlap']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
