# Phase 5 — tokenizer and native logits CPU compatibility

2026-09-16. [Protocol](../architecture/phase5_guard_language_native_v1_contract.md).
Source `2269fefa979a6027531516560c838a478c331914`.

## Current terminal result — COMPLETE and audited

Notebookv1/ID134521565 was COMPLETE before download at18:34:40UTC and remained
COMPLETE/private/version1 after download at18:36:08UTC on2026-09-15.
[Terminal identity](../../experiments/manifests/phase5_guard_language_cpu_terminal01.json),
[release audit](../../experiments/manifests/phase5_guard_language_cpu_audit01.json),
[native CPU summary](../../experiments/manifests/phase5_guard_language_cpu_summary01.json),
[QA](../../experiments/manifests/phase5_guard_language_cpu_release_qa01.json).

Actual Qwen tokenizer admits all3069combinations; maximum response plus EOS is
**36tokens**, below128. Actual Transformers5.5/Torch2.10/tokenizers0.22.2 pass
**248mask checks** on the predeclared12paths. Six tokenizer/config hashes and
installed processor source match pinned inputs. Compilation took0.839066s;
mask harness, faults and input recheck took0.521304s (not model latency or total
notebook time). No weights/model.generate/GPU/Test/privateGT were used.

The later ForcedBOS processor deliberately overrides the prefix mask. This
negative control passed; it is **not** a claim that arbitrary processor chains
are safe. Future native guard adapter must admit only the declared composition
and verify completion; no fallback to unconstrained generation. Errors and
interruption propagate; thread settings restore and fresh callback remains usable.

10raw/2remote files and86source pins authenticated. Two local audits (02/03)
using the post-download observation are byte-identical. Native library checks
were executed once on Kaggle; local audit authenticates source/artifacts and
bounded reported metrics, it does not independently rerun those libraries.
58focused tests/6.40s, setup/Ruff/mypy424/knowledge pass;175baseline pins unchanged.
Final [closure check](../../experiments/manifests/phase5_guard_language_cpu_close01.json)
reverified214preflight raw files and86source pins;37selected evidence/source
files scanned against configured credential values, zero matches.
Raw `results/phase5_guard_language_monitor03`; post-download observation
`results/phase5_guard_language_terminal04`; audits02/03 and release_qa02 use
the same `phase5_guard_language_` prefix. Keep audit01 and QA01 history (a local
101-character lint line was corrected before QA02); do not redownload/resubmit.

Next: opt-in guard adapter with constrained-generation/cache/audit identity and
strict processor composition, followed by exact package preflight before a
separately preregistered GPU diagnostic. No native model quality/utility or Phase5
acceptance is claimed; acceptance groups remain4/7≈57%.

## Submission-time history

Submitted once: [actual notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-language-cpu-v1),
version1/ID134521565, private CPU, QUEUED at2026-09-15 18:28:13UTC.
Remote source SHA matches; GitHubevidencecfd1dd9 preceded submission.
[Submission receipt](../../experiments/manifests/phase5_guard_language_cpu_submission01.json).
No native result yet at this observation; do not resubmit.

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
