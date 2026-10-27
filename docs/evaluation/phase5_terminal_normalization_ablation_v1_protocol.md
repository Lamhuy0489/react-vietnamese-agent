# Phase 5 terminal-line normalization ablation — protocol v1

This is a predeclared, CPU-only ablation prompted by the epoch-2 exact-email
diagnosis. It tests one narrow hypothesis: a model proposal that differs from
the canonical public body only by one terminal line ending can be released
after the raw proposal and canonical release are both hash-bound.

The profile removes at most one terminal `LF`, `CRLF`, or `CR`. It does not
trim spaces, normalize Unicode, remove controls, alter internal newlines, or
change the A3–A5 session veto, guard threshold, or provenance requirements.
Repeated terminal endings and every other mismatch are denied. The frozen
mainline API result is not rewritten and this profile is not enabled by
default. The component uses synthetic values only and performs no API/model or
network request.

The expected canonical body is host-declared before evaluation. The ablation
records `raw_sha256`, `released_sha256`, status, operation, byte lengths, and
the zero Test/private-ground-truth counters. A future native run would require
a separate task identity, worker journal, source snapshot, and paired evaluator;
this CPU receipt is not native evidence or Phase 5 acceptance.
