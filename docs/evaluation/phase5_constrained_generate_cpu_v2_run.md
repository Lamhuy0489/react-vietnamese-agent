# Phase 5 — native constrained generation CPU v2: COMPLETE

2026-09-16. Native source `b4ae0f7ff8ba698cc09bbd10a08ab4fb9156d2aa`;
auditor source `82985026c6b5302452b1da4efd0ca07a3568932d`.
This closes the bounded CPU GenerationMixin control, not Phase 5 acceptance.

## Run identity and scope

Actual=requested [notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-constrained-generate-cpu-v2),
version 1/ID 134579648; submitted 08:11:54 UTC; COMPLETE first observed
08:16:13 UTC and reauthenticated after download at 08:25:13 UTC.
[Dataset](https://www.kaggle.com/datasets/huylmhuhu/react-vn-guard15-probe-data-v1)
version 1 unchanged; private/offline/CPU, no model mounts, timeout 3600s.
GitHub membership does not confer private Kaggle access; no public-sharing change.

Pinned Transformers 5.5.0 / Torch 2.10.0+cu128, real Qwen tokenizer and actual
GenerationMixin.generate, but four fresh **tiny random** Qwen2 models: hidden 8,
one layer, seed 42, no pretrained weights or GPU. Full architecture is in the
[summary](../../experiments/manifests/phase5_constrained_generate_cpu_summary01.json).
This does not exercise the complete production guard constructor/paired runtime.

## Fixed-schedule results

| Case | Outcome | Forward / callback / output tokens | Seconds |
|---|---|---|---:|
| success01 | Complete admitted JSON + EOS | 28 / 28 / 28 | 0.236173 |
| success02 | Complete admitted JSON + EOS | 28 / 28 / 28 | 0.146198 |
| forced_bos | ValueError before forward/processor admission | 0 / 0 / — | 0.020492 |
| interrupt | KeyboardInterrupt at first forward, propagated | 1 / 0 / — | 0.024273 |

Hooks restored in all cases, Torch threads restored. Success processor chain is
exactly repetition penalty 1.1 then prefix constraint. Both successful token/text
hashes match; failures are deliberate controls, not omitted attempts. These
case durations include scope/control overhead and are not production model
latency, throughput comparisons or statistically estimated performance.

The separate [v1 failure](phase5_constrained_generate_cpu_v1_run.md) is retained.
V2 fixes six int/float mismatches in the expected policy hash, without changing
numerical generation settings, prompt, parser, model selection or thresholds.
No semantic retry, best-of selection, Test or private ground-truth access.

## Verification and artifacts

- [Submission](../../experiments/manifests/phase5_constrained_generate_cpu_submission02.json),
  [terminal identity](../../experiments/manifests/phase5_constrained_generate_cpu_terminal01.json),
  [package preflight](../../experiments/manifests/phase5_constrained_generate_cpu_preflight02.json).
- [Read-only audit](../../experiments/manifests/phase5_constrained_generate_cpu_audit01.json):
  source/settings/bootstrap, tokenizer/wheel, fixed coverage, counters and receipt
  joins checked. Two independently executed audits are byte-identical. Auditor
  authenticates the executing source and reported native checks; it does not
  rerun native libraries or reconstruct token values from hashes.
- [QA](../../experiments/manifests/phase5_constrained_generate_cpu_qa03.json):
  401 focused tests / 21.87s, including 22 new synthetic auditor tests;
  setup/Ruff/mypy 433/knowledge pass. Full pytest excluded to avoid Test-assigned
  authoring fixtures. Active 142, prior-native 86 and baseline 175 source pins intact.
- Raw/remote: `results/phase5_constrained_generate_monitor03`; observation:
  `results/phase5_constrained_generate_terminal04`; repeated audits:
  `results/phase5_constrained_generate_audit02` and `..._audit03`.
  Raw outputs remain untracked/immutable; selected JSON evidence is tracked.
- [Final integrity/secret-exclusion receipt](../../experiments/manifests/phase5_constrained_generate_cpu_close01.json).

## Next gate

No remaining job in this CPU schedule and no new GPU submission. Integrate host
classifier/cache identity and benchmark auditor joins into the paired runtime,
with synthetic negative controls; then exact-package preflight and a separately
frozen GPU diagnostic protocol. Guard 1.5B quality, CUDA behavior, benign utility,
graceful lifecycle and formal freeze remain open. **4/7 ≈ 57% acceptance groups**
is unchanged; passing syntax controls does not certify security effectiveness.
