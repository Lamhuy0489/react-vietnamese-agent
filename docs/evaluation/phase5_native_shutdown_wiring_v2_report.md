# Phase 5 — native shutdown wiring v2 CPU evidence

Completed 2026-09-14 (Asia/Ho_Chi_Minh). Native factory composition, versioned
runner/checkpoint and native-shaped auditor QA only; no GPU or Phase 5 acceptance.

## Result and identity

Source `dfbd54f12835727eb9d2309341b006bafbb92c34`. Full pytest **2,740 passed,
one skipped in 719.76s**; focused 36 passed in 27.70s. Setup, Ruff, mypy (342
source files) and knowledge-check passed. Optional native tqdm is unavailable
locally; this skip does not certify dependency compatibility in the GPU image.
QA subprocess wall times: 720.888s full, 28.458s focused, including overhead.

[Selected receipt](../../experiments/manifests/phase5_native_shutdown_wiring_v2_cpu01.json)
SHA-256 `fd4c7a3fcc773811545a286d5b23e3b1bfa214526ba115bd54eb3052c1a8e911`.
Independent re-audit matched 478 source/4,726 raw hashes and unchanged hashes
for all 169 tracked data files. Parent pair/runtime v3 receipt still matches
all 1,114 source/raw entries. This is working-tree CPU QA; unrelated user edits
were preserved, not claimed absent. Immutable raw output remains untracked at
`results/phase5_native_shutdown_wiring_v2_cpu01`.

## What passed

- New native composition creates ShutdownPair directly with pinned model
  identities and observed-shutdown workers. Agent-only preserves the same lazy
  agent stack with separate startup/call execution config. Topology, pickle,
  path isolation and rejection-before-allocation controls pass without loading
  native models. Both native runner branches are inspected before model load.
- Real-spawn synthetic runner exercises seven levels, completed/missing-only
  resume and rejection of changed identity/partial attempts. 15 retained runtime
  receipts independently join correctly, with 26 GRACEFUL/reaped lifecycle
  events. These workers use synthetic backends, not native HF inference.
- Native-shaped audit controls retain 70 synthetic receipt records, explicitly
  mocked at the checkpoint boundary. Source/tokenizer/policy/timing/role and new
  protocol/config mutations are rejected. A recovered-but-forced synthetic
  control is not labelled observed graceful. These 70 records are not 70 runs
  on a GPU and are excluded from actual runtime-execution counts.

Checkpoint v2 binds protocol, known public inputs and execution configs; old
v1 checkpoints cannot silently resume in the new runner. Native joined audit v2
separates lifecycle observations, memory recovery and artifact integrity.
Partial native-call evidence remains explicitly unverified. Existing native
metrics have no independent request-content hash: native sidecar correspondence
uses role/PID/order/config/timing, not full native payload authentication.

## Remaining and scope protection

No native model load, Kaggle submission, benchmark Dev inference, Test/private-GT
parsing or model/prompt/policy change. All old source/receipts remain unchanged.
The public calculator is a CPU wiring control, not a retry of its old native
zero-tool/guard semantic outcome. No new Kaggle URLs/versions exist at this milestone.

Next: version wrapper/builder and release auditor; verify exact archive/expanded
mounts, isolated imports, eight tools, public Dummy/missing-only resume and new
runner/auditor CLI routing. Predeclare a new native lifecycle/guard-path diagnostic
before GPU use. Grouped Dev guard quality, broader semantic coverage and formal
Phase 5 freeze remain open. Four of seven aggregate tracking gates remain closed;
this CPU milestone does not close an additional native/quality/freeze gate.

[Contract](../architecture/phase5_native_shutdown_wiring_v2_contract.md) ·
[Next-package checklist](../../knowledge/native_shutdown_wiring_v2.md) ·
[Kaggle directory](../../knowledge/kaggle_resources.md).
