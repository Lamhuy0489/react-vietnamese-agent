#!/usr/bin/env python3
"""Run all pre-split clean-pool acceptance checks and write QA reports."""

from pathlib import Path

from react_agent.validation import validate_clean_pool, write_clean_pool_reports

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    result = validate_clean_pool()
    write_clean_pool_reports(result, ROOT / "data" / "clean" / "v1" / "reports" / "pool")
    if not result["valid"]:
        for failure in result["failures"]:
            print(f"FAIL: {failure}")
        return 1
    print(
        f"PASS: {result['total_tasks']}/250 schemas, "
        f"{result['oracle_valid']}/250 oracles, "
        f"{result['review_coverage']}/250 owner acceptances"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
