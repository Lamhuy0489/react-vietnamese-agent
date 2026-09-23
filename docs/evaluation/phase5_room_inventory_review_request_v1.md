# Phase 5 — source-inventory review and owner decision

Prepared 2026-09-23 for a **new auxiliary prospective pilot**, not the frozen
Phase 3 benchmark or scored Dev32. The
[content-free draft](../../experiments/manifests/phase5_room_prospective_inventory_review_draft_v1.json)
has two IDs that have not been used in the earlier CPU pilots. No document
content, agent answer, evaluator label or model output has been created for
this pair. It is not an approved `InventoryPin` or an inference manifest.
Draft file SHA-256:
`3e59834a960bdac5995fdbff07fb589a450d59861440600ef606b339e2125cc5`.

| Planned source ID | Host type | Sensitivity | Trust | Intended source role |
|---|---|---|---|---|
| `AUX_FUTUREROOM` | document | S0 public | UNTRUSTED | Synthetic public room bulletin |
| `AUX_FUTUREPRIVATE` | document | S2 confidential | UNTRUSTED | Synthetic private enrollment record, unrelated to the room in the clean branch |

The clean and attack/control branches will share these source identities and
labels; only their document content may differ. The S2-collision branch will
deliberately repeat a room value in the private source and must be denied.
No branch may promote source trust or derive a label from its text. The user
task and mock destination will be declared before inference too. This is a
technical pilot outside formal benchmark scoring; any claim about Phase 5 DoD
or model utility still needs its own prospective protocol and evidence.

**Owner decision received before writing either document.** In reply to the
explicit question confirming `AUX_FUTUREROOM` S0, `AUX_FUTUREPRIVATE` S2 and
both UNTRUSTED, the owner answered “ok làm tiếp và hoàn thiện cho tôi”. This
is interpreted as self-review approval of exactly those roles, not approval
of a model result or a change to the frozen benchmark. The content-free
[review record](../../experiments/manifests/phase5_room_prospective_inventory_review_v1.json)
was written at 2026-09-23 16:58:41 UTC; SHA-256
`a7036c2892d2ffbc1025f811a1f0bc04cb1a02844b2176f0c0c82a99fbcc90bc`.
It binds the original draft hash and references this conversation. The exact
timestamp is **recording time**, not a cryptographic timestamp of the owner's
message; no independent peer review or cryptographic human attestation is
claimed. [Admission code](../../src/react_agent/validation/room_inventory_review_v1.py)
rejects altered draft bytes/roles, wrong pair, mismatched run pin/commit and
missing/extra source IDs before constructing a catalog.

The next gate remains open: create a versioned `InventoryPin` with an **actual
source commit**, freeze its SHA-256 in a separate run manifest, and only then
author the new content under the [prospective protocol](phase5_room_prospective_v1_protocol.md).
Current worktree is not that source commit. The
[paired CPU adapter](phase5_room_ticket_pair_cpu_v1_report.md) has synthetic
admission/audit evidence but not an actual native package. `host_inventory_attested`
remains false and no model run is authorized solely by this owner response or
record.
