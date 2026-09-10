# Next gate: maximum-context stress design (not submitted)

Status: implementation design, not an accepted test, GPU run or a frozen launch
manifest. Separate from the running IPC-origin diagnostic. Do not change a
running kernel, frozen adapter or benchmark decoding to execute this design.

## Question and scope

Can the current two-T4 candidate placement execute its maximum admitted input
and output lengths with both model workers resident and then reclaim memory?
Small-context success and fixed allocator fractions do not answer this question.
Agent budget is4096input/512output; guard4096input/128output. These are distinct
technical workloads, not a head-to-head model capability or speed comparison.

## Proposed bounded implementation

- Separate diagnostic backend wrapper inside each existing task-owned worker.
  Reuse authenticated HF model/tokenizer loaders and placement checks. Never
  inject diagnostic host commands into the benchmark prompts/runtime.
- Construct exactly4096non-padding input token IDs from a fixed, innocuous
  synthetic Vietnamese seed and the pinned tokenizer; record seed hash, tokenizer
  identity, construction algorithm and exact token-ID digest. This is a token-
  geometry workload, not a claim about4096tokens of natural chat-context utility.
  No truncation of a user/benchmark request; deterministic construction must be
  declared before the run and fail if tokenizer assumptions do not hold.
- Fresh native greedy generation config/cache, batch1, seed42, one beam,
  FP16/SDPA and existing agent12/7GiB/guard5GiB caps. Use min_new_tokens equal to
  max_new_tokens512/128 only in this diagnostic; preserve the native EOS list.
  This intentionally suppresses early EOS and is not normal benchmark decoding.
- Record exactly4096input IDs and require exactly512/128new output IDs. Do not
  decode or save generated text; store shape/count/hash only. Do not request
  hidden reasoning, scores, attention maps or hidden-state output.
- Native generation normally does not forward the last emitted token through
  the model. Therefore output count alone cannot certify a KV cache covering the
  full4096+512/128positions. Report actual cache length if inspected; if full
  boundary allocation is required, predeclare a separate final-token forward
  and its timing/memory, rather than silently equating output and cache lengths.
- Agent then guard, no simultaneous inference; one fresh pair, fresh per-call
  cache. Pair retains both models between calls. Preserve cold1200/120 and
  request180/120s ceilings/cleanup graces, unless a new pre-run contract explicitly
  justifies distinct stress-only deadlines. Timeout is an observed failure, not
  permission to silently lengthen a completed run or retry for a better result.
- Record ready memory; each call's tokenize/prefill/generation/optional final
  forward/host total separately where actually instrumented. Peaks are process
  allocator counters per GPU; global free endpoints are not global peak memory.
- Close in finally on success, OOM, timeout or interruption; preserve partial
  evidence, worker PID/reap/method and six recovery samples at1s intervals.
  Keep ±256MiB last-three recovery gate and old forced/graceful distinction.

## Required preflight before a launch decision

CPU fakes must verify exact token count/digest and mutation rejection, no
padding/truncation, max length rejection, isolated diagnostic decoding, fresh
cache/config, correct single-device/dual-device routing, failure retirement,
durable partials and no generated text retention. Verify optional final-token
forward semantics against the exact installed native version, not assumptions.

Then exact standalone allowlisted archive/expanded/PAX wrapper rehearsals with
8tools/21Dummy/resume and the actual stress entry point in stub mode; full QA,
source/receipts pushed to GitHub, private mounts/versions/quota verified. Record
new kernel ID, exact source/dependency hashes, expected calls and wall ceiling
in a launch contract before any GPU submission. No local weights, Test/GT,
automatic fallback, account cycling or semantic retries. No stress run was
submitted as part of writing this design.

## Source-level evidence and limits

The already pinned offline wheel `transformers-5.5.0-py3-none-any.whl`, SHA256
`821a9ff0961abbb29eb1eb686d78df1c85929fdf213a3fe49dc6bd94f9efa944`, was inspected
without installation/model loading on2026-09-09. Its generation/utils.py sets
max_cache_length to max_length minus one, then appends sampled IDs after forward
and checks stopping criteria. Its MinNewTokensLengthLogitsProcessor suppresses
EOS before the requested minimum. These code observations motivate the separate
cache/output accounting; they are not measured cache residency or throughput.
Primary source: [Transformers5.5.0 generation implementation](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/generation/utils.py),
[logits processor](https://github.com/huggingface/transformers/blob/v5.5.0/src/transformers/generation/logits_process.py).

Remaining independent acceptance gates: runtime integration, A4 processing-scope
anchors, general final entitlements, grouped Dev guard/model decision and freeze.
This design does not close any of those gates or Phase5.
