"""Write the deterministic Phase 5 20-DoD no-go freeze receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from react_agent.validation.phase5_formal_freeze_v1 import ROOT, write_freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = write_freeze(ROOT, args.output)
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "phase5_accepted": result["phase5_accepted"],
                "dod_count": result["dod_count"],
                "open_dod": result["open_dod"],
                "payload_sha256": result["payload_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
