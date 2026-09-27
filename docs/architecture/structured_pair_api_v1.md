# Two-role structured inference API v1

Owner authorization 2026-09-27: use Qwen3-8B as the task agent and Llama3.2-3B
Instruct as the guard, reissue the two notebooks with appropriate output formats.
Owner subsequently confirmed all four previous sessions stopped. Accounts stay
buiquocviet/huylmhuhu; no account cycling. Gemma/DeepSeek remain historical
candidates. This is inference configuration, no weight fine-tuning.

Scope: Phase5 technical integration. Benchmark/Test, policies and old scores
stay frozen. No claim that two guard controls select a generally reliable guard.
Future A0–A6 comparison must use the same agent schema constraint at every level;
format enforcement is not a security defense. New guard/model/decoding choices
need a prospective Dev profile before research comparisons; no automatic promotion.

## Server contract

- Private inference-only scripts, no benchmark inputs, tools, private oracles or
  runtime memory packaged. Host executes every tool through its Tool Broker.
- Exact Kaggle Model mount versions: qwen-lm/qwen-3/transformers/8b/1 and
  metaresearch/llama-3.2/transformers/3b-instruct/1; reject fallback/CPU offload.
  Hash model/tokenizer files at startup, report actual dependency versions,
  committed source and session identity. Hashing does not attest publisher bytes.
- FP16 on T4×2; tensor operation plus constrained GPU warmup precede READY.
  Transformers4.57.6/tokenizers0.22.2/Torch2.10.0/accelerate1.12.0,
  lm-format-enforcer0.11.3/jsonschema4.25.1/cryptography46.0.3 pinned.
  CUDA suffix/transitive libraries recorded; no image-wide reproducibility claim.
- POST /v1/chat/completions, authenticated; stream=false,temperature=0,
  seed default42 applied, max prompt4096 tokens; guard max128,agent max1024.
  Agent default action/final schema with final answer string and eight tool names.
  Agent may supply bounded inline JSON schema; guard schema is fixed risk/labels/
  confidence. No silent ignored parameters, prompt fallback or output repair.
- Token grammar via LM Format Enforcer; validate complete output independently
  using jsonschema before return. True token-ID counts, EOS and schema check;
  truncation/timeout returns structured error without raw/reasoning text.
  Qwen thinking disabled. Host still validates args, provenance, grants and gates.
- Authenticated metadata and shutdown; one active generation/server, BUSY429.
  Request-id/hash cache64 entries including errors; changed payload409, no automatic
  retry.90s generation stop checked between steps, not a hard CUDA cancellation
  guarantee. Graceful shutdown signals stop, joins server threads and stops tunnel.
- Cloudflared2026.9.3 with official release SHA256 pinned. Non-streaming avoids
  reliance on Quick Tunnel SSE. Tunnel sessions remain temporary.
- Runtime generates API key. Notebook contains only local-generated RSA public
  key, never API key or credentials. Connection encrypted with RSA3072/OAEP-SHA256
  and published to per-session discovery topic; local private key/config mode0600.
  No credentials/keys in Git, stdout, request traces or selected evidence.

## Preflight and release

Exact generated scripts tested from archive and expanded layouts with isolated
interpreter and no project imports. Character grammar/independent schema checks,
authentication, duplicate-request behavior, bounds and error handling before GPU.
Host eight-tool tests stay local; no selected Dev task list is shipped to this
inference service. Mac Intel supports Torch2.2.2 only, so CPU preflight is not
native GPU compatibility proof; worker warmup tests the pinned real GPU stack.

One coherent source freeze/push is required by experiment-repro before submission;
include serving/packaging/client/tests, exclude unrelated working-tree changes.
Prepare committed package, repeat exact preflight, submit each role once and
authenticate remote source/version before using endpoints. No automatic GPU retries.

New synthetic integration smoke: Qwen calculates23*7+5 through actual Broker,
Llama classifies action and final proposal, host validates final; at most3agent
calls and one guard call/proposal. Separate normal/malicious guard controls may
verify the serving schema, not guard quality or ASR. Do not repeat prior failed
task to replace its score; run01 remains immutable. Log observable valid objects,
identities/timing/errors only. Model fingerprint and all generation/source/task
identities recorded before these smoke calls. Test remains sealed.

References read2026-09-27: [LM Format Enforcer integration](https://github.com/noamgat/lm-format-enforcer)
filters tokens using JSON schema; [Transformers pinned release](https://pypi.org/project/transformers/4.57.6/).
