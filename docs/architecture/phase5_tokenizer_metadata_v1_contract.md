# Phase 5 tokenizer metadata admission v1

Scope: authenticate public tokenizer configuration for the fixed Qwen2.5 7B
agent and 1.5B guard, then derive expected special-token IDs for the ordinary
six-request artifact auditor. No runtime, decoding, benchmark or Test changes.

## Inputs and authority

Both pinned upstream revisions have the same 7,305-byte `tokenizer_config.json`:
SHA256 `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583`,
Git blob `07bfe0640cb5a0037f9322287fbfc682806cf672`. Authority comes from the
accepted [agent inventory](../evaluation/qwen7b_upstream_inventory_v1.json),
[mount scan](../../experiments/manifests/phase5_agent_mount_v1_scan01.json), and
[guard snapshot](../../tests/fixtures/ordinary_pair_guard_snapshot.json).
No arbitrary caller-supplied hash is trusted.

[Public source bytes](../evaluation/tokenizer_config_v1_source.json) use a JSON
string envelope to preserve the upstream file's missing final newline. Decode
`source_utf8` to UTF-8 for tests; the envelope itself is not a model input.
Its publisher chat template is data only: never execute it in this auditor or
inject it into benchmark prompts. No vocabulary, weights or private data added.

## Interfaces

- `tokenizer_metadata_v1.authenticate(path, role)` checks no symlink, regular
  file, bounded exact size, SHA256 and Git blob before strict JSON parsing. It
  derives pad/EOS IDs from unique special entries in `added_tokens_decoder`.
- `collect_phase5_tokenizer_metadata.py --agent-path ... --guard-path ...
  --output ...` reads only each model's configuration, authenticates both before
  writing, copies to a fresh disjoint directory, and checks copied/source bytes.
  Any partial failure remains unaccepted; it is not retried or overwritten.
- Output names are exactly `agent_tokenizer_config.json` and
  `guard_tokenizer_config.json`. Collection alone does not authenticate a full
  model mount or prove that an agent model was loaded.
- `ordinary_tokenizer_audit_v1.audit(...)` adds a fifth, disjoint read-only
  `tokenizers` root to the frozen ordinary native audit. Derived pad IDs are
  passed to that auditor, and configuration bytes are bound to its authenticated
  agent runtime file list / fixed guard snapshot. Tokenizer EOS must be among
  authenticated publisher stop IDs. Inputs are checked again after joining.
- `audit_phase5_ordinary_tokenizer.py` takes probe/policy/attention/publishers/
  tokenizers/snapshot, explicit expected source commit, and fresh output outside
  all inputs. There are no user-provided pad-ID arguments.

## Acceptance and boundaries

Tests must reject byte/size/hash drift, links, extra/missing/nested metadata,
source/loader/policy mismatch and input mutation during audit. Saved inputs must
remain unchanged and repeated receipts byte-identical. Imports remain free of
Torch, Transformers and tokenizers; native timings in synthetic tests are fake.

`tokenizer_metadata_authenticated` and `tokenizer_ids_bound_to_policy` describe
only this new layer. Frozen inner receipts retain their local false flags;
they are not rewritten. `native_tokenizer_executed`, `native_validated`,
`source_authenticated` and `phase5_accepted` remain false. This does not prove
native tokenization of messages or audit all tokenizer backend semantics.
Exact package/source/remote validation and a new native A/B/A run remain next.
