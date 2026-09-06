"""Reuse frozen QA/scorers for transaction candidates with full-pool grouping."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from react_agent.authoring.candidate_qa import load_candidates
from react_agent.authoring.candidate_review import group_audit
from react_agent.authoring.mechanism_batch import verify_batch
from react_agent.authoring.workbench_qa import file_hashes


def verify_transactions(
    inputs: Path, priors: list[Path], clean: Path, output: Path
) -> dict[str, Any]:
    inputs, clean, output = (p.resolve() for p in (inputs, clean, output))
    priors = [p.resolve() for p in priors]
    if not priors or len(set(priors)) != len(priors) or inputs in priors:
        raise ValueError("nonempty distinct prior roots required")
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in priors):
        raise ValueError("output must be separate from all prior inputs")
    candidates = load_candidates(inputs)
    prior_candidates = [c for p in priors for c in load_candidates(p)]
    combined = [*prior_candidates, *candidates]
    if len(candidates) != 12:
        raise ValueError("transaction batch v1 requires twelve candidates")
    for identities in (
        [c.public.task_id for c in combined],
        [c.metadata.family_id for c in combined],
        [c.overlay.source_id for c in combined],
    ):
        if len(identities) != len(set(identities)):
            raise ValueError("cross-batch identity collision")
    prior_before = [file_hashes(p) for p in priors]
    report = verify_batch(inputs, priors[0], clean, output)
    exfiltration = {
        c.public.task_id for c in candidates if c.overlay.attack_category == "data_exfiltration"
    }
    if len(exfiltration) != 2:
        raise ValueError("transaction batch requires two encoded sink-position cases")
    for check in report["checks"]:
        if check["task_id"] in exfiltration and check["fixture"] == "negative":
            if not any(
                "encoded_sink_disclosure" in reasons
                for reasons in check["score"]["mechanism_reasons"].values()
            ):
                raise ValueError("encoded sink fixture only triggers an argument mismatch")
    if prior_before != [file_hashes(p) for p in priors]:
        raise ValueError("prior input bytes changed during transaction QA")
    return {
        **report,
        "scope": "twelve transaction/sink-position candidates; not Phase 3 acceptance",
        "combined_candidates": len(combined),
        "group_audit": group_audit(combined),
        "prior_inputs": [
            {"root": str(p), "sha256": hashes}
            for p, hashes in zip(priors, prior_before, strict=True)
        ],
        "encoded_sink_negative_checks": 4,
    }
