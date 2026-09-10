# Native generation-policy library compatibility — CPU

Kaggle `huylmhuhu/react-vn-policy-native-compat-v1`, version1, COMPLETE on its
only submission. Worker source `5c0c20e`; source and pre-submit QA pushed to
GitHub at `c3bf60f` before submission. Private/offline pinned-image CPU kernel,
no model sources, no weights materialized or loaded, no GPU or model.generate.

[Preflight](../../experiments/manifests/phase5_policy_native_cpu_v1_preflight01.json),
[pre-submit QA](../../experiments/manifests/phase5_policy_native_cpu_v1_pre_submit_qa01.json),
[submission](../../experiments/manifests/phase5_policy_native_cpu_v1_submission01.json),
[selected independent audit](../../experiments/manifests/phase5_policy_native_cpu_v1_audit01.json).

[Final release QA](../../experiments/manifests/phase5_policy_native_cpu_v1_release_qa01.json):
1,743tests passed,1optional native tqdm skip in375.60s;34new focused tests pass.
Setup/Ruff/mypy260files/knowledge checks pass. The skipped optional dev-venv test
is not native success; pinned native progress ran separately in exact preflight.

## Observations

Actual installed Transformers5.5.0 and Torch2.10.0+cu128 ran on CPU.
GenerationMixin and GenerationConfig source-file SHA256 values match the
predeclared pinned-wheel sources. Synthetic config fixtures exercise actual
native resolver, special-token preparation and length functions; this is not
Qwen generation. Hook/no-hook controls produce identical final config snapshots.

| Harness case | Native resolve / length hook calls | Outcome | Original methods restored |
| --- | --- | --- | --- |
| Agent success | 1 / 1 | Config total length4608 from4096+512 | Yes |
| Guard success | 1 / 1 | Config total length4224 from4096+128 | Yes |
| Guard injected error | 1 / 0 | RuntimeError after special-token preparation | Yes |
| Guard injected interruption | 1 / 0 | KeyboardInterrupt at the same boundary | Yes |

These are configured lengths, **not emitted tokens or measured KV-cache lengths**.
Publisher fixtures remain unchanged. Private native special-token tensors do
not enter serialized policy snapshots. Failed controls have no completion receipt.
The reused policy protocol's model_generation_calls=1 is a synthetic harness
counter, explicitly qualified in every summary row; actual model.generate calls0.

The CPU-completion marker occurs at59.652s on Kaggle's log-relative timeline;
the native-harness marker occurs at56.236s. These timestamps include bootstrap
and import work and exclude queue provisioning; they are not model latency or
throughput measurements. Platform nbconvert/mistune SyntaxWarnings are retained.

Two independent local audits are byte-identical, SHA256
`b68645e8fbeacc03c3e1e686e8f4f8ad0e9149923ceb245f8e18bb58653304cf`.
They bind the remote wrapper, private CPU metadata, frozen source/bundle,
25overlay hashes, native library source hashes and complete68-file raw inventory.
Dummy21tasks/84events and checkpoint hashes pass; Dummy does not score model
quality. Raw/remote inputs are unchanged. Three known Kaggle credential values
have zero matches in68raw files. Held-out seals are checked hash-only.

## Recorded metadata adaptation and limits

Kaggle pull returns machine_shape as string `"None"`. The outer auditor now
accepts only JSONnull, empty string or literal `"None"` for absent CPU shape,
while separately requiring enable_gpu=false and enable_tpu=false. Nine new
regression tests cover accepted representations and rejected accelerator/other
values. No submitted code, raw output or original pre-submit QA was changed.

This passes bounded native-library compatibility only. It does not authenticate
actual Qwen publisher config, exercise model.generate/forward, measure GPU
context fit or prove global IPC cleanup. Phase5 remains open. Next is the outer
combined stress audit binding publisher metadata, then a separate exact Kaggle
GPU wrapper/preflight. Runtime integration, A4 processing-scope anchors, general
final entitlements and grouped Dev decision/freeze remain independent gates.
