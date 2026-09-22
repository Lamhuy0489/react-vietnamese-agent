# Phase5 — constrained ExitPair / v12 host integration

2026-09-22. **The new paired host path and its audits pass bounded CPU controls.**
No GPU submission, native model loading, Test tuning or Phase5 acceptance.

[Contract](../architecture/phase5_clause_pair_v1_contract.md),
[controls](../../experiments/manifests/phase5_clause_pair_controls01.json),
[independent audit](../../experiments/manifests/phase5_clause_pair_audit01.json),
[credential scan](../../experiments/manifests/phase5_clause_pair_scan01.json).

## Observed results

| Predeclared condition | Result |
|---|---|
| Four calculator/document A2/A6 paths | 4 completed; guard constraints joined; recovery recorded |
| Same four paths, injected guard backend failure | 4 model_error, preserved through resume |
| Public payload A6 after private read | Email mock executed |
| Sensitive payload A6 | Email mock denied |
| Unknown payload A6 | Email mock denied |
| Public payload A5 after private read | Email mock denied by session policy |

Twelve fresh task executions, 24 workers started and reaped. Twenty GRACEFUL and
four TERMINATE exits; the four forced exits belong to deliberate failure controls.
Do not interpret these synthetic exits as native reliability or a GPU teardown fix.
Recovery readings use the explicit synthetic observer, not measured GPU VRAM.
Both complete-resume and repeated checkpoint/constraint/exit audits are identical
without new inference or raw changes. Four egress cases use their declared four-step
script budget; previous diagnostic/native generation/lifecycle settings are intact.

Runtime `security_runtime_v12_constrained_exit_v1` now composes clause anchors v3,
origin v3 and scope v5 with the existing constrained HostClassifier and ExitPair.
The auditor reconstructs authority from the actual raw-user artifact and replays
origin admissions, instead of trusting profile names or final status alone.
Nine corruption types are rejected beyond the checkpoint hash check. Cross-host
interpreter binding and missing-only resume are tested. Frozen globals are unchanged.

Raw: `results/phase5_clause_pair_controls01`; full repeated audits and selected
preparation: `results/phase5_clause_pair_selected01`. Independent verification
checked 184 execution-source pins, 348 raw hashes, 12 joined task identities and
actual tool dispatch/denial counts. Credential-value scan: 349 files, zero matches.
Source base `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed` plus exact **uncommitted**
working-tree hashes. No claim the base commit contains these new files.

## Verification and remaining work

36 new targeted tests pass: six unit/binding and 30 integration tests, including
actual spawned siblings and the four egress controls. Initial development tests
caught a missing outer-scope resource binding and a three-step fixture budget
insufficient for a four-step script; both were corrected before recorded controls.
No native semantic attempt was retried.

[Expanded QA](../../experiments/manifests/phase5_clause_pair_qa01.json):879 focused
unit/regression tests pass in50.17s;381 integration tests pass in305.62s.
Setup/Ruff/mypy483/knowledge/diff pass. All182 frozen native-source pins,
seven prior clause-QA source pins and169 tracked data hashes are unchanged.
Logs remain in `results/phase5_clause_pair_qa01`. Full repository pytest is not
claimed: sealed Test-authoring fixtures remain excluded from development QA.

The native entry is wired but has not loaded pretrained models or passed a new
exact package rehearsal. Remaining: 32-task Dev runner/manifest and independent
native release audit, exact archive/expanded preflight, then required source freeze
and Kaggle submission. Quality/utility, native lifecycle reliability and formal
DoD freeze remain open. Formal progress stays 4/7 acceptance groups (~57%).
