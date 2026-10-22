# Kaggle HTTP diagnostic v1

2026-09-27, Phase 5 opt-in technical scope. Owner clarified Llama3.2-3B is a
guard candidate; Qwen3-8B, Gemma4-E4B and DeepSeek-R1-Llama8B are task agents.
Use existing four sessions; no default A0–A6/model/policy replacement. This
supersedes the old batch-only transport preference for this diagnostic.

Before inference: record working-tree source hashes (not a frozen Git commit),
synthetic inputs, generation profile, evaluator version, ordered task IDs,
expected model mounts and observed metadata. Legacy servers do not attest
weights/tokenizer/library hashes or seeds; identity is explicitly unverified.
Therefore this is connectivity/format/Broker smoke, not research scores or a
native release of the field-reference prototype. Held-out Test stays sealed.

HTTP adapter implements existing LLMBackend with explicit generate/health
operations, verified HTTPS, no redirects or automatic retries, bounded response
bytes and socket timeout. Only greedy temperature=0 is admitted for this legacy
server. Seed is recorded as unsupported, never claimed applied. Model alias and
mount path must match configured expectations. Credentials/URLs are local only;
errors retain codes, never response bodies/authorization/raw exception text.
Server-reported token usage/finish reason are unverified legacy estimates.

Three fresh synthetic calculator tasks use the existing context/parser, local
CalculatorTool via ToolBroker, at most three model calls each, 256 output tokens
per call. Same user input and profile across agents; no cross-task state.
Two separate guard checks use existing ModelGuard/PROMPT, 128 output tokens:
ordinary public-room content and explicit instruction override/exfiltration.
Maximum 11 model calls, sequential within each server, no semantic retries.
Do not request/store reasoning or persist rejected raw text. Only validated
observable action/final/guard objects, Broker events, timing and error codes
are saved. No grammar constraints are claimed for Llama; malformed output is
an error, not SAFE. Quality expectations are evaluator-only.

Create a fresh output directory and a declaration before calls. Save a started
marker before each task and a checkpoint after it. Resume validates declaration,
source, input and checkpoint hashes, skips all completed tasks (including errors),
and refuses a partial started task. Timeout does not prove remote cancellation;
never silently replay it. No notebook restart/submit/stop is needed for this
milestone. Promotion requires separate Dev protocol and immutable model identity.
