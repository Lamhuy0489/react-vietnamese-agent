# Request worker v3 — source freeze for owner-operated notebooks

This freeze covers the nine-module inference worker, deterministic package
builder, notebook exporter and their focused tests. It does not include the
unfinished host runner, runtime experiments or research acceptance changes.
Model roles remain Qwen3-8B task agent and Llama3.2-3B-Instruct guard.

The worker authenticates requests, binds each boot instance, records durable
content hashes, and rejects reuse of request IDs with changed inputs. Results
are bounded and never evicted into accidental re-execution. A cancel signal
remains pending until the engine returns and device synchronization completes.
CPU tests do not establish actual native GPU cleanup or remote availability.

Packages embed exactly nine source modules in the script shipped to Kaggle.
Explicit owner names affect notebook metadata only; no account credentials are
read by preparation/export and no notebook is submitted. Notebook code cells
match the preflighted script bytes; ZIP exports exclude the discovery private
key and contain only the notebook, metadata and README. Git freeze comparison
checks bytes, including trailing newlines.

Validation:59 worker/package/export tests plus12 loopback HTTP tests passed;
exact script-only/expanded package preflight4/4; setup, Ruff and mypy passed.
The whole repository pytest suite was not rerun for this bounded source freeze.
The working tree contains other unfinished work not part of this commit.
[Source hashes and QA](../../experiments/manifests/request_worker_v3_source_freeze_20261001.json).

After this source commit is pushed, create a fresh package with its full SHA,
run preflight on that exact package, then export owner notebooks. Each owner
operates their own account within its permitted allocation. Do not cycle account
credentials to bypass exhausted quota. Keep notebooks private, attach the exact
model version, enable T4x2 and Internet, and start once. Local discovery must
verify the authenticated boot/source/model identity before any Dev inference.
No notebook URL, READY state, API key, native quality or Phase5 acceptance is
claimed by this source freeze.
