# Pair GPU execution v1 — predeclared technical scope

Continue Phase5 only. First combined-residency execution: one private offline
two-T4 kernel, fresh sibling agent/guard workers, two small synthetic calls.
Use model_pair_v1 and model_pair_probe_v1 without changing their deadlines,
thresholds, prompt, generation or failure interpretation. No Test/GT, benchmark
model selection, maximum-context stress, v5 runtime integration or Phase5 closure.

## Bound inputs and compatibility

Frozen guard Dataset `huylmhuhu/react-vn-guard15-probe-data-v1`, version1,
manifest pinned to the cancellation preflight. Frozen source archive/runtime
7649d5bed0b872e93b4233a7dcdbdf0da4623194, guard Qwen1.5B snapshot revision
989aa7980e4cf806f80c7fef2b1adb7bc71aa306 and exact wheel hashes unchanged.
Agent is the read-only Kaggle model `qwen-lm/qwen2.5/transformers/7b-instruct/1`,
expected runtime identity `24b62737df7885edc2facccd6ca172c0266bccec85c30080a9fcb45adad6d19b`.
Agent verifies actual live bytes/header before load and after load; the known
README difference remains a full-inventory failure, never rewritten to success.

Pre-submit inspection of the exact bundled Transformers5.5.0 wheel exposed a
compatibility gap: native Qwen2 registers both inv_freq and original_inv_freq,
while frozen agent v1 admitted only the former. New AgentHFBackendV2 changes
only the post-load buffer validator and adds adapter_protocol to metrics.
Require exact5.5.0, exactly both64-element rotary buffers, permitted FP16/FP32,
same fixed device mapping, and unchanged339FP16parameter shapes/count. All other
admission, geometry, generation, budgets and metrics behavior stays inherited.
Never mutate v1/frozen receipts or substitute a different dependency version.

Wheel SHA256 `821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944`.
Verified directly against Dataset wheel manifest before inspecting source:
modeling_qwen2.py SHA256 `99fa98c5676604cf6ef505892b70fda5c1c4cd835971459f38d61090cccab1e4`;
configuration_qwen2.py SHA256 `281986fef33b2c5226389a479113eb963c8336467e76e1b8d49fd3d18ee4a882`.
This is a packaging-time compatibility fix, not tuning after a GPU/Test result.

## Packaging acceptance

HF entry requires the previously observed torch2.10.0+cu128/CUDA12.8 and pinned
Transformers5.5.0 before any model load. Record these versions in the manifest;
reject drift instead of dynamically replacing torch. Kaggle CLI supports original
image pinning, but prior pulled GPU metadata returned an empty image digest;
there is no claim of a known Docker SHA. Request original image pinning, verify
native versions and actual tensor operations, and retain returned remote metadata.

Embed exact frozen PAX-aware bootstrap source/hash plus an eleven-file overlay,
source commit and Dataset-manifest hash in a new standalone wrapper. Import the
hash-checked bootstrap from a fresh temporary file; never execute model-provided
code. Overlay may add only declared paths, never overwrite original runtime.
Do not upload full repo, knowledge, credentials, private GT, pool or Test.
No agent weight copies/downloads locally. Existing guard archive is reused as-is.

Render from clean committed source; validate actual wrapper in both archive and
expanded/PAX layouts, isolated fresh venv with only pinned base wheels and the
frozen project's src. Verify full file trees/hashes, eight tools/fault, all21
Dummy tasks, completed resume and missing-only resume preserving20checkpoints.
Execute the same new entry point in stub mode through both layouts, including
spawn imports and durable pair outcomes. Stub paths must not load torch/model.

Before GPU push: full QA, retained exact preflight, source pushed to GitHub,
account/quota/private Dataset/version/model pin verification. Kernel title/id
must agree (`react-vn-pair-gpu-v1`) to avoid prior title-derived slug deviation.
No automatic retries. Pull remote wrapper/metadata and fresh output artifacts;
audit source, metrics, model identities, deadlines, raw immutability and cleanup.
Keep any failure and classify it before considering a new execution identity.

Submission wall-clock limit: 3600 seconds for this single technical run, including
bootstrap and live model hashing. This does not extend per-worker cold/warm
deadlines. GPU quota checked pre-submit: 29.33 hours remaining on 2026-09-09.
