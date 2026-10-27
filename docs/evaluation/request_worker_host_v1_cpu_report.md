# Request-worker v3 host wiring — CPU candidate

2026-09-29. This candidate adds the host side of the versioned request-worker
v3 lifecycle. It is source-only CPU evidence; it was not submitted to Kaggle,
did not open Test/private ground truth, and made no model or network request.

`request_worker_transport_v1.py` performs verified HTTPS-only, no-redirect
requests with bounded JSON reads. An authenticated `/models` probe pins the
worker's complete public identity and fresh boot `instance_id`; every request,
status lookup and cancel carries that instance id. It rejects identity changes,
unprobed calls, unsupported routes, oversized responses and malformed JSON.

`request_worker_journal_v1.py` is a new journal profile and does not rewrite the
frozen v1 journal. The directory is scoped by the static session/source/model
identity, while records include the dynamic boot id. An uncertain `started`
attempt remains blocked even after a reboot with a different boot id. Recovery
is explicit and fail-closed: GET status must match the exact request and full
identity and be terminal/durable/non-retired, then one identical POST is used
only to retrieve the worker's cached result. The immutable uncertain record is
never overwritten; recovery is recorded in a separate `.recovered.json` file.
No semantic retry is authorized and no prompt/model response is written to the
journal.

`request_worker_runtime_v1.py` provides a credential-free picklable factory and
structured LLM backend. It revalidates endpoint/metadata file hashes, loads
credentials only in the owning process, probes before construction, validates
the existing structured output schemas, and exposes status/cancel/recovery as
separate lifecycle operations. It is an opt-in candidate and is not connected
to the currently running notebooks.

Focused controls in
[`test_request_worker_host_v1.py`](../../tests/unit/test_request_worker_host_v1.py)
pass **6/6**: immutable success/duplicate delivery, uncertain-attempt blocking,
exact terminal cached recovery, status-hash mismatch with zero second POST,
fresh-boot bypass rejection, structured backend validation, and authenticated
transport probe/instance binding. Ruff and strict mypy pass for all three new
modules; no API/GPU inference was run.

This evidence does not prove remote endpoint availability, native CUDA
quiescence, server lifetime/shutdown, or Phase 5 acceptance. Existing v1/v3
receipts remain unchanged.
