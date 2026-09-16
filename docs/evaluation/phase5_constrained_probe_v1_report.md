# Phase 5 — constrained runner and native evidence join

2026-09-16. [Contract](../architecture/phase5_constrained_probe_v1_contract.md).
This closes the bounded runner/checkpoint/native-auditor implementation step,
not exact Kaggle packaging or production guard quality.

## Delivered

- New candidate identity and fixed CALC/DOC × A2/A6 schedule; explicit stub and HF
  entry points, no native output injection or native-to-stub fallback.
- Hash-bound checkpoints revalidate every existing task before missing work starts.
  Terminal semantic errors remain terminal; partial/corrupt attempts cannot be
  silently rerun. Prompt/model/parser/fallback/shutdown settings are unchanged.
- Native auditor reuses load/tokenizer/publisher/policy/attention/HF metrics,
  lifecycle and recovery validators, then joins constrained guard input/output
  token counts to the same indexed native calls. Request/PID/hash/response witness
  joins are inherited from the constrained runtime auditor.
- Failed/partial roles contribute no unjoined timing/throughput denominator.
  A valid artifact audit does not authenticate source/model mounts or prove
  semantic/security quality; those release gates remain explicit.
- Run, audit and local-control CLIs are ready. The control checker is **not** an
  exact archive/expanded package rehearsal; no new notebook has been submitted.

## Local controls and verification

32 new tests passed / 15.50s in the first focused run: explicit mocked native
boundary/count/denominator checks and real spawned synthetic runner/resume checks.
Neither fixture category runs Transformers or loads pretrained weights.

Retained controls: `results/phase5_constrained_probe_cpu_controls02`.
Four normal cases completed; four deliberate backend failures remain model_error.
Completed resume is immutable; missing-only resume adds one task per condition
while preserving six copied checkpoints: ten fresh synthetic task executions total.
No inference retry of semantic model failures or access to benchmark Test/private GT.
Two independent valid-condition audits are byte-identical; failure-condition
audit passes without converting errors into successful completions.

These are pre-commit development controls. The identity's source_commit field
names Git base `e655658284e48b4409d5d00ac1eee8116ccfa6c5`; its execution-source
hashes bind the added working-tree code. It is **not** a runnable GPU release
commit claim. QA records this distinction so one final commit can group tested
implementation and evidence, as requested by the owner.

Excluded history: `results/phase5_constrained_probe_cpu_controls01` used an
incorrect manually supplied base SHA. Keep it unchanged, do not select it as
provenance-valid evidence. Controls02 corrects the label with no native/model run.

Final [QA receipt](../../experiments/manifests/phase5_constrained_probe_cpu_qa01.json):
**480 focused tests / 42.60s + 105 integration tests / 112.49s passed**;
setup/Ruff/mypy 443/knowledge/diff checks pass. Active 142, prior-native 86 and
baseline 175 source pins remain unchanged. Full repository pytest excluded
because Test-assigned authoring fixtures must stay sealed.
Raw logs: `results/phase5_constrained_probe_cpu_qa01`.
[Control integrity and secret scan](../../experiments/manifests/phase5_constrained_probe_cpu_close01.json)
bind the retained control tree, source hashes and repeated read-only audits.

## Next gate

Prepare the candidate notebook/bootstrap and exact archive plus generated-expanded
source package from the tested committed source. Rehearse in fresh offline venvs:
eight tools, 21 public Dummy tasks, the new controls and missing-only resume.
Authenticate package, account/quota and private model/Dataset mounts before one
new GPU submission. Record actual notebook/version after submission, not before.

Native GPU behavior, guard quality, benign utility, graceful lifecycle and formal
freeze remain open. Phase 5 stays **4/7 ≈ 57% acceptance groups**. No new Kaggle
resource, native run, Test access or alteration of historical results in this step.
