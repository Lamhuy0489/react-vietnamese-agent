# Phase 3 accepted: adversarial release v2

Accepted 2026-09-07 under the existing owner self-review waiver. Source commit
`c228a6818319f2566ac888b57f0b52492043a1aa`. The earlier v1 remains rejected.
[Closure receipt](../../experiments/manifests/phase3_release_v2_closure.json),
[immutable seal](../../data/adversarial/release_v2/seal.json),
[contract](adversarial_release_v2_contract.md).

| Acceptance item | Verified result |
|---|---|
| Canonicals and grouped split | 70 paired scenarios; 40 Dev/30 Test; 20 intact groups |
| Variant completeness | Five types; 350 attack + 350 matched benign |
| Experimental counts | Each branch 200 Dev/150 Test; canonicals excluded |
| Review | 280 linguistic and 140 boundary records self-reviewed; 280 structural records checked |
| Executable references | 280 canonical + 1,400 variant standard + 12 safe alternatives |
| Integration | Exact fixture/identity mapping; frozen six-scorer dispatch; all eight mock tools |
| Evidence archive | 1,692 reused/re-scored observable traces, not new inference |
| Test seal | Payloads, schema, mapping, source/config, environment/dependencies hash-bound |

Seal SHA-256: `431b81118026bef6c60e33306e51df71160504579e76ea08fb4648005fa1cb6b`.
782 tests passed before sealing; two post-seal-only tests were skipped then.
After sealing, 132 tests pass; 650 historical construction tests are deliberately
not collected, before import, to keep held-out scenarios out of later development.
This is a different suite scope, not a drop in test success or removal of tests.
Setup, Ruff, mypy (146 source files), clean seal and adversarial hash checks pass.

Dedicated mechanical/linguistic receipts contain 1,128/564 fresh Replay paths;
release assembly reuses their 1,692 paths rather than counting them as new runs.
732 of those paths concern Test-assigned construction data, all before seal.
Additional software tests are verification, not experimental/model observations.
Zero new LLM or held-out model runs. Existing Gemma/Qwen scores remain unchanged.

Runtime loading defaults to Dev and does not open Test files or private oracles.
Only task instructions enter the model; synthetic environment values enter via
tools, never by including the fixture object in a prompt. Use only hash checks
for sealed Test integrity; no authoring/replay commands during later development.

Limits remain explicit: assistant review is not independent human review; 70
scenario families are not independent abstract mechanisms; grouped allocation
has output-poisoning 12 Dev/3 Test families. Exact reference parity establishes
bounded solvability/scoring, not general semantic equivalence or model ASR.
Phase 4 and final model experiments have not started.
