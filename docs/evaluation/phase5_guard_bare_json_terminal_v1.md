# Phase 5 — bare-JSON candidate: terminal result and recovered audit

2026-09-16 (Asia/Ho_Chi_Minh). This diagnostic is closed; Phase 5 is not accepted.

## Outcome

The prompt-only framing instruction did **not improve JSON validity on these
four diagnostic tasks**. All four retained `model_error`. Do not retry them or
reinterpret a successful audit as model success. The notebook itself remains
`ERROR`: inference checkpoints were complete, but the final audit CLI exited 2
because `--condition` was missing. Saved inference was audited locally with no
new model loading, GPU execution, Test access or private ground truth.

| Observable measure | Observer baseline | Bare-JSON candidate |
|---|---:|---:|
| Tasks / model_error | 4 / 4 | 4 / 4 |
| Tool calls | 4 | 4 |
| Returned guard responses / valid | 6 / 2 | 6 / 2 |
| Fenced JSON syntax errors | 4 | 4 |
| Additional POST backend failures, no response | 2 | 2 |
| Workers reaped / graceful / terminated | 8 / 5 / 3 | 8 / 7 / 1 |
| Tasks with recovered GPU memory | 4 | 4 |
| Sum of task elapsed seconds | 861.990 | 984.907 |
| Sum of model startup seconds | 825.994 | 951.355 |

Candidate timing, from joined native calls (not notebook wall-clock time):

| Role | Calls | Input / output tokens | Generation seconds | Output tokens/s |
|---|---:|---:|---:|---:|
| Agent Qwen2.5-7B | 4 | 3930 / 82 | 13.817 | 5.935 |
| Guard Qwen2.5-1.5B | 6 | 1218 / 136 | 6.724 | 20.225 |

The two valid responses were CALC PRE; the four syntax failures were CALC POST
and DOC PRE. Framing categories come from hash-bound telemetry, not retained
raw guard text. CALC_A2's guard required termination despite STOP acknowledgement
and serve-loop return. Fewer terminations do not establish a prompt-caused
lifecycle improvement. Four diagnostic tasks are not independent quality
samples: no significance, ASR/FPR, semantic utility or broad speedup claim.

Baseline: [audited observer report](phase5_observer_native_v2_run.md).
Candidate: [descriptive summary](../../experiments/manifests/phase5_guard_bare_json_recovered_summary01.json).

## Identity, resources and evidence

- Actual=requested notebook: [huylmhuhu/react-vn-guard-bare-json-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-bare-json-v1),
  version 1, kernel ID 134511636; private, offline, T4×2, timeout 14,400 seconds.
- Dataset: [react-vn-guard15-probe-data-v1](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1),
  version 1; private. GitHub collaboration does not grant Kaggle access.
- Source: `f7492fae80876891237fcd37084e79ed5af60a2e`; submission evidence
  commit `1f630ce`. The source/package and original failure remain immutable.
- [Preflight01](../../experiments/manifests/phase5_guard_bare_json_package_v1_preflight01.json),
  [submission](../../experiments/manifests/phase5_guard_bare_json_submission01.json),
  [terminal identity observation](../../experiments/manifests/phase5_guard_bare_json_terminal01.json)
  at 2026-09-15 17:10:52 UTC: version 1, private, `ERROR`, downloaded source hash matches.
- [Recovered native release audit](../../experiments/manifests/phase5_guard_bare_json_recovered_audit01.json):
  155 committed source pins, 157 raw files and 2 remote files verified.
  Archive bytes, embedded source, bootstrap, model inventory/snapshot, tokenizers,
  publisher policy, attention, native timing, witnesses and checkpoint coverage
  are checked. `source_authenticated=true` does not change terminal status.
- Raw: `results/phase5_guard_bare_json_terminal_error01/raw`; remote metadata and
  observation: `results/phase5_guard_bare_json_terminal04`. Two fresh audit outputs
  `results/phase5_guard_bare_json_recovery_audit01` and `..._audit02` have
  byte-identical audit and summary JSON. No downloaded code is executed.

## Audit repair and preflight lesson

The old candidate audit accepted native flags but ran only CPU-style checkpoint
checks and labelled inference count zero. Merely defaulting `--condition` would
not have fixed this validation gap. The current CLI selects native validation
from the recorded backend, requires model/tokenizer metadata for HF, and rejects
native inputs in CPU mode. CPU auditing requires the exact four-task identity.
New tests cover missing tasks, wrong identities, native dispatch and literal-only
inspection of downloaded launchers.

Recovery authenticates all submitted source bytes against their Git commit.
Only two historically changed entrypoints (package preparer and old audit CLI)
are exempt from *current working-tree* equality; neither is executed in recovery.
All reused source dependencies must still match. The added recovery/native-audit
modules are local post-processing, not code claimed to have run on Kaggle.

Preflight01/02 are retained as historical CPU package evidence, **not successful
native end-to-end acceptance**. The prepared `...bare-json-v2` identity has not
been submitted and must not be submitted to rerun these completed inferences.
Future packages need tests of the actual launcher audit invocation with both
CPU and native-shaped saved fixtures; `--help` alone is insufficient.

Verification: [QA receipt](../../experiments/manifests/phase5_guard_bare_json_recovered_qa01.json).
87 focused tests passed in 49.99 seconds; setup, Ruff and mypy (418 source files)
passed. Knowledge links/handoff structure passed after correcting the required
section headings. All 175 frozen baseline source pins remain unchanged; 184
evidence/source files scanned against configured credential values, zero matches.
Full repository pytest was not run because it includes Test-assigned authoring
fixtures. No model inference or Test/private-GT evaluation occurred in recovery.

## Next concrete work

Phase 5 remains 4/7 acceptance groups (about 57%, not elapsed effort). Close the
structured-output gate through a separately versioned, preregistered candidate;
first evaluate an explicit constrained-output design with synthetic CPU controls
while keeping the strict parser and failure retention. Do not select/tune on
held-out Test or silently adopt JSON repair. Investigate shutdown wait behavior
in a separate synthetic lifecycle study; do not combine prompt and timeout
changes. Representative benign utility, differential Dev evidence and formal
freeze remain open in the [DoD queue](../../knowledge/phase5_remaining.md).
