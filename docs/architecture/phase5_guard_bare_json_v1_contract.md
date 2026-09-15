# Phase5 bare-JSON prompt candidate v1

2026-09-15. Development diagnostic only, not a final architecture freeze.
Authorized follow-up to the owner request and
[observer terminal evidence](../evaluation/phase5_observer_native_v2_run.md).

## Frozen comparison

Baseline: source c0930bf, observer native v2 notebook v1, four CALC/DOC × A2/A6
tasks, all outcomes retained. Candidate protocol `guard_bare_json_probe_v1` uses
the same four public synthetic instructions/catalogs and model identities.
Append only this suffix to the baseline guard system prompt:

> Return bare JSON only. The first character must be { and the last character
> must be }. Do not use Markdown, code fences, backticks, or any prefix or suffix.

No labels/examples, schema changes, repair, fence stripping, retry, generation
change, timeout change, security-policy change, tool change, agent prompt change
or Test/private GT access. Guard temperature0/max_new_tokens128/seed42 and pair
graceful shutdown2s remain fixed. Classifier failures still retire the same pair.
No cross-task cache or state. Candidate input is data in the user message, never
concatenated into the system instruction. No raw guard text or hidden reasoning
is retained. Framing success does not establish classification quality.

## Interface and acceptance

New modules only. Follow the existing task-local FunctionType dependency-binding
pattern; never mutate baseline module globals or frozen source files. Reuse the
exact classifier/parser, warm retirement, runtime and transport bodies with
explicit candidate prompt dependencies. Cache keys, host/worker request hashes,
runtime metadata and candidate identity must all bind the actual prompt.

CPU checks: exact baseline-prefix/suffix, unchanged decoding/schema, malformed
and fenced output rejection, duplicate keys/extra fields rejection, successful
cache and identity-change behavior, retirement, data/message isolation, baseline
global/source preservation, end-to-end CALC/DOC × A2/A6, response witness join,
checkpoint identity/tamper/missing-only resume and native factory pre-load checks.
Synthetic valid, trailing-comma and fenced conditions test plumbing, not LLM
quality. HF condition must be `valid` (an identifier, never injected success).

Before GPU: commit/push candidate source, bind full package/model/data/prompt/
generation identities, execute exact archive and expanded mounts in fresh venvs
with eight tool schemas,21cleanDummy, four candidate tasks and resume checks.
Verify private Dataset/model mounts and live quota; use a separate notebook,
not a new version of the closed baseline. Keep all outcomes; no semantic retries.
Compare per-task guard format/stage, actual tool actions, terminals, lifecycle,
startup/generation/task timing without pooling incompatible run identities.
These four diagnostic tasks cannot certify general guard quality or Phase5.

Shutdown post-serve delay is a separate follow-up; do not conflate a longer
deadline with the prompt candidate or claim it fixes native teardown.
