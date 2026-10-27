# Source-drift audit v3 for `encoded_final_api_v1`

This is a read-only re-audit of the historical 2026-09-28 encoded FINAL
correction after the hardened v2 evaluator added manifest/conditions symlink
checks. It did not contact either Kaggle endpoint, start a notebook, rerun
inference, or modify the historical run, evaluations, receipt, or journal.

The signed record is
[`encoded_final_api_v1_freeze_audit_v3.json`](../../experiments/manifests/encoded_final_api_v1_freeze_audit_v3.json).
It reports zero mismatches across the 94 receipt artifacts, 32 journal
records, and all 336 source paths bound by the raw run manifest. The protocol
and saved evaluator match the raw manifest; evaluation01 and evaluation02 are
byte-identical; and running the saved evaluator against the raw checkpoints
reproduces the saved evaluation object. Therefore
`re_audit.can_reaudit_old_evidence=true` for this audit.

Five current source paths are outside the parent binding: the v1 evaluator,
the two hardened v2 runner/evaluator files, and the two authorization candidate
modules. They are recorded as additions and were not retroactively included in
the historical result. This is a working-tree integrity audit, not a Git
release freeze. Any later change to a parent-bound source, protocol, evaluator,
artifact, or journal requires another audit. `phase5_accepted` remains false;
the historical scope is controlled Replay proposals plus native guard, not a
Qwen task benchmark.
