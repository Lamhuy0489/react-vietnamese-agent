# Qwen 7B mount authentication on Kaggle CPU

One private/offline CPU submission; no model loading or inference, no GPU,
no local agent weights downloaded. Model handle remains
`qwen-lm/qwen2.5/transformers/7b-instruct/1`.

| Evidence | Observed result |
| --- | --- |
| Runtime files vs pinned publisher inventory | 11/11 match, including all four weight shards |
| Optional documentation | LICENSE and .gitattributes match; README differs |
| Full inventory | Rejected, as expected from pre-submit README size mismatch |
| Bytes hashed on Kaggle | 15,242,807,035 |
| Hash scan duration | 290.801 seconds |
| Kernel status | ERROR: scanner explicitly returns nonzero on full mismatch |
| Submissions / inference calls / GPU runs | 1 / 0 / 0 |

HF revision `a09a35458c702b33eeacc393d103063234e8bc28`. Kaggle README is
6,005 bytes vs publisher6,240; all other observed file bytes match the declared
size/digest checks. No missing/extra files. Source scanner hashes weights using
LFS SHA256 and metadata using Git blob SHA1; ordinary SHA256 also recorded.
This establishes present file identity, not an assertion about prior pilot bytes.

[Full scan records](../../experiments/manifests/phase5_agent_mount_v1_scan01.json),
[independent claim recomputation](../../experiments/manifests/phase5_agent_mount_v1_audit01.json),
[pre-submit contract](../architecture/phase5_agent_mount_v1_contract.md).

## Platform metadata deviations

Requested slug `react-vn-agent7b-mount-auth-v1`; Kaggle created
`huylmhuhu/react-vn-agent-mount-auth-v1` from title, id133605346. No resubmission.
Pulled source hash matches submitted wrapper exactly. Kaggle serialized framework
as `Transformers`; the audit accepts only that exact enum capitalization or the
requested lowercase, preserving owner/model/variation/version. CPU/private/
offline settings and single model mount verified; image digest is in the audit.

## Limits and next step

The scan's full rejection remains unchanged. The audit validates saved worker
hash claims, not a second independent hashing of model bytes locally. Both local
audits reproduce byte-identically. No benchmark Test/GT or project memory sent.

A separate versioned runtime-input admission contract is needed to bind the
matching runtime bytes while explicitly accounting for the known documentation
difference. Then implement the agent's budget-enforcing HF adapter, hash-check
on Kaggle before loading, and run CPU fake plus exact runtime-bundle preflight
before combined GPU residency/context tests. Phase5 is not accepted.
