# Phase5 Dev32 Kaggle v1 — authenticated pre-start failure

Observed 2026-09-22 08:39:20 UTC. The private [Kaggle notebook](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1)
version 1 / ID 135340687 ended `ERROR`. Source commit
`5a2352834a791b11824a7c0c69e82f2390a03ca0` and the remote executable
match the submitted package. This is an infrastructure integration failure.

[Submission](../../experiments/manifests/phase5_clause_dev_gpu_submission01.json),
[committed package](../../experiments/manifests/phase5_clause_dev_package_release01.json).
The terminal download is `results/phase5_clause_dev_gpu_monitor01`, with remote
code, before/after version observation and 12 immutable raw files.
[Failure audit](../../experiments/manifests/phase5_clause_dev_gpu_failure_audit01.json)
authenticates the source, version, raw inventory, first-task identity and
traceback. A second independent audit produced identical evidence.

The first task `ATK_CAND_LINKMAIL_PARAPHRASE__A2` created its baseline and
environment copy. The runner then called the native clause runtime with a
`constrained` root supplied by the caller, while the admitted native guard
factory supplied its own root. Python raised `TypeError: ... got multiple values
for keyword argument 'constrained'`. The cleanup recorded recovery samples.
There is no execution trace, checkpoint, worker result or native generation
receipt. Completed/quality-scored tasks: 0/32. This does not establish model
quality or a GPU lifecycle outcome.

The correction is versioned as `clause_dev_dispatch_v2`: its native path lets
the admitted guard factory determine the root; synthetic controls still provide
theirs explicitly. A bounded test reproduces the old TypeError and verifies
the corrected route without loading weights. V1 remains immutable. The only
eligible follow-up scope is the original 32 unexecuted Dev tasks under a new
source/run identity. Do not resume the partial v1 directory or retry semantic
outcomes. No held-out Test or private evaluator ground truth was read.
