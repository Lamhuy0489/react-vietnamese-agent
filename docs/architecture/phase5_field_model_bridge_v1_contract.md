# Field-plan model bridge v1 (exploratory, not A6)

2026-09-25, before implementation. Extends the owner-approved isolated prototype;
does not change the original field component contract or frozen runtime.

Host supplies an existing pinned Session, matching raw user, generation config,
expected backend model/revision, and optional final veto callback. Host reads
the Grant's bounded readable documents through the Broker, then offers their
raw records and field references to one LLM call. This is a one-shot selection
bridge, NOT a ReAct loop or a natural-language authorization compiler. Read
authorization is the existing Grant; A1/guard/PRE/POST are NOT wired here.

Model messages contain a fixed system schema and a JSON user envelope with
untrusted observations. No evaluator, expected answer, attack label, project
memory or veto result is included. Model outputs exactly Plan JSON: no repair,
markdown stripping, explanation, retry, literal final or permission fields.
Reject duplicate JSON keys, non-finite constants, over-budget responses and
wrong response identities. Host validates references and labels again. The
host-only final veto callback is denied by default and must return actual True;
errors fail closed. A fake callback in tests is not a native guard evaluation.

Owner subsequently selected batch Kaggle, without a public endpoint. No HTTP
transport, tunnel or new backend is implemented here. Reuse the LLMBackend
interface; a native backend must separately disable thinking, verify model
weights and retain only observable output. This bridge cannot attest backend
internals: matching response model/revision strings is NOT weight attestation.
Formal native release stays unavailable. Mock sinks remain network-free.

Limits: 1 MiB serialized request, 64 KiB plan, output tokens <=4096, no retry.
Native timeouts/process deadlines are the backend/worker's responsibility, not
guaranteed by this synchronous bridge. Record call and total bridge wall time,
not GPU decode throughput or TTFT. Existing native instrumentation supplies
token/device timings separately when admitted; CPU stubs cannot supply them.

CPU acceptance: real Broker public selection succeeds only with host permission;
private/encoded/mixed/ungranted/forged refs and literal/free-form permission
attempts fail; malformed/duplicate/oversized/identity/transport/veto failures
fail closed, no generation retry. Backend errors are reduced to a closed status,
not persisted with raw content. These controls establish wiring only, not prompt-injection resistance
of an LLM, utility generalization, implicit-flow protection or phase completion.

Next: real synthetic model-selection smoke with pinned source/model/server
manifest; then actual prior policy/guard/PRE/POST composition on a fresh protocol.
No promotion to A0–A6 and no reuse of held-out Test to design this interface.
