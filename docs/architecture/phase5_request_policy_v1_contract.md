# Request-local generation policy observation v1

CPU component after request-pair rehearsal. Frozen stress observer, native
loaders, attention adapter and request-pair v1 remain unchanged. No Test access.

`RequestPolicyBackend` wraps an exact fresh EfficientRequestBackend, retaining
its native model/config and original messages. `RequestPolicyFactory` validates
fresh disjoint policy/attention roots before invoking EfficientRequestFactory.
The later pair runner must place ReadyFactory outside progress outside policy
outside attention outside native factory. No new GPU entry or runtime adoption
is implied by this component.

Each admitted request gets request_000001 etc. Observe original bound
_prepare_generation_config and _prepare_generated_length exactly once, in order,
without replay, forcing length, changing parameters or copying input/token
tensors. Input length is a strict integer1–4096. Record public allowlisted
submitted/resolved/length/publisher/global config only; exclude private tensors.
Ordinary native submitted min_new_tokens and output_logits are None (unlike
the fixed stress harness). Keep actual publisher/default inheritance unchanged.

Baseline publisher snapshot is captured at construction, checked before/after
every request; drift retires the wrapper rather than resetting publisher config.
Check owner PID/thread, role generation config and native/response identities.
Restore installed methods on success, exception, interruption and evidence-write
failure; release locks even if restoration receipts cannot be saved. Any admitted
failure permanently retires the wrapper. Caller must close/reap the task worker.
No inter-task state isolation is claimed by this wrapper alone.

Completed requests have entered/resolved/length/restored/completed records.
Error paths preserve available partials; missing or error requests cannot pass
the success auditor. Auditor joins the existing attention/native metrics audit,
checks exactly declared requests/indices/PID/model, independently reconstructs
ordinary submitted config and publisher/default precedence, and recomputes
length using measured input tokens. Reject inventory/JSON/type/hash/restore
mutations and input changes during audit; no inference or input writes.

Caller must independently authenticate publisher metadata and tokenizer pad ID,
remote source, native loader/memory and supervisor lifecycle. Auditor flags these
limits explicitly; config consistency is not proof of source authentication,
all generation internals, full KV-cache, stateless numerical outputs or quality.
Native pinned-wheel method checks may execute with fake objects only in tests;
no local weights, Torch, native tensors or GPU. Native composed rehearsal and
exact package preflight remain prerequisites before a new Kaggle model run.
