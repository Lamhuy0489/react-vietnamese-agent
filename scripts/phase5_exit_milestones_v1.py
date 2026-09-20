"""Run synthetic exit controls or audit immutable records; never load a model."""

import argparse
import shutil
import subprocess
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links, write_receipt
from react_agent.llm.exit_milestone_probe_v1 import audit, run

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "audit"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    no_links(args.output)
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "results"):
        raise ValueError("fresh output under results required")
    if args.action == "run":
        if args.input is not None:
            raise ValueError("run does not accept inputs")
        git = shutil.which("git")
        if git is None:
            raise RuntimeError("git required")
        base = subprocess.check_output(  # noqa: S603 - resolved Git, fixed read-only arguments
            [git, "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        run(output, base)
    else:
        if args.input is None or output.is_relative_to(args.input.resolve()):
            raise ValueError("audit requires input separate from output")
        write_receipt(output, audit(args.input))
        print("EXIT_MILESTONE_AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
