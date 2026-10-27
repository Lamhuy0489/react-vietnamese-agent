"""Run one source- and manifest-admitted doc_read proof task on native workers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.llm.doc_read_native_dispatch_v1 import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "manifest-path", "project", "source-manifest", "inputs", "agent", "guard", "output"
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--resume", action="store_true")
    result = run(**vars(parser.parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
