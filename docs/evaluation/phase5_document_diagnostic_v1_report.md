# Phase 5 — document diagnostic v1

2026-09-14. Status: native version1 COMPLETE, source/artifact audit passed;
guard-path objective failed. Phase 5 is not accepted.

## Purpose and frozen scope

[Preregistration](../architecture/phase5_document_diagnostic_v1_contract.md):
one public synthetic CDOC_034 lookup at each A0–A6, fixed order, fresh workers.
Successful path coverage needs actual Broker document execution and uncached
successful guard PRE/POST at A2–A6. A correct guessed answer is not coverage.
No benchmark task/private oracle/Test payload was read. No semantic retry of
the historical calculator pilot. Source `54aa3eca04ad31618e82bd97b2bce4261e2008c9`.

Agent Qwen2.5-7B-Instruct and guard Qwen2.5-1.5B-Instruct retain immutable native
shutdown v2 identities. Agent startup/call 1200/180s; guard 120/120s; normal stop
2s, terminate 0.5s, kill 1s. Temperature 0, seed 42; agent/guard caps 512/128.
These are configured limits, not measured latency or allocation.

## Pre-inference implementation finding

Draft01 CPU output `results/phase5_document_devcheck01` revealed that scope v2
does not recognize the clean environment's CDOC namespace. A4–A6 denied the
legitimate read. Those outputs remain development history, not acceptance.
Scope v3 adds exact bounded CDOC IDs without aliasing them to DOC, preserves
quoted/conditional/negative grant rejection, source identity matching and v2
table/column pairs. Runtime v8 substitutes only this per-run scope dependency;
transport remains v3. Frozen old sources and receipts were not edited.

## CPU package evidence

- 49 focused tests pass (7.25s in CPU01): document path, identity/catalog rejects,
  read-only resume, scope negatives, overlay/remote metadata mutations and
  coverage negatives (guess/blocked/error/cached/missing guard stage).
- Exact preflight01 passed both isolated archive and expanded mounts. Per
  layout: eight tool schemas/recovery, 21 public Dummy tasks/missing-only resume,
  seven synthetic document runs, seven successful doc_read and ten guard calls.
- All 110 selected source and 430 raw file hashes matched after preflight.
  102-file overlay; no local torch/transformers/model loading. The new native
  audit CLI imported via --help; the ordinary synthetic joined CLI executed.
  This does not constitute a full native audit of the new run before inference.
- [Selected preflight receipt](../../experiments/manifests/phase5_document_probe_v1_preflight01.json),
  SHA-256 `419c4b28f7d6f79120c3e8bccbec8345dfac7062818020a7208546058e926c0e`.
- Full QA: **2,813 passed, 1 optional-native-tqdm skipped**, 693.77s (process wall
  694.73s). Setup/Ruff/mypy357files/knowledge pass. 501 source/158 raw hashes
  reverified, 169 tracked data hashes unchanged, parent622 entries preserved.
  Seven actual synthetic runtime receipts passed independent lifecycle joins.
  [CPU01 receipt](../../experiments/manifests/phase5_document_probe_v1_cpu01.json),
  SHA-256 `159b2269d234b89530177094498085364af9a52d1bba3fb30f09b6eb431e9196`.
  Output `results/phase5_document_probe_v1_cpu01` is complete; do not rerun or
  append. Scan of 434 package/access files against four credential values had
  zero matches. CPU results are synthetic evidence.

## Native execution and access

Confirmed private/offline pinned T4 notebook version1:
`huylmhuhu/react-vn-document-runtime-v1`, timeout7200s. Source/evidence GitHub
`8836e9c` pushed before submission. [Submission receipt](../../experiments/manifests/phase5_document_gpu_v1_submission01.json).
[Read-only access snapshot](../../experiments/manifests/phase5_document_access01.json)
confirms shared Dataset ready/private/v1, model-version listing access, and
new kernel name not found under mine search; quota snapshot is not reservation.
Record the actual URL/version in [Kaggle directory](../../knowledge/kaggle_resources.md)
after real submission, and authenticate downloaded source/metadata/raw before
reporting native counts, timing, tokens or lifecycle.

## Audited native result

