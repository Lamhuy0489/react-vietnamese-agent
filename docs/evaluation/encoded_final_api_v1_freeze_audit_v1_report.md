# Source-drift audit for `encoded_final_api_v1`

This is a read-only audit of the 2026-09-28 encoded FINAL correction. It does
not contact either Kaggle endpoint, start a notebook, rerun inference, or
modify the historical run, evaluations, receipt, or session journal. The
machine-side audit record is
[`encoded_final_api_v1_freeze_audit_v1.json`](../../experiments/manifests/encoded_final_api_v1_freeze_audit_v1.json).

At the audit timestamp (2026-09-29), the historical evidence is re-auditable:

- all 94 receipt artifact hashes match, including the raw run manifest and the
  two saved evaluations;
- all 32 receipt journal hashes match;
- all 336 source paths bound by the raw run manifest match the current bytes;
- the protocol and saved evaluator hashes match the raw manifest;
- the two saved evaluations are identical; and
- invoking the saved evaluator against the raw checkpoints reproduces the
  saved evaluation object.

The resulting record has `can_reaudit_old_evidence=true`, zero parent artifact,
journal, and source mismatches, and `network_or_inference_run=false`. This
means the old result can be independently checked from the recorded local
inputs under the exact source bytes currently present. It does not promote the
experiment or establish new model quality.

The current working tree contains five source paths outside the parent run's
binding: the v1 evaluator, two v2 runner/evaluator candidates, and two
authorization candidate modules. They are recorded in the audit JSON and were
not retroactively included in the old result. The source state is therefore a
working-tree audit, not a Git commit or release freeze; any modification to a
parent-bound path, historical artifact, journal record, protocol, or evaluator
requires a new audit and invalidates this re-audit result. The audit record has
its own tamper-evident `audit_record_sha256` field.

The historical scope remains controlled Replay proposals plus native guard,
not a Qwen task benchmark. Test inputs and private oracles remain sealed;
`phase5_accepted` remains false.
