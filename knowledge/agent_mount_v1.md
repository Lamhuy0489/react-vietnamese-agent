# Agent model remains on Kaggle — 2026-09-09

Owner explicitly clarified local machine has no GPU: all large models and heavy
model jobs must run on Kaggle. No local Qwen7B download or storage expansion is
required by this workflow. Disk limitation of the earlier multi-copy suggestion
does not block read-only Kaggle model mounts.

[Contract](../docs/architecture/phase5_agent_mount_v1_contract.md): first a
private CPU/offline worker verifies the pinned model mount against HF publisher
hashes; no inference, CUDA, benchmark inputs, Dataset or full repo upload.
Worker source is a stdlib-only scanner plus frozen inventory/commit/hash.
Only metadata/hash receipts and logs return to local; model weights stay mounted.

Kaggle model handle `qwen-lm/qwen2.5/transformers/7b-instruct/1`, compared against
HF revision `a09a35458c702b33eeacc393d103063234e8bc28`. Eleven required runtime
files; three optional documentation files also verified when present.
LFS SHA256 for four weight shards, Git blob SHA1 for publisher metadata and
ordinary SHA256 for every observed permitted file. Inventory mismatches are
retained, not accepted or silently repaired. Success proves file bytes only.

29 targeted tests pass including standalone isolated(-I) renderer execution on
direct/nested synthetic mounts and negative corruption; fake tiny bytes, not
actual model weights. Fullsuite pending. No submission yet at this entry.
Next: commit/source freeze, render actual-inventory wrapper and help/import check,
retain preflight, push, submit once CPU, pull exact source and audit returned
hashes/status. Then budget-enforcing agent loader and combined GPU preflight.
Existing guard/classification diagnostics and Test seals remain unchanged.

Pre-submit CLI listing:14files, README6005bytes vs HF6240bytes. Other13sizes
match, which is not a hash proof. Full-inventory rejection is expected. The
single CPU diagnostic will gather exact runtime hashes and preserve doc mismatch;
no changing pin or filtering README to obtain pass. No weights loaded/generated.
