# Ordinary A/B/A pair — native T4×2 evidence

Kernel `huylmhuhu/react-vn-ordinary-pair-t4x2-v1` version 1 completed on
2026-09-12 with the explicit Kaggle `NvidiaTeslaT4` machine shape.  The private
offline Dataset and pinned model mounts were used only by Kaggle; no credential,
Test payload or private ground truth is stored here.

The exact package is bound to source commit
`a412e571a6fba89103b93c55eb830106bede2d01`, preflight receipt SHA
`080d7370f937bb5bb6b466a393b31ebc12ffe210325763d2a320b91332091d9d`, and
wrapper SHA `1429eb99ade62c555378c44c1559e61049519f171f0f62fbc8eedf510d49cf45`.
Remote metadata and code were pulled back and match the package identity.  The
release audit is [phase5_ordinary_pair_t4x2_v1_audit01.json](../experiments/manifests/phase5_ordinary_pair_t4x2_v1_audit01.json).

## Measured technical result

- The frozen 21-task public Dummy/resume check completed with 21/21 terminal
  tasks and zero model errors before the native probe.
- The native pair loaded Qwen 7B agent and Qwen 1.5B guard once each, then
  returned all six ordinary requests in A/B/A order (three per role).  Native
  generation calls counted from the two metric streams: 6; no semantic retry.
- Two Tesla T4 devices were observed.  Ready-minus-baseline free-memory deltas
  were 9.798828 GiB (device 0) and 7.621094 GiB (device 1).  Six recovery
  samples returned to signed zero residual on both devices.
- Agent load/generation seconds were 273.607 / 2.245, 5.559, 0.516; guard
  load/generation seconds were 31.849 / 1.645, 0.999, 1.034.  These are one
  instrumented technical run, not a speed ranking.
- A responses matched by SHA for both roles.  Both workers were reaped with
  `TERMINATE/-15`; graceful exit was not observed and is reported separately.

The worker's joined native/policy/attention audit is valid, its tokenizer IDs
are authenticated from the public tokenizer bytes, and two fresh local audits
are byte-identical to the remote receipt (SHA
`a8669af992c77045ff97192f396d8440114543f96bfde881c0bef73a551b23dc`).  The
release audit itself is deterministic and reports `phase5_accepted: false` by
design: this is transport/residency/native execution evidence only, not ASR,
utility, guard quality, full-context/KV, global IPC cleanup, or runtime A0–A6
acceptance.

Raw output is retained locally at
`results/phase5_ordinary_pair_t4x2_v1_remote01` and is hash-bound (132 files);
the pulled remote source has two hash-bound files.  The next work remains
versioned runtime A0–A6 integration, A4 processing-scope/private-final gates,
and grouped Dev differential/model/freeze validation.  Do not run held-out Test
or use this six-call probe to tune policy.
