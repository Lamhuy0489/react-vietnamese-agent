# Phase 5 — pinned room-ticket pair, CPU evidence v1

2026-09-24 local time. After the owner's content-free source-role confirmation,
the new [adapter](../../src/react_agent/security_v1/room_ticket_pair_runtime_v1.py)
composes the existing v12 cumulative loop, constrained guard and ExitPair with
the v14 dated public-field ticket policy. It does **not** mutate measured v12,
the CPU-only v13/v14 runtimes, Dev32 raw or the held-out Test. A separate
[read-only auditor](../../src/react_agent/validation/room_ticket_pair_audit_v1.py)
checks the new runtime version and frozen prospective pin identity; the old
clause auditor remains strict for its own runtime. The first audit attempt
correctly rejected the new version, so a versioned auditor was added rather
than relaxing the historical audit.

Admission reads the actual environment's document IDs before pair startup,
then requires exact approved S0/S2 roles, the reviewed draft SHA, a separately
declared `InventoryPin` SHA and matching source commit. Wrong hash, wrong A6
level, duplicate/missing/extra auxiliary IDs or caller-supplied native
constraint root fail closed. The candidate constructs only the fixed eight
synthetic mock tools. The runtime trace retains the pin SHA, draft SHA and
source commit but explicitly marks source authentication and human attestation
as **not proven** by CPU/schema checks. Real Git/package authentication is a
later release-audit task.

Paired-process specimen controls use an obviously fake source commit and
test-only synthetic documents **after** a fake test pin. They are not the
approved prospective pilot payload. The clean public room reached only the
authorized `post_webhook_mock`; appending an instruction to the public document
kept the webhook denied. An S2 source containing the same room value and a
wrong webhook destination are also denied; a synthetic private value in the
proposed final is redacted or denied before release. On the *same reviewed
S0/S2 metadata* and scripted paired transport, v12 metadata-only still denied
the clean sink while the ticket adapter allowed it; this isolates the ticket
effect from merely changing labels. Paired runs generated
agent/guard and exit receipts, which the new auditor joined without modifying
raw files. An altered expected pin fails the auditor. Bad run identity or A5
instead of A6 is rejected before worker start and before runtime output.

Eight new paired integration cases and seven review/admission unit cases pass;
the broader ticket/inventory suite and repository QA are recorded in the
[handoff](../../knowledge/handoff.md). This is **CPU synthetic correctness and
audit wiring**, not native model quality, a real source freeze, a successful
Kaggle package, guard lifecycle reliability, Dev32 remediation or Phase 5
acceptance. The production `InventoryPin` does not yet exist: source code and
supporting evidence still need a coherent QA'd commit, then the pin/run
manifest must precede actual pilot content. Follow the
[prospective protocol](phase5_room_prospective_v1_protocol.md) and keep Test
sealed.
