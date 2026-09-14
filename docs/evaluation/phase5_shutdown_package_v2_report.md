# Phase 5 — observed-shutdown package v2 CPU evidence

Completed 2026-09-14 (Asia/Ho_Chi_Minh). Exact offline package and bounded release
auditor QA, not a new Kaggle run, GPU lifecycle acceptance or Phase 5 freeze.

## Exact package

Source `fa284013566c2a7a8ae164d68988c39250876f96`. New wrapper/builder preserve
the frozen base Dataset and extend the allowlist to 94 files. Runtime/audit v3,
native wiring v2, observed worker/pair v2 and new CLI routing are included without
overwriting frozen base files or adding the benchmark-authoring initializer.

Both archive and Kaggle-expanded/PAX layouts passed in isolated Python venvs
using hash-pinned offline dependencies: eight tool schemas/recovery, 21 public
Dummy tasks and missing-only resume, seven synthetic runtime levels and immutable
completed resume. New package checkpoint audit is byte-repeatable; new native
audit CLI imports in the package. The latter is not a native HF sidecar execution.
Legacy synthetic native-shaped joined-CLI checks also remain explicitly synthetic.

Independent re-audit matched **101 source and 430 raw hashes**, generated wrapper
and metadata hashes. Across the two layouts, 14 runtime receipts join correctly,
20 synthetic guard attempts are recorded and 24 workers are GRACEFUL/reaped.
No native model tensors were materialized locally; no GPU runs occurred.

[Preflight receipt](../../experiments/manifests/phase5_shutdown_package_v2_preflight01.json)
SHA-256 `b768d70b934e5aea4bced61a9dbfeac07303b8862c43a9bf92d91c363e184e45`.
Exact wrapper SHA-256
`3c55d5b7d8e267b255447af24e0dbdb020e4e92d7db1e1a4acad54e2ef50408c`.
Immutable local package: `build/kaggle/phase5_shutdown_package_v2_preflight01`.
Selected receipt bytes equal the generated receipt; raw/build output is untracked.

## Repository QA

Full pytest **2,764 passed, one skipped in 693.35s**; focused 24 passed in 7.11s.
Setup, Ruff, mypy (346 source files) and knowledge-check passed. The optional
native tqdm test skips in the regular local venv; isolated preflight installs
the pinned 4.67.3 wheel offline. Neither result certifies GPU-image compatibility.
QA process wall intervals: 695.224s full, 7.797s focused (including overhead).

[CPU receipt](../../experiments/manifests/phase5_shutdown_package_v2_cpu01.json)
SHA-256 `1802c3c635c6cf431540afd2046d779eba6dfc290d93bcb4f7c256dc506d7e7d`.
Independent re-audit matched **485 source/137 raw hashes** and unchanged hashes
for all 169 tracked data files. Seven focused runtime receipts join correctly.
Parent native-wiring evidence retains all 5,204 source/raw hash matches.
Raw root: `results/phase5_shutdown_package_v2_cpu01`. Working-tree CPU QA only;
unrelated user edits were preserved and excluded from this milestone's commits.

Tests cover allowlist/pins, missing/extra/hash/overwrite rejection, native CLI
routing without retries, remote-shaped metadata/source negatives, independent
audit output and read-only synthetic checkpoint checks. Release auditor v2 is
prepared for v2 bootstrap/preflight/remote identities; metadata tests are not
authentication of an actual remote v2 run or all partial-native failure paths.

## Remaining

`native_submission_ready=False` is intentional. Metadata contains a proposed
v2 notebook ID only; no actual notebook version/URL is claimed. Do not submit this
calculator control as a semantic retry of v1. Next: predeclare a new diagnostic
with lifecycle/tool/guard-path objectives, version its input identity and package,
then verify account/quota/private mounts before GPU submission and terminal audit.

No model/prompt/policy change, benchmark Dev inference, Test/private-GT parsing
or new remote writes occurred. Guard quality/grouped Dev, broader semantic
coverage and Phase 5 freeze remain open. Four of seven aggregate tracking gates
remain closed; package CPU acceptance does not close an additional production gate.

[Contract](../architecture/phase5_shutdown_package_v2_contract.md) ·
[Handoff](../../knowledge/handoff.md) · [Kaggle directory](../../knowledge/kaggle_resources.md).
