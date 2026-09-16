# Constrained probe package v1

Scope: package the existing constrained runner/native evidence join for the four
synthetic CALC/DOC × A2/A6 tasks. No change to prompt, weights, policy, parser,
fallback or shutdown deadline. This is a new package identity, not a rerun of the
bare-JSON experiment; Phase 5 acceptance and held-out Test remain unchanged.

## Source identity and commit cadence

`prepare_phase5_constrained_probe_package_v1.py` defaults to committed release
mode: every selected source byte must match HEAD. Unrelated dirty files are not
included. Its explicit `--development` mode allows local working-tree QA before
the owner's single coherent commit. It binds each selected file by SHA-256 and
labels HEAD as `git_base_commit`, not as the source release (`source_commit=null`).
Nested CPU checkpoints retain that base in their legacy source-commit field;
their enclosing working-tree receipt and file hashes are essential context.

Development metadata disables GPU and the generated launcher rejects both
`main()` and direct `native_payload()` invocation before bootstrap, mounts,
dependency installation or model access. It cannot be submitted as a native run.
After a tested source freeze, rebuild in default mode and repeat the exact
preflight. Never amend an experiment source commit. Do not make routine extra
commits just to record a receipt or a status update.

## Exact local preflight

Verify frozen Dataset manifest, baseline source pins and offline progress wheel;
collect the static source dependency closure plus approved public inputs. Reject
test files and data outside the existing approved worker inventory. The launcher
embeds its hash-bound bootstrap and source archive. In fresh offline venvs, test
both archive and expanded source mounts with isolated imports, all eight tools,
21 Dummy tasks and full/missing-only resume, then constrained valid/failure
controls and audits. Recheck source bytes after execution. No pretrained models,
native ML libraries, GPU inference or Test/private ground truth are accessed.

## Native routing and remaining gates

Committed launcher uses the frozen private guard Dataset, exactly one pinned
Qwen2.5 7B Instruct v1 mount, tokenizer collection, the constrained HF runner and
the constrained native auditor, in that order. Hash verification is fail-closed.
Offline/private metadata requests T4; the actual remote identity, version,
privacy, mounts and quota must be checked before submission and after download.

Local `native_submission_ready=true` means the committed package preflight
passed, not remote admission or scientific acceptance. Native evidence remains
unauthenticated until a separate source/version/output release audit succeeds.
Requested notebook: `huylmhuhu/react-vn-constrained-guard-v1`; this document does
not claim that notebook exists. Do not retry terminal semantic failures.
