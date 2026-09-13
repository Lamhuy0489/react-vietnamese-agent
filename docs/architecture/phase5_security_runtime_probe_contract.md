# Seven-level native runtime technical probe v1

Same frozen Qwen7B agent, 512-token greedy seed42 generation, security runtime v7
and eight mock tools across A0–A6. One public synthetic calculator instruction,
fresh state/worker(s) for each level. No benchmark labels or private oracle.
A0/A1 use the same ThreadProgress → RequestPolicy → EfficientRequest → native
agent loader stack as A2–A6, but never construct a guard or ModelPair.

This is a technical pilot, not the final security experiment. The inherited
agent-only interface has one 1200s startup/call deadline versus paired agent's
1200s startup/180s call deadline; both are recorded explicitly. Do not make a
cross-level timeout/latency advantage claim from this pilot. Agent model,
decoding, prompt, tools and attention are unchanged. Guard remains Qwen1.5B,
128 tokens; quality/selection remains unaccepted.

Runner output contains a frozen identity, per-level runtime/worker/native
sidecars, baseline and six recovery memory samples, then a raw-hash checkpoint.
Resume validates identity and every raw hash; it skips terminal results including
semantic/model failure, refuses partial attempts and stops on unrecovered memory.
No semantic retries. Startup exceptions preserve partials and require a separate
infrastructure deviation before a fresh run. Stub mode never imports native models.

Native audit joins runtime/worker identity with model admission, pinned tokenizer
and publisher bytes, policy/attention instrumentation and per-call token/timing
records. Failed native roles are explicitly partial/unassessed, not successful
joins. Zero guard generation is recorded, not called an operational guard test.
All timings include instrumentation. Artifact consistency is separate from remote
source authentication. No quality, ASR, full GPU cleanup or Phase 5 acceptance claim.

Package v1 extends the old immutable 56-file overlay by 26 files (82 total).
Keep validation as a worker namespace package: the repository's validation
initializer imports clean-pool QA and must not enter the inference payload.
It reuses the pinned private base bundle, wheel/model hashes and Kaggle bootstrap;
selected bytes must be committed and pushed before GPU upload. Exact archive and
expanded mounts run in offline isolated venvs, with all eight tools/fault recovery,
21 public Dev Dummy tasks/missing-only resume, old ordinary fixture diagnostics
and the seven-level new stub runtime plus immutable resume. No model tensor is
loaded locally. New native routing is collector → runtime → joined auditor, fail-stop.
