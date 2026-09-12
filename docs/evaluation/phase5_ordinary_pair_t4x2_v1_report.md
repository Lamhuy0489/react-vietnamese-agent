# Phase 5 ordinary pair — native T4×2 technical report

## Scope

This report covers one private, Internet-disabled Kaggle kernel using the exact
ordinary package preflight.  It is a feasibility and provenance check for the
native model pair, not a benchmark-quality or security-acceptance experiment.
No held-out Test payload, private ground truth, semantic retry, or real external
side effect was used.

## Identity and integrity

| Item | Value |
| --- | --- |
| Kernel | `huylmhuhu/react-vn-ordinary-pair-t4x2-v1` v1 |
| Machine shape | `NvidiaTeslaT4` |
| Dataset | `huylmhuhu/react-vn-guard15-probe-data-v1` v1, private/offline |
| Package source commit | `a412e571a6fba89103b93c55eb830106bede2d01` |
| Preflight receipt SHA-256 | `080d7370f937bb5bb6b466a393b31ebc12ffe210325763d2a320b91332091d9d` |
| Remote wrapper SHA-256 | `1429eb99ade62c555378c44c1559e61049519f171f0f62fbc8eedf510d49cf45` |
| Release audit | [`phase5_ordinary_pair_t4x2_v1_audit01.json`](../../experiments/manifests/phase5_ordinary_pair_t4x2_v1_audit01.json) |

The downloaded remote source contains only the kernel metadata and renamed
wrapper.  Their inventory and wrapper hash match the package.  The bootstrap
identity, pinned guard snapshot, source overlay, wheel set, clean/adversarial
seals and 21-task Dummy artifacts were independently checked.

## Native execution

The pair was loaded once per role on two Tesla T4 devices with the pinned
Transformers 5.5.0 / Torch 2.10.0+cu128 environment, FP16 and SDPA.  The
ordinary runner issued six calls in the fixed order shown below.

| # | Input | Role | Input tokens | Output tokens | Native seconds |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | A | agent | 43 | 8 | 2.245 |
| 2 | A | guard | 147 | 31 | 1.645 |
| 3 | B | agent | 744 | 78 | 5.559 |
| 4 | B | guard | 843 | 27 | 0.999 |
| 5 | A | agent | 43 | 8 | 0.516 |
| 6 | A | guard | 147 | 31 | 1.034 |

Model-load times were 273.607 s (agent) and 31.849 s (guard).  A-response
hashes repeated for both roles.  These timings are instrumentation from one
technical run and must not be pooled with prior stress or pilot measurements.

Ready residency exceeded the declared per-device minimum by observing free
memory deltas of 9.798828 GiB (device 0) and 7.621094 GiB (device 1).  Six
signed recovery samples returned to zero residual on both devices.  Both child
workers were reaped with `TERMINATE/-15`; no graceful exit was observed.  This
does not establish global IPC cleanup or native-generation cancellation.

## Audit result and limits

The worker-produced joined tokenizer/native receipt and two fresh local audits
are byte-identical (SHA
`a8669af992c77045ff97192f396d8440114543f96bfde881c0bef73a551b23dc`).  The
release audit validates source/package/remote identity, native metric streams,
policy/attention joins, tokenizer metadata, Dummy isolation and raw inventory.

It intentionally records `phase5_accepted: false` and makes no claim about
ASR, utility, guard classification quality, cross-model ranking, full-context
KV behavior, runtime A0–A6 integration, grouped Dev validation, or final
thesis results.  Those remain the next gates.
