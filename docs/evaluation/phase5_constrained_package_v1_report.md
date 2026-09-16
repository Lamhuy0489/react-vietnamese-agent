# Phase 5 — constrained exact package v1

2026-09-16. [Contract](../architecture/phase5_constrained_package_v1_contract.md).
Phase 5 remains **4/7 ≈ 57% acceptance groups**; no new Kaggle run or model result.

## Implemented and rehearsed

The new constrained launcher packages the existing runner, native metrics join
and approved source dependencies. It authenticates embedded bootstrap/archive
bytes before use and routes tokenizer collection → constrained HF run → audit.
Unknown source mode, malformed commit or ambiguous model mount fails closed.

Local development package: `build/kaggle/phase5_constrained_probe_package_dev01`;
[selected receipt](../../experiments/manifests/phase5_constrained_probe_package_dev01.json).
166 worker files/172 source pins; 433 raw files per layout were rehashed.
Both archive and generated-expanded mounts passed in fresh offline venvs, without
editable-install leakage or importing torch/Transformers/tokenizers. Each layout
passed eight-tool recovery preflight, 21 Dummy tasks, full/missing-only resume,
four valid and four deliberate failing synthetic constrained tasks. Per layout,
there were ten fresh constrained task executions and six copied terminal
checkpoints; audits did not convert expected errors into successes.

This package uses explicitly labeled working-tree hashes plus Git base `f5e97ae`;
it is not committed release evidence. Development metadata disables GPU and both
launcher entry points reject native execution. No model weights were loaded.

## Commit preference and verification

Project skills `react-vn-capstone` and `experiment-repro` now require batching one
finished, tested work item with evidence/memory. Small edits, intermediate errors
and routine status changes do not each trigger a commit. A necessary experiment
source freeze is an explicit exception; subsequent receipts can wait for the
next coherent commit. Both skill definitions passed the skill validator.

15 new unit tests passed (routing, identity/mount rejection, hash authentication,
development native lockout, source selection and no release-mode fallback).
Final [QA receipt](../../experiments/manifests/phase5_constrained_package_cpu_qa01.json):
495 focused tests / 42.96s and 105 integration tests / 111.91s passed;
setup/Ruff/mypy444/knowledge/diff checks passed. The 142 active, 86 prior-native
and 175 baseline source pins are unchanged. The development package scan checked
1,043 source/evidence files with zero credential-value matches.
Full repository pytest is excluded because
Test-assigned authoring fixtures must remain sealed.

## Remaining gate

After grouped source freeze, rebuild without `--development` and repeat both
layouts. Before GPU submission, implement/verify the remote source/version/output
authentication path and check actual private account, mounts, Dataset version and
quota. Requested notebook `huylmhuhu/react-vn-constrained-guard-v1` has not been
submitted or authenticated. Do not claim its remote existence from this name.

Production guard/CUDA behavior, guard quality, benign utility, graceful lifecycle
and formal freeze remain open. No Test/private ground truth was accessed.
