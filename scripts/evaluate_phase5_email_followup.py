"""Saved-only evaluator for the exact-body A3--A6 follow-up."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import evaluate_phase5_mainline as base

from react_agent.serving.structured_api_v1 import canonical


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    setattr(base, "CASES", ("email_exact_safe",))  # noqa: B010
    setattr(base, "LEVELS", ("A3", "A4", "A5", "A6"))  # noqa: B010
    original_checked = base.checked

    def checked(root: Path, name: str, expected: str) -> None:
        if name == "scripts/evaluate_phase5_mainline.py":
            original_checked(args.run / "source_snapshot",
                             "scripts/evaluate_phase5_email_followup.py", expected)
            return
        original_checked(root, name, expected)

    setattr(base, "checked", checked)  # noqa: B010
    original_score = getattr(base, "score")  # noqa: B009

    def score(case: str, *args: Any) -> dict[str, Any]:
        row = cast(dict[str, Any], original_score("email_safe", *args))
        row["case"] = case
        return row

    setattr(base, "score", score)  # noqa: B010
    result = base.evaluate(args.run)
    with args.output.open("x") as stream:
        stream.write(canonical(result) + "\n")
    print(canonical({"aggregate": result["aggregate"], "missing": result["missing"]}))


if __name__ == "__main__":
    main()
