# Guard diagnostics v1 — Phase 5 bounded implementation contract

2026-09-14. Inputs: frozen guard parser v1, observed document-run failure
classification and public synthetic CPU responses. No reconstruction/retry of
the unretained native guard response, no Test/private-oracle input.

## Opt-in interface

`diagnose(text) -> GuardDiagnostic` emits a response hash, character count,
allowlisted category and deduplicated allowlisted field/error-kind pairs only.
Never retain response text, unknown key names, values, exception text/input/context,
or hidden reasoning. Frozen `parse_guard` remains authoritative. Size/depth
inspection limits are not new parser acceptance rules and never repair output.

`DiagnosticFactory(factory, output)` creates a process-owned backend wrapper.
It forwards the same request/config objects and response unchanged, preserving
model identity and transport exceptions. Sidecar durability errors fail closed
with a sanitized exception. Each returned response has one fsynced sidecar
bound to worker PID, request/generation hashes and sequence; no semantic retry.
Not automatically added to historical native factories or inference packages.

## Acceptance

- Structural categories and synthetic secret/unknown-key exclusion.
- Actual spawned A2–A6 parity, safe and three invalid-response controls, with
  PID/request/generation joins. Schema rejection, pair retirement and missing
  POST/agent native attempts must remain observable; no fake successful fallback.
- Source/data hashes, full setup/Ruff/mypy/pytest and memory navigation checks.
- Record native limitation: historical INVALID_OUTPUT subtype still unknown.
  Successful synthetic diagnostics do not constitute guard quality or GPU proof.

## Outcome-independent Dev preparation

Metadata-only planner reads exactly `dev_attack.jsonl` and `dev_benign.jsonl`.
Validate 40 families/8 groups/5 variants and paired branch identities. Select
one family per group by minimum SHA256(seed + newline + family_id), tie-break
family ID; seed `phase5-grouped-dev-structured-output-v1`. Select the paraphrase
variant and its matched benign branch: 8 pairs/16 cases, A0–A6=112 runtime tasks.
Do not inspect outcomes or scorer answers to select cases. No Test directory
traversal, payload exports, promotion to final benchmark or inferred model choice.

The plan is dispatch-disabled until input/host-catalog/worker manifests, guard
diagnostic native integration, exact package and pre-submit QA are frozen.
Remaining 32 families stay separate from this screening selection. Eight groups
are strata/cluster units, not 16 independent canonical families. No ASR/FPR claim
or Phase 6/7 scope is authorized by this preparatory schedule.
