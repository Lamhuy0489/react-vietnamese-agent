"""Add authenticated tokenizer expectations to the frozen ordinary joined auditor."""

from pathlib import Path
from typing import Any

from react_agent.llm.agent_mount_v1 import no_links
from react_agent.llm.guard_snapshot_v1 import GuardSnapshot
from react_agent.validation.context_stress_audit_v1 import equal, inventory
from react_agent.validation.efficient_requests_audit_v1 import _record
from react_agent.validation.guard_probe_audit_v2 import require
from react_agent.validation.ordinary_native_audit_v1 import audit as audit_native
from react_agent.validation.ordinary_pair_audit_v1 import ROLES
from react_agent.validation.tokenizer_metadata_v1 import authenticate


def audit(
    probe: Path,
    policy: Path,
    attention: Path,
    publishers: Path,
    tokenizers: Path,
    *,
    pin: GuardSnapshot,
    commit: str,
) -> dict[str, Any]:
    """Read-only; callers cannot override derived pad IDs or promote native acceptance."""
    roots = dict(
        probe=probe,
        policy=policy,
        attention=attention,
        publishers=publishers,
        tokenizers=tokenizers,
    )
    for name, root in roots.items():
        no_links(root)
        require(root.is_dir(), "audit input directory")
        for other_name, other in roots.items():
            if other_name != name:
                require(
                    not root.resolve().is_relative_to(other.resolve())
                    and not other.resolve().is_relative_to(root.resolve()),
                    "disjoint tokenizer audit inputs",
                )
    before = {name: inventory(root) for name, root in roots.items()}
    tokenizer_tree = sorted(p.relative_to(tokenizers).as_posix() for p in tokenizers.rglob("*"))
    equal(
        sorted(p.name for p in tokenizers.iterdir()),
        [f"{role}_tokenizer_config.json" for role in ROLES],
        "exact tokenizer sidecars",
    )
    metadata = {
        role: authenticate(tokenizers / f"{role}_tokenizer_config.json", role) for role in ROLES
    }
    joined = audit_native(
        probe,
        policy,
        attention,
        publishers,
        pin=pin,
        commit=commit,
        pad_token_ids={role: row["pad_token_id"] for role, row in metadata.items()},
    )
    for role in ROLES:
        # The inner auditor already authenticates the agent file-list content
        # identity and the guard's complete snapshot identity. Join this metadata
        # to those same admitted files, rather than accepting an arbitrary pin.
        if role == "agent":
            first = _record((probe / "agent_hf_metrics.jsonl").read_text().splitlines()[0])
            entries = first["runtime_admission"]["files"]
        else:
            entries = [entry.model_dump() for entry in pin.files]
        matches = [entry for entry in entries if entry["name"] == "tokenizer_config.json"]
        require(len(matches) == 1, "admitted tokenizer metadata coverage")
        for key in ("size", "sha256"):
            equal(matches[0][key], metadata[role]["identity"][key], "admitted tokenizer " + key)
        require(
            metadata[role]["eos_token_id"]
            in joined["publishers"][role]["publisher_json"]["eos_token_id"],
            "tokenizer EOS included in publisher stop IDs",
        )
    equal(
        {name: inventory(root) for name, root in roots.items()},
        before,
        "tokenizer joined inputs changed during audit",
    )
    equal(
        sorted(p.relative_to(tokenizers).as_posix() for p in tokenizers.rglob("*")),
        tokenizer_tree,
        "tokenizer input tree changed during audit",
    )
    return dict(
        protocol="ordinary_tokenizer_joined_audit_v1",
        valid=True,
        tokenizer_metadata_authenticated=True,
        tokenizer_ids_bound_to_policy=True,
        native_tokenizer_executed=False,
        native_validated=False,
        source_authenticated=False,
        phase5_accepted=False,
        source_commit=commit,
        tokenizers=metadata,
        joined=joined,
        input_sha256=before,
        scope="Authenticated configuration-derived IDs joined to six-call policy evidence. "
        "Does not execute/tokenize text or prove native tokenizer, model, source, package, "
        "remote execution, quality or Phase 5 acceptance. Inner audit flags retain their scope.",
    )
