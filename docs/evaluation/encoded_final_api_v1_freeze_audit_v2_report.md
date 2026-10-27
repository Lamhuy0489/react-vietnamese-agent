# Source-drift audit v2 for `encoded_final_api_v1`

This versioned record supersedes the development-time v1 audit artifact after
the audit script's typing and lint fixes. It is still a read-only audit of the
historical 2026-09-28 encoded FINAL correction. The script did not contact a
Kaggle endpoint, start a notebook, rerun inference, or modify the historical
run, evaluations, receipt, or session journal.

The signed record is
[`encoded_final_api_v1_freeze_audit_v2.json`](../../experiments/manifests/encoded_final_api_v1_freeze_audit_v2.json).
Its `audit_script_sha256` binds the exact current audit script, and
`audit_record_sha256` makes the JSON record tamper evident.

The audit found zero mismatches across the 94 receipt artifacts, 32 receipt
journal records, and all 336 source paths bound by the raw run manifest. The
protocol and saved evaluator match the raw manifest. The two saved evaluations
are identical, and running that evaluator against the raw checkpoints
reproduces the saved evaluation object. Therefore
`re_audit.can_reaudit_old_evidence=true` at this timestamp.

The current working tree has five additional source paths outside the parent
binding: the v1 evaluator, two v2 runner/evaluator candidates, and two
authorization candidate modules. They are listed in the JSON and were not
retroactively included in the historical result. The record is a working-tree
audit rather than a committed release freeze; a future change to any
parent-bound source, protocol, evaluator, artifact, or journal file requires a
new audit. `phase5_accepted` remains false, and the historical scope remains
controlled Replay proposals plus native guard, not a Qwen benchmark.
