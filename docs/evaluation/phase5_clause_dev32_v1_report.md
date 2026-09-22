# Phase5 — Dev32 candidate runner: CPU evidence

2026-09-22. **The fixed 32-task runner, checkpoint/resume and candidate artifact
audits pass CPU verification. No native model or Kaggle run was started.**

[Contract](../architecture/phase5_clause_dev32_v1_contract.md),
[controls](../../experiments/manifests/phase5_clause_dev32_cpu01.json),
[independent audit](../../experiments/manifests/phase5_clause_dev32_audit01.json),
[expanded QA](../../experiments/manifests/phase5_clause_dev32_qa02.json).

## Results and limits

- Eight shards, 16 fixed public-Dev fixtures × A2/A6: 32 completed synthetic tasks.
- 64 workers reaped with GRACEFUL shutdown; 32 synthetic recovery checks passed.
- Complete-resume changed no raw files and did not run tasks again. Two separate
  audit passes per shard found 32 unique keys and matching checkpoint bindings.
- 188 source pins and 928 raw artifact hashes independently verified. The full
  summary is separately hashed in the selected receipt.
- 23 new tests: 14 runner integrations and nine native-shaped unit/lazy-factory
  controls. Faults include manifest/raw tampering, missing checkpoints, preserved
  backend failures, cross-host interpreter and native token/count mismatches.

The synthetic agent performs a fixture trigger followed by a scripted answer.
`completed` does not mean a correct business answer or benign utility. These
counts are infrastructure controls, not native ASR/FPR, speed or GPU reliability.
The native audit adapter joins existing source-independent artifact checks but
does not authenticate a native release; runner HF dispatch deliberately remains
closed. No model inference, private GT or held-out Test parsing occurred.

## Reproduction and storage

Run `.venv/bin/python scripts/run_phase5_clause_dev32_cpu_v1.py --output
results/<fresh-directory>` from the repository with dependencies installed.
The command refuses existing output and records source pins before/after all
shards. Use checkpoint audits to inspect existing output, not a replacement run.

Raw: `results/phase5_clause_dev32_cpu01`; repeated audit:
`results/phase5_clause_dev32_audit01`. QA logs/receipt:
`results/phase5_clause_dev32_qa02`; the earlier complete QA01 is retained too.
Selected receipts above are suitable for version control; full raw remains
local/untracked, without an independent off-machine backup.
Source base `6d039e255a0a0a91f6e514cfebe889c4b7ae8aed` plus explicitly
uncommitted working-tree hashes. No new commit/push or remote availability claim.

Expanded QA: 888 focused tests in45.40s and395 integration tests in351.23s.
Setup/Ruff/mypy488/knowledge/diff checks pass. All182 frozen native source pins,
eight previous paired-QA source pins and169 tracked data hashes are unchanged.
Full-repository pytest is not claimed: sealed Test-authoring fixtures were excluded.

## Next concrete work

Create the Dev32 native source/release admission and launcher, then rehearse the
exact Kaggle archive and expanded layout offline. Only after those gates pass,
freeze the required source and submit the declared workload once. Do not repeat
the old four-task native diagnostic. Measure classification/utility separately
from completion, and preserve all failures. Native lifecycle reliability and
formal DoD freeze remain open. Formal acceptance remains4/7 (~57%).
