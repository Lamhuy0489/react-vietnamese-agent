# Phase5 — clause Dev32 runner and checkpoint contract

2026-09-22. Development-only integration of the paired v12 candidate. This does
not authorize native inference, change the benchmark, or accept Phase5.

## Fixed inputs and interfaces

`clause_dev_identity_v1.identity` derives its schedule from the frozen grouped
public-Dev selector: eight paired families, 16 fixtures, A2/A6, four tasks per
shard and 32 tasks overall. Selection is not based on model outcomes. Original
input/environment/model/generation/runtime/recovery settings remain bound;
the historical 112-task schedule and outputs are unchanged.

Identity `clause_dev32_v1` additionally pins the candidate execution sources,
clause anchors v3, scope v5, origin v3, constrained guard prompt/language/cache
policy, ExitPair configuration and recorded interpreter. Working-tree hashes
are distinct from the Git base; the base does not contain uncommitted files.

`clause_dev_runner_v1.run` currently admits only the explicit synthetic backend.
An HF request fails before creating output. Each task receives fresh state.
Completed checkpoints are audited, never regenerated. Resume accepts only a
complete valid prefix and executes missing tasks; semantic failures are retained.
Unexpected files, partial checkpoints, changed identities or raw hashes fail closed.

## Evidence binding

`clause_dev_checkpoint_v1` composes the frozen grouped checkpoint validator with
candidate raw-authority/origin replay and constrained/exit evidence joins. It
validates worker closure and recovery observations. Cross-host audits use the
interpreter recorded by the run, not the auditor's local default.

`clause_dev_native_audit_v1` adapts native artifact checks to this identity. It
joins completed constrained calls to native guard call indices and input/output
token counts. Unverified/partial calls must not enter the native timing sample.
This is an artifact auditor, **not** model-source or remote-release authentication.
Mocked native records and a lazy native factory test do not prove pretrained
execution. Both native-release authentication and dispatch remain false.

## CPU acceptance and native gate

CPU evidence requires all eight shards, unique 32-task coverage, two read-only
audits, immutable raw/source hashes and unchanged complete-resume. Tests cover
missing-only resume, deliberate backend errors, identity/raw corruption,
symlinks, interpreter binding and native call-count joins.

The synthetic agent triggers each fixture then emits a scripted final answer;
it does not demonstrate task utility, attack resistance or model reasoning.
Recovery readings are synthetic, not GPU measurements. No ASR/FPR is computed.

Next: separate source-authenticated native launcher/release gate and exact
archive/expanded Kaggle package rehearsal, then a necessary committed source
freeze and one declared Dev32 submission. Preserve old worker sources, errors,
denials and missing-only resume. Never promote these CPU counts to native quality
or lifecycle reliability. Held-out Test and private evaluator GT stay inaccessible.
