# Agent runtime admission and HF loader v1 — CPU engineering evidence

Source commit `fa894c4`; [contract](../architecture/phase5_agent_hf_v1_contract.md).
No new Kaggle submission, real model load, GPU inference or local weights download.
This does not close Phase5 or establish combined GPU fit or guard quality.

## Verified scope

The versioned loader rehashes the live mount before importing model libraries and
after loading. Required runtime files must match the frozen publisher inventory;
only the exact documentation-only README mismatch from the earlier CPU diagnostic
is permitted. The original full-inventory rejection and source remain unchanged.
Recorded-scan classification is not sufficient authorization to load a model.

CPU fixture tests cover bounded safetensors headers/index coverage,339expected
parameter shapes (7,615,616,512parameters), every runtime/document file changed,
corrupt pin, links, extras, missing files, duplicate JSON keys, shape/dtype/offset
errors and path traversal. Actual model headers have not been inspected in this
milestone; the existing Kaggle evidence authenticates runtime bytes only.

Fake GPU/library tests verify exact20/8layer mapping and12/7GiB agent allocator
ceilings set before loading, native local-only FP16 loading, tensor placement,
fresh message/generation state,1–4096input tokens,512output budget and text-free
metrics. Tests reject CPU offload, busy allocator, unsupported GPU/config,
over-budget observations, OOM, bad context, reasoning markers and metrics failure.
The adapter retires after request errors. A dedicated process supervisor still
must provide deadlines, termination/reaping and resource-recovery evidence.

Native Qwen2Config's inert rope_scaling=None is handled at the post-load boundary
without relaxing raw publisher-config validation. Regression tests reject active
overrides; the frozen geometry validator is not edited.

## Reproduction and QA

87new targeted tests passed:43runtime-input and44adapter. Setup/Ruff/mypy221files
and knowledge-check pass. Final full suite:1,274passed/278.23s, JUnit XML at
`results/phase5_agent_loader_v1_final02_pytest.xml`. The initial1269test/281,10s run began before final config
handling changes and is not final-source QA. A subsequent monitored run lost its
process handle before completion was retrieved; no pass count is inferred from it.
The final rerun writes JUnit XML for durable test counts, failures and elapsed time.

Two clean-source CPU reproductions under `results/phase5_agent_loader_v1_validation01`
and `validation02` are byte-identical. They verify six source hashes, saved public
scan identity and parameter arithmetic,134frozen guard-source hashes, plus sealed
benchmark integrity by hash only. They do not load a model or read held-out payloads.
[Selected receipt](../../experiments/manifests/phase5_agent_loader_v1_validation01.json).

## Remaining gates

Supervised combined agent/guard residency, context and cancellation protocol;
exact archive/expanded/PAX worker preflight with eight tools and21Dummy/resume;
private pinned inputs, dependency image and quota check; first combined GPU run
and artifact audit. Separately: grouped Dev/guard choice, broader A4 scope and
private-record final entitlements. No semantic retries or Phase6/7 transition.
