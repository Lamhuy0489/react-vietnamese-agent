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

**ERROR**, observed2026-09-16 07:58:28UTC; raw downloaded and preserved.
Actual=requested notebook
[huylmhuhu/react-vn-constrained-generate-cpu-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-constrained-generate-cpu-v1),
v1/ID134578096, private/offline/CPU, no external model mounts, timeout3600s.
[Submission receipt](../../experiments/manifests/phase5_constrained_generate_cpu_submission01.json).
Remote source matches source999d658; GitHub evidencecb1b7f8. Existing private
Dataset `huylmhuhu/react-vn-guard15-probe-data-v1` confirmedready/v1 before push.
First case `success01` failed before chain admission: generate1/processors0/
callbacks0, hooks restored, no completed cases. No native-success/quality claim.
[Failure audit](../../experiments/manifests/phase5_constrained_generate_cpu_failure01.json)
authenticates141source pins against Git, remote source/settings and12raw/2remote
files; scan14files/0credentials. Raw: `results/phase5_constrained_generate_monitor02`.

[Static policy diagnosis](../../experiments/manifests/phase5_constrained_policy_diagnosis01.json)
reproduces six integer/float type mismatches between historical selected config
and pinned native defaults. The original remote inner message was sanitized;
this is a definite admission defect consistent with that boundary, not a complete
remote traceback. New typed configv2 is selected; one corrected CPU technical
schedule uses a new source/package/notebook, not a semantic retry. See deviation
in the contract. No second submission yet at this report revision.
Do not interpret local metadata rehearsal as actual GenerationMixin execution.

## Remaining

Terminal source/version/raw audit after the CPU run; host security classifier/
cache identity and benchmark auditor integration; then a separately admitted GPU
diagnostic. The tiny CPU control does not validate28-layer CUDA attention or
production1.5B guard quality/latency. Phase5 remains4/7≈57% acceptance groups.
No model semantic retries or baseline changes; user Phase6–9/report files untouched.
