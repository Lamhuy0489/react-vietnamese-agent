# Private-record final entitlements v1

This component is a host-only extension for a future A6 runtime. It is separate
from the frozen `a6_public_final_v1` policy and does not modify runtime v5,
`value_release.py` or any prior benchmark source. It never reads evaluator
grants, expected answers, hidden reasoning or held-out Test payloads.

## Explicit grant shape

`extract_final_entitlement` scans only affirmative raw-user clauses. A clause
must name at least one exact synthetic `DOC_*`/`CACHE_*` resource or a bounded
database table, and at least one supported value type (GPA, email, URL, student
ID, course code, phone, money, date or identifier) together with a final-answer
cue such as “trả”, “hiển thị”, “show” or “report”. Negated, conditional, quoted,
scope-only and destination-only clauses do not grant final access. The raw user
is bound by SHA-256; the raw text is not copied into the entitlement artifact.

The host must pass the same run-local `ValueOriginIndex`, raw user artifact ID
and proposed final artifact. The function verifies that the entitlement hash
matches the raw user, the proposal descends from that user, and the admitted
source roots exactly cover the proposal ancestry. No caller-supplied evaluator
or model-origin labels are accepted.

## Release rule

Known protected values are matched with the frozen exact/raw-offset profile.
An origin is entitled only when its source artifact has the exact user-named
resource/table, its value type is explicitly granted and its trust is
`TRUSTED`. An untrusted origin never becomes entitled, even when a trusted
origin contains the same value. Authorized raw spans remain; unauthorized spans
are deterministically replaced with `[REDACTED]`. Normalized-only matches,
incomplete coverage, residual unauthorized matches or scan failures produce a
new empty released artifact and `DENY`. A final with no known protected match
is `ALLOW` only in the finite extraction profile.

Released artifacts retain conservative sensitivity/trust joins and link the
proposal plus all observed matching roots. The decision stores proposed/released
IDs and hashes, index/entitlement identities, match classes and redacted spans;
it does not store model reasoning. A future runtime must compose this decision
with A6 rule/session vetoes and final sink accounting, rather than treating it
as a standalone security success.

## Evidence and limits

The v1 QA covers authorized private GPA, missing/wrong/untrusted source or value
type, mixed authorized/unauthorized output, normalized-only denial, coverage and
hash binding, public no-match, serialization and cue inventory. It is synthetic
component evidence only: it does not prove semantic intent, paraphrase/encoded
leakage resistance, complete origin extraction, runtime adoption, ASR/utility,
model quality or Phase 5 acceptance. Broader origin coverage and versioned A6
runtime differential tests remain required.
