# Pinned public guard deployment — 2026-10-02

Owner authorized deploying the public Llama distribution specifically on
meanalways, retaining the running lamhuy8904 Qwen worker. This changes inference
model acquisition only; it does not access Test or change benchmark/policy scope.
The previous guard versions 1 and 2 failed with no mounted model input, and
authenticated Kaggle file access returned403. Their evidence remains immutable.

The new guard acquires unsloth/Llama-3.2-3B-Instruct at revision
006f5dcd1393c3add266de40994ba96225e9689d without a Hugging Face token. Its private
Kaggle metadata declares no gated model input. Downloaded files must match the
source-pinned size/SHA256 manifest before loading; altered cache, extra files,
symlinks, oversized/incomplete downloads and architecture mismatches fail closed.
No model file is downloaded merely by importing the module. Files are acquired
explicitly at native deployment, before the API starts. The Llama3.2 license
continues to apply; public hosting is not a license waiver.

Two publisher LFS shard hashes and the weight index match the historical Kaggle
guard fingerprint. Config, generation config, tokenizer and special-token files
differ. This is a new source identity and prospective Dev epoch, not evidence
of complete behavioral equivalence. Chat template bytes now join the runtime
model fingerprint. FP16 load, two-T4 tensor checks, constrained generation,
warmup, model bounds and credential-encrypted discovery remain unchanged.

The exact public snapshot manifest is embedded in
src/react_agent/serving/public_llama_source_v1.py. The builder's --public-guard
flag explicitly selects it; the agent configuration is unchanged. Only guard
is to be submitted. A fresh package/session and source commit are required;
do not reuse a failed guard session or overwrite its receipts.

CPU validation before commit:62 targeted acquisition, serving, worker-package,
entrypoint, quiescence and export tests passed. The public guard package passed
all4 isolated role/layout preflights. Setup and mypy631 passed; Ruff passed after
removing one unused test import. Full repository pytest was not rerun. These
checks do not prove native download, model loading, API availability or Phase5
acceptance. Final source-package QA and remote evidence are separate receipts.

After submission, pull the actual source and compare bytes, observe exact version
and status, then authenticate model/source/boot metadata. Assemble local pair
configuration from the existing agent and newly verified guard, with keys in
ignored0600 files only. Native closure v2 uses a new immutable manifest before
any inference; preserve missing/failed conditions and score recorded outputs.

Sources: [public repository](https://huggingface.co/unsloth/Llama-3.2-3B-Instruct),
[read-only evidence](phase5_llama_public_source_20261002.md).
