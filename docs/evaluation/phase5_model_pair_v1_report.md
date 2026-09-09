# Model pair lifecycle v1 — synthetic CPU evidence

Source `6d1c761`; [contract](../architecture/phase5_model_pair_v1_contract.md).
No real model load, GPU execution, new Kaggle submission or held-out inference.

## Outcome

Two task-owned sibling workers now have explicit agent-first startup, readiness
without inference, separate cold/warm deadlines, identity and liveness checks,
failure retirement and guard-then-agent cleanup. Frozen WarmGuardBackend,
agent HF loader and guard adapter remain unchanged. No policy/v5 integration
or model selection is claimed by this building block.

37supervisor tests pass with actual spawn processes and synthetic backends:
startup/call failures, identity drift, timeouts, SIGTERM-ignore requiring KILL/-9,
abrupt exit, retained-worker reuse, owner/concurrency/config rejection and sibling
cleanup despite one cleanup error.19probe tests pass for durable artifacts,
memory schema/failure/leak rejection, interruption and fake CUDA observer calls.
These are not real GPU resource-recovery or semantic statelessness proofs.

Two clean-source rehearsals each complete agent/guard readiness and two synthetic
inference calls, then reap both children. Four total child workers across the
two runs close GRACEFULLY on CPU. This does not replace the earlier real guard
GPU result that required TERMINATE. Both runs have six simulated recovery samples;
all match the declared synthetic baseline, which is not measured VRAM.

Each rehearsal preserves15raw files plus a receipt. Their stable outcome summaries
and six source hashes match; raw hashes intentionally differ because PIDs,
timings and process observations differ. Do not report raw byte-identical replay.
140prior source entries (134guard +6agent loader) and Test seals verified without
parsing held-out payloads. Generated outputs stay untracked except selected receipts.

## Verification

Setup/Ruff/mypy224sourcefiles and knowledge-check pass. Final full suite:
1,330tests passed in326.86s; durable JUnit
`results/phase5_model_pair_v1_final01_pytest.xml` records zero failures/errors/skips.
Source boundary is `6d1c761`; no changes to source during final tests/rehearsals.
[Selected CPU receipt](../../experiments/manifests/phase5_model_pair_v1_validation01.json).

## Remaining work

HF entry point, exact source overlay and archive/expanded/PAX worker validation
with8tools/fault/21Dummy/resume; pinned dependencies/private inputs/quota check;
combined GPU residency and artifact audit. The implemented probe has two small
contexts only: maximum-context/cancellation stress needs explicit additional
conditions before running. No owner-SIGKILL or detached-process guarantee.

Grouped Dev/guard choice, broader A4 processing scope, private-record final
entitlements and Phase5 acceptance remain open. No Phase6/7 transition.
