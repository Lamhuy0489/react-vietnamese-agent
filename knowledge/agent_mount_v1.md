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
actual model weights. Fullsuite1.172tests/263,13s pass;setup/Ruff/mypy216files
và knowledge pass. Actual rendered wrapper -I help/import pass.
[Preflight](../experiments/manifests/phase5_agent_mount_v1_preflight01.json).
First submission v1 accepted; actual kernel `huylmhuhu/react-vn-agent-mount-auth-v1`.
Requested id có agent7b nhưng title không có7b nên Kaggle tạo slug theo title.
Giữ metadata/preflight gốc, audit actual source bằng wrapper hash; không resubmit
chỉ để sửa tên. Source/receipt push2db4496 trước CPU; scanner source97c9507.
Preflight/source freeze, render/help checks, push, single CPU submission and
returned source/hash audit are complete; see results below. Next is separate
runtime admission, budget-enforcing agent loader and combined GPU preflight.
Existing guard/classification diagnostics and Test seals remain unchanged.

Pre-submit CLI listing:14files, README6005bytes vs HF6240bytes. Other13sizes
match, which is not a hash proof. Full-inventory rejection is expected. The
single CPU diagnostic will gather exact runtime hashes and preserve doc mismatch;
no changing pin or filtering README to obtain pass. No weights loaded/generated.

## CPU diagnostic finished; runtime hashes match

Actual kernel v1(id133605346) ERROR because the scanner deliberately exits1 on
full mismatch, not a failed model load.14files/15,242,807,035bytes hashed in
290,801s. All11runtime files match publisher size/hash; LICENSE/.gitattributes
also match; only README differs. No missing/extra entries, no retry.
[Report](../docs/evaluation/phase5_agent_mount_v1_report.md),
[scan](../experiments/manifests/phase5_agent_mount_v1_scan01.json),
[audit](../experiments/manifests/phase5_agent_mount_v1_audit01.json).
Remote source matches wrapper, private/offline/CPU and modelversion1 verified.
Framework case serialized Transformers; strict owner/model/variation/version
retained. Two audits byte-identical; six raw/remote/audit files credential scan0.
15new audit tests pass; final fullsuite1.187tests/238,38s pass. Setup/Ruff/
mypy218files/knowledge pass. Do not call full mount accepted.
[Release QA](../experiments/manifests/phase5_agent_mount_v1_release_qa01.json).
Next separate runtime-input admission with known documentation difference pinned,
then agent loader enforcing12/7GiB process budgets. Model remains on Kaggle.
