#!/usr/bin/env python3
"""Run clean environment acceptance checks from the command line."""

from react_agent.validation import validate_environment


def main() -> int:
    failures = validate_environment()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: clean_env_v1 satisfies schema, scale, integrity, and offline constraints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
