# Phase5 — constrained worker composition and native generation CPU control

2026-09-16. Source `999d6587923ab66dc717703f27f0f465eb1029ae`.
[Protocol](../architecture/phase5_constrained_policy_v1_contract.md),
[package preflight](../../experiments/manifests/phase5_constrained_generate_cpu_preflight01.json).

## Completed locally

- Worker factory composes constraints around original request-policy and
  attention scopes, preserving agent factory, response observer and host witness.
  Counters align across four layers; failures retire all layers. Snapshot,
  output separation and topology faults are rejected before loading.
- 30 new composition tests;148 focused tests across composition/adapter/policy/
  native topology passed in9.11s. Setup/Ruff/mypy431 pass. Native constructor
  source check now unwraps torch.no_grad after exact SDK bound-method admission.
  Earlier candidate QA did not test that constructor; it is historical evidence.
- Exact package01 passes archive and expanded source/tokenizer layouts in fresh
  offline venvs: eight tool schemas,21Dummy tasks, missing-only resume and native
  launcher metadata-only invocation.141source pins; noTest/privateGT/GPU access.
  Full receipt/raw checks live in `build/kaggle/phase5_constrained_generate_cpu_package01`.

## Native control status

Prepared, not yet submitted at this report revision. Requested notebook:
`huylmhuhu/react-vn-constrained-generate-cpu-v1`. Use private Datasetv1
`huylmhuhu/react-vn-guard15-probe-data-v1`; live access/version must be checked
before push. Four fixed tiny-random-Qwen CPU cases, no pretrained weights.
Do not interpret local metadata rehearsal as actual GenerationMixin execution.

## Remaining

Terminal source/version/raw audit after the CPU run; host security classifier/
cache identity and benchmark auditor integration; then a separately admitted GPU
diagnostic. The tiny CPU control does not validate28-layer CUDA attention or
production1.5B guard quality/latency. Phase5 remains4/7≈57% acceptance groups.
No model semantic retries or baseline changes; user Phase6–9/report files untouched.
