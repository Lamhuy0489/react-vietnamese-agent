"""Collect only authenticated public tokenizer configs; never read weights or run models."""

import argparse
from pathlib import Path

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.validation.context_stress_audit_v1 import equal
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.tokenizer_metadata_v1 import MODELS, SIZE, authenticate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("agent-path", "guard-path", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    sources = dict(agent=args.agent_path, guard=args.guard_path)
    no_links(args.output)
    require(not args.output.exists(), "fresh metadata output")
    for root in sources.values():
        no_links(root)
        require(
            not args.output.resolve().is_relative_to(root.resolve())
            and not root.resolve().is_relative_to(args.output.resolve()),
            "metadata output outside model inputs",
        )
    admitted = {
        role: authenticate(sources[role] / "tokenizer_config.json", role) for role in MODELS
    }
    args.output.mkdir(parents=True)
    for role in MODELS:
        source = sources[role] / "tokenizer_config.json"
        target = args.output / f"{role}_tokenizer_config.json"
        with source.open("rb") as stream:
            raw = stream.read(SIZE + 1)
        with target.open("xb") as stream:
            stream.write(raw)
        equal(authenticate(target, role), admitted[role], "copied tokenizer identity")
        equal(authenticate(source, role), admitted[role], "source tokenizer changed")
    print("TOKENIZER_METADATA_COLLECTED roles=2 native_tokenizer_executed=False")


if __name__ == "__main__":
    main()
