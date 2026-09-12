# Ordinary policy + attention pair composition v1

New lazy builder `policy_pair(agent_factory, guard_factory, config, attention,
policy)` validates fresh disjoint roots and pinned role identities before
allocating transport. Refuse prewrapped ordinary factories. Native factory
closures remain caller-owned; exact native loader admission still happens in
the unchanged EfficientRequestFactory inside each child.

The chain is ModelPair's ReadyFactory → ThreadProgressFactory →
RequestPolicyFactory → EfficientRequestFactory → original native factory.
Progress precedes native loading. READY bypasses both request wrappers and
does not count as model generation. Request policy and attention retain one
index per original generate. Errors retire wrappers; frozen ModelPair owns
sibling cleanup and refuses retry. Both roles load: not A0/A1 ownership.

CPU rehearsal reuses frozen request-pair controls through a scoped HOST-only
builder substitution restored in finally; no frozen source edits. Explicit
picklable synthetic factories prepare native-shaped placeholders, fake config
resolution/length and shape-only attention. Native tqdm and daemon spawn are
real. No model constructor, native Torch/Transformers, GPU, Test data or model
quality/performance measurement. Synthetic durations are never native timings.

Cases: A/B/A input1/4096/1 and output1/3/1 in both workers; reversed wrapper order
fails startup; injected errors on each role preserve policy/attention partials,
restore hooks, close siblings and reject retries. Join completed policy with
attention/native-shaped metric records, exact request coverage and worker PID.
Verify idle sibling readiness creates no policy requests. Preserve all raw
snapshots and partials. Reaping, graceful exit and GPU cleanup remain distinct.

Remaining before model GPU adoption: repeated-request native entry point,
publisher/tokenizer/source/loader/memory authentication, supervisor-bound audit
and exact package preflight. Then agent-only A0/A1 task owner and versioned
runtime A0–A6 routing/differential/lifecycle/grouped Dev gates. No Phase5 closure.
