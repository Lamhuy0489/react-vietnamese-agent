# Phase 5 agent read-only Kaggle mount authentication v1

Owner clarified: large weights stay on Kaggle; local machine does CPU software
QA and orchestration only. No local agent download, model archive or GPU needed.
Do not upload the whole repository: no credentials, Test, private GT or memory.

Before the combined GPU adapter, run one private CPU/offline metadata-and-hash
worker with only the pinned Kaggle source
`qwen-lm/qwen2.5/transformers/7b-instruct/1`. No Dataset, torch, pip, inference,
tool runtime, CUDA or benchmark tasks are in this narrower authentication job.
The eight-tool/Dummy exact mount preflight remains required for a later runtime
GPU job; this CPU-only scanner is not a substitute for that gate.

The worker embeds only the stdlib verifier, committed HF upstream inventory,
source commit and verifier hash. Resolve exactly one mount with suffix
qwen2.5/transformers/7b-instruct/1 (extra leading provider directories permitted).
Reject links on the root/ancestors/entries, unexpected files or directories.
Require all eleven runtime files (four shards, index and six metadata/tokenizer
files); README/LICENSE/.gitattributes may be absent, but verify if present.
Match the frozen HF revision inventory by exact size plus LFS SHA256 for weight
shards, Git blob SHA1 for other files. Also record ordinary SHA256 for every
observed allowed file. Stream files in 1MiB chunks; never copy model bytes or
retain weight contents in output. Inventory is a trusted host input, not a
model-provided prompt. Validate filenames, hash encodings, integer sizes,
unique complete expected inventory and expected model/revision first.

Record all observed per-file mismatches, missing/extra filenames, exact model
handle, inventory/verifier/source identity and timings. Refuse to call a mismatch
authenticated; kernel exits nonzero after durable receipt. Preserve failure,
never silently switch model version or accept a different tokenizer/config.
A successful scan authenticates only present runtime/optional file bytes against
that HF revision, not historical Kaggle pilot execution or placement/quality.
Pre-submit file listing on2026-09-09 already shows README6005bytes on Kaggle
versus6240bytes in the HF inventory. Full-inventory acceptance is therefore
expected to fail; one CPU scan is still useful to establish all runtime hashes
and preserve the exact difference. This is a declared diagnostic job, not an
attempt to certify a known-identical mount or a GPU/runtime experiment. Keep
the full failure even if all runtime files match; further admission of a
runtime-only view requires an explicit versioned contract, not silent filtering.
No model loading, shape/header validation or GPU fit claim in this milestone.
No automated retries; failures require classification and a new explicit scope.

Local preflight uses synthetic tiny shard bytes, not real weights or Test data.
Execute the exact rendered standalone script using isolated Python (-I) on both
direct and nested mount layouts, with hash/tamper/missing/extra/link negatives.
Commit/push source and retain preflight before the single CPU submission.
Afterward pull remote source/hash/private/offline/CPU metadata and download raw
receipt/log into a fresh directory; compare with frozen inputs before selection.
