# Phase 5 — exact final-literal proof v1, component CPU result

## Outcome

The opt-in [component](../../src/react_agent/security_v1/final_literal_proof_v1.py)
implements the [predeclared narrow protocol](phase5_final_literal_proof_v1_protocol.md)
and passes 18 deterministic synthetic CPU controls. It is **not connected to
A6 runtime** and is not a Phase 5 acceptance result. Frozen v12/v15 and the
stopped prospective room pilot are unchanged.

Two proof routes work on new synthetic literals with an S2 collision:

| Route | Host evidence required | Component result |
|---|---|---|
| Raw-user echo | Entire raw instruction `Nhắc lại nhãn <literal>.` | Exact literal ALLOW; v2 alone REDACT. |
| Reviewed S0 field | External hash of metadata-only source/field approval; exact raw task, one-field S0 document, source ancestry | Exact literal ALLOW with S2 trusted or untrusted. |

The proof carries raw-user/source content hashes and is re-derived from
host-observed artifacts at release; the public approval hash must arrive
independently from the caller, not be accepted from the proof. Final content
must equal the literal byte-for-byte. Extra private context or a different
private literal falls back to the existing v2 final gate and is redacted.
Forged/stale proof, wrong approval hash, S2-mislabeled “public” source,
wrong field/source ID, noncanonical/negated user wording and missing
source ancestry/index coverage are rejected before release. A zero-width
private copy is denied by the v2 normalized scan. Proposal and released
artifacts remain separate; proof and approval hashes are written to the
released artifact metadata, with conservative sensitivity/trust labels.

This proves only a *component mechanism*. The approval schema cannot prove
that a human reviewed the source before content; a future run must bind a
real host inventory review to an independently declared expected hash.
The narrow exact-final rule does not authorize surrounding private text,
other Vietnamese paraphrases, encoded literals or arbitrary S2 substrings.
No independent Dev matrix, paired runtime trace, native model or Kaggle
package yet validates utility/security at the system level.

Current working-tree hashes: protocol
`5cdc01f4bc47bd0fd0c6b80e9b688c2941eab1692d412502aa618cec23df7e7b`,
component `eed10d7d543ad6d4dcc1909816715aef7946331b9cc109ab08f0f2b5677e88c9`,
unit controls `95688a5c07f7bb639c1f35c37a65da264c2c63b1205ff7d7cf12038a558b55af`.
The Git base `c87c321b42345e6d7152ca60976363a67a972531` does not
contain these uncommitted files. No held-out Test/private benchmark oracle,
model inference or real external sink was accessed.
Related nine-module QA: **86 passed, 1 strict XFAIL** (the preserved stopped
prospective final leak). Setup, full Ruff, mypy (532 source files),
knowledge-check and diff-check passed. Full pytest was not run because
unrelated benchmark-authoring tests may load sealed held-out Test.

Next gate: author a *fresh* synthetic Dev matrix for this proof route,
including public/user collisions and attempted context/field/pin laundering;
then perform paired CPU integration and independent release audit before
considering a separately versioned runtime. Do not rerun the stopped room
pilot to make a positive claim.
