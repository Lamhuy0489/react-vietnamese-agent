# Request worker v3 — quiescence and bounded HTTP candidate

2026-09-28. New versioned implementation; existing worker v1, lifecycle v2,
receipts and native experiment inputs retain their original bytes. This
candidate has not been submitted to Kaggle. Scope: inference lifecycle only;
tools, benchmark data and evaluators stay on the host. Test remains sealed.

## Native adapter

`load_hf_engine` explicitly loads the frozen HFEngine with its original model
fingerprints, two-T4 checks, warmup, schemas, greedy decoding and limits.
`QuiescentEngine` exclusively owns that engine and assigns a fresh stop event
before each request. The v1 stopping criterion already observes that event.
Generation and cleanup share the same lock; no second request may enter while
either is running. No changes to model prompts or generation settings.

After success, cancellation or a generation error, synchronize both CUDA
devices before returning an `EngineOutcome`. Attempt synchronization of device1
even when device0 raises. An unhandled generation error retires the model
instance; failed synchronization yields QUIESCENCE_UNKNOWN and retires it.
Interrupts also attempt cleanup and retire. A stuck synchronization leaves the
request active; it must never produce a false successful cancellation receipt.

PyTorch documents synchronization as waiting for work on the selected device;
using an explicit device for each of the two GPUs is therefore necessary.
[PyTorch2.10 reference](https://docs.pytorch.org/docs/2.10/generated/torch.cuda.synchronize.html).
The event is cooperative, checked through the generation stopping criterion;
it cannot interrupt an individual GPU operation.
[Transformers stopping criteria reference](https://huggingface.co/docs/transformers/v4.57.1/en/internal/generation_utils#transformers.StoppingCriteria).

This establishes an implementation contract, not proof of hardware behavior.
`gpu_quiescence_attested=true` means the worker's device-synchronize callback
returned successfully; it is not external attestation. CPU substitutes can test
ordering but cannot establish native GPU quiescence. This also does not unload
the model, free its resident VRAM or close the long-lived notebook process.

## State, bounds and transport

`QuiescentLifecycle` writes/fsyncs started state before dispatch. Terminal status
requires callback return; cancellation wins over generated content only after
confirmed synchronization. Failure to confirm cleanup produces
QUIESCENCE_UNKNOWN, never CANCELLED. Persistence failure marks state nondurable
and retires the instance, even when in-memory state looks terminal.

No eviction: at most256request IDs; at most262144serialized result bytes per ID
(64MiB retained JSON content at the maximum, plus Python object/index overhead).
Oversized output becomes a cached RESULT_TOO_LARGE error. Capacity exhaustion
refuses new IDs; repeated IDs cannot silently execute again. This bounds
retained content, not total Python/model RAM. CPU QA tests both bounds.

`QuiescentHTTP` publishes a random boot ID and public worker/model/source pins.
Authenticated completion, status and cancel routes bind that boot ID.
`LimitedHTTPServer` admits at most8handlers by default; extra connections close,
and slots release on completion or thread-start failure. Socket timeout starts
before header parsing. Saturation may delay status/cancel: no availability or
bounded-cancellation-latency guarantee is claimed. TLS/tunnel lifecycle remains
deployment work. Response loss does not erase worker state or cached output.

`load_worker` composes the native adapter and API after load/warmup/synchronization.
It does not start a server, download a tunnel, expose credentials or publish
discovery. A notebook entrypoint must explicitly own those actions.

## Host reconciliation boundary

`verify_terminal_status` requires exact boot/session/source/model/role and
request-hash matches, terminal state, engine returned, inactive engine,
synchronization confirmation, durable receipt and non-retired instance.
`save_resolution` appends an immutable resolution receipt. Unknown/mismatched
status remains unresolved; a new READY observation alone never resolves it.
These functions assume an authenticated transport; they do not attest worker
honesty. They do not modify v1 journal records or authorize semantic retries.

Still required: versioned authenticated host transport/journal/runtime wiring,
cached-result recovery with hash checks, notebook entrypoint/discovery and
lifetime shutdown handling, source commit/push freeze and exact final package
QA, then a predeclared native cancellation diagnostic. Any uncertain old v1
request must remain blocked rather than being bypassed by changing journal roots.
