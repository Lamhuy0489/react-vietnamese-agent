# Phase 5 — tokenizer and native logits CPU compatibility

2026-09-16. [Protocol](../architecture/phase5_guard_language_native_v1_contract.md).
Source `2269fefa979a6027531516560c838a478c331914`.

## Preflight and scope

[Corrected preflight02 receipt](../../experiments/manifests/phase5_guard_language_cpu_preflight02_corrected.json):
86source pins, archive/expanded source, actual launcher CLI in metadata-only
mode, both tokenizer layouts, eight tools,21Dummy and missing-only resume.
214raw files across two layouts; six tokenizer/config files are read and
authenticated, no model-weight payload. Synthetic language3069/202846prefix
checks remains CPU evidence, not native generation. 38focused tests,
setup/Ruff/mypy423 passed; fullpytest with Test-assigned fixtures excluded.
Logs/check timings: `results/phase5_guard_language_package02`.
The failed package01 is retained: checking mutable aggregate run reports during
resume incorrectly failed; corrected checks bind task checkpoints and identity.
Original selected preflight02 is retained as invalid: a locale warning was
mistakenly copied into its full-receipt digest. Submission01 rejected this
locally before any Kaggle call. The corrected selection preserves the original
package/preflight bytes; no package or model run is repeated for this correction.

Package: `build/kaggle/phase5_guard_language_cpu_package02`.
Access01 verifies ownerhuylmhuhu and private guard15 Datasetready/version1.
Requested notebook `huylmhuhu/react-vn-guard-language-cpu-v1`; no actual handle
or remote availability claimed until submission is confirmed.
[Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
v1/private; no external model mount, accelerator or Internet. Timeout3600s.
This CPU diagnostic does not load weights, call model.generate or use Test/GT.

Next: confirm actual version/source after one submission, preserve terminal
status and authenticate downloaded code, bootstrap, tokenizer hashes and native
summary. Compilation success and masking checks do not establish guard quality
or close Phase5. A later ForcedBOS override is a predeclared negative control;
do not adopt constrained generation without processor-composition admission.
