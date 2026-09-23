# Phase 5 Dev32 v2 guard-exit diagnostic protocol

Declared 2026-09-23 before inspecting the complete per-task lifecycle distribution.
Use the authenticated immutable Dev32 v2 terminal audit and its 32 public Dev
task receipts. Do not load benchmark Test, private oracle or model weights;
do not rerun inference. Verify raw inventory, task keys and joins first.

For every task compare the pair snapshot lifecycle with observed exit milestones
for both roles. Record method, exit code, reaped state, STOP/serve/finalizer/thread
milestones, non-daemon thread counts, configured graceful timeout, and guard
request count. Preserve all failures; no selective exclusions or changed timeout
based on the observed first task. Summarize counts and the anomalous task using
metadata only, with no prompt, answer, source value, or credential in the report.

Classification is limited to the observation boundary. `serve_returned` and
`finalizers_return` do not by themselves prove the OS process exited before the
grace deadline. A reaped `TERMINATE/-15` is not a graceful exit, even with a
completed task and no pending handle. This diagnostic may locate the delay but
cannot establish its underlying CUDA/Python cause without a separate prospective
instrumented experiment. Phase 5 lifecycle acceptance remains open.