[Kaggle notebook v1](https://www.kaggle.com/code/huylmhuhu/react-vn-document-runtime-v1)
is COMPLETE. [Release audit](../../experiments/manifests/phase5_document_gpu_v1_audit01.json)
SHA-256 `ea799c3c1ab4afe8d2efa48be651241bd5f02686043c4caa7b3171f58a470228`;
[terminal summary](../../experiments/manifests/phase5_document_gpu_v1_terminal01.json).
261 raw and two remote files authenticated; repeated local native joins equal
the canonical remote report. Raw hashes independently rechecked. Secret scan:
263 files/four credential values, zero matches. No semantic retry or Test run.

All seven levels performed one successful CDOC_034 read. A0/A1 completed and
returned the stated D305 location; A2–A6 ended in model_error with no final
answer. Five native guard generations occurred, but **all five PRE classifications
were INVALID_OUTPUT**. All five POST classifications were BACKEND_FAILURE with
zero native attempts. Thus the predeclared successful guard PRE/POST objective
failed in all five guard-enabled levels; this is not 7/7 utility or a guard score.

Observed causal sequence, joined with frozen source: ModelGuard rejects the
response at JSON/schema validation; WarmModelGuard retires on error; the paired
role adapter closes the entire pair. The local read remains permitted under
the bounded non-external fallback, then POST and the next agent request encounter
the retired pair. This explains the terminal model_error without implying GPU
OOM or failed native generation. Exact malformed guard text was intentionally
not retained by the loader, so its particular JSON/schema violation cannot be
recovered or attributed to a guessed field. No output-token-cap tuning or model
replacement has been performed on these outcomes.

There were 14 native calls: agent nine calls, 9,130 input/206 output tokens,
24.572s total generate time; guard five calls, 910 input/155 output tokens,
7.705s total generate time. Per-call agent wall times ranged 2.497–3.567s and
guard 1.500–1.679s. Total task times (including startup and cleanup, excluding
the later recovery sampling) were A0 318.143s, A1 144.421s, A2 176.669s,
A3 176.503s, A4 174.178s, A5 174.231s, A6 176.061s. These are single fixed-order
diagnostic observations; disk/hash/load caching and unequal paths prevent a
controlled latency ranking or statistical performance claim.
The five guard inputs are the same PRE request across five levels, not five
independent sampled tasks; do not turn 5/5 INVALID_OUTPUT into a population rate.

Eight workers (A3–A6 pairs) had observed stop/serve-return, zero exit and reaping:
GRACEFUL. Four (A0/A1 agents and A2 pair) had observed stop/serve-return but
required TERMINATE/-15 after the normal deadline. All 12 were reaped. All seven
levels recovered: 42 two-device samples, 84 device observations, zero residual
bytes relative to baseline. Partial graceful success does not close the general
native lifecycle gate or establish global IPC cleanup.

Raw: `results/phase5_document_gpu_v1_output01`; pulled source/metadata:
`results/phase5_document_gpu_v1_remote01`. Both are closed, immutable outputs.
Repeat the read-only audit into a new output (no model loading):

```sh
.venv/bin/python scripts/audit_phase5_document_runtime_gpu.py \
  --raw results/phase5_document_gpu_v1_output01 \
  --remote results/phase5_document_gpu_v1_remote01 \
  --preflight experiments/manifests/phase5_document_probe_v1_preflight01.json \
  --output results/phase5_document_gpu_v1_reaudit02.json
```

## Limits and next acceptance work

This is a technical diagnostic, not ASR/FPR, model comparison, statistical
utility estimate, or proof of all cleanup failures. Native sidecar joins bind
PID/role/order/config/timing, not an independent native request-content hash.
Recovered VRAM and observed graceful process shutdown are separate outcomes.
Guard quality, grouped Dev differential coverage, broader semantic coverage and
formal freeze remain open. Phase 5 is not accepted; no Phase 6/7/Test execution.

Additional pre-native inspection: the inherited rejection cue `cho` also matches
the legitimate phrase `cho biết` in this diagnostic instruction, so its scope
anchors are empty (`explicit_scope=false`). The trusted public first read is
allowed under the frozen no-scope-trigger behavior after CDOC shape/source
resolution was repaired. The diagnostic therefore does not demonstrate explicit
user-bound resource authorization. Preserve this lexical limitation for broader
public/Dev scope validation; do not change the already packaged instruction or
policy in the middle of this run. Unit tests with affirmative `Đọc CDOC_034`
exercise exact anchors separately.
