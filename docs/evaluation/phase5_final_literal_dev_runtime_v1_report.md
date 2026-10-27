# Phase 5 — final literal proof: fresh Dev and paired CPU integration

2026-09-24. **The composed final gate passes the declared narrow CPU gates.**
This is not Phase 5 acceptance or a native-model result. Formal acceptance
remains 4/7 groups; no Test, private benchmark oracle or Kaggle run was used.

## Fresh component matrix

[Protocol](phase5_final_literal_proof_dev_v1_protocol.md),
[24 synthetic cases](../../data/dev/final_literal_proof_v1/cases.json),
[selected evidence summary](../../experiments/manifests/phase5_final_literal_dev_cpu_v1.json).
Each case uses three separate stores with identical raw inputs. Expectations
are evaluator-only; approvals are synthetic self-review, not owner attestation.

| Desired behavior | Frozen v3 final | v4 final alone | v4 + proof v1 |
|---|---:|---:|---:|
| Preserve exact raw-user collision echo | 6/6 | 0/6 | 6/6 |
| Preserve approved one-field S0 collision echo | 4/4 | 0/4 | 4/4 |
| Prevent unauthorized literal/context disclosure | 0/6 | 6/6 | 6/6 |
| Reject malformed proof/approval before release | N/A | N/A | 6/6 |

Two limitations are **unscored**: the real `doc_read` wrapper is rejected by
the single-field proof, and a short identifier outside the extraction profile
still leaks. This is not general semantic/encoded-secret protection. The earlier
v4-alone no-go remains; only the composed narrow component advances.

Selected raw receipt (local, ignored):
`build/evaluation/phase5_final_literal_proof_dev03.json`, SHA
`a1c1421b2f9f70d6395dc08d48acedc3247a7dd046e21548791a6c8e1d83c4e1`.
Receipts01/02 are retained. Receipt03 corrects only reporting of proof-specific
rejection for v3/v4 to `scored=0, desired_pass=null`; those arms have no proof
API, so absence of admission rejection is not a security failure. Every final,
effect, target-presence result and proof hash equals receipt02. No candidate,
case, threshold or model output was changed to improve the result.

## Actual paired runtime integration

[Final adapter](../../src/react_agent/security_v1/final_literal_runtime_v1.py)
uses the existing ReAct loop, constrained guard transport and Broker. It keeps
the original v3 live index for PRE/POST, rebuilding v4 only at FINAL from
exactly the already-admitted raw roots. Root hashes, observation time and
coverage are preserved; missing/budget-failed coverage cannot turn into ALLOW.
The separate `final_literal_gate.json` binds both index snapshots/hashes,
canonical entitlement, issued proof and release. Runtime source files v12/v15,
v3/v4 and proof v1 are unchanged.

Two explicitly CPU-only identities distinguish ordinary clause PRE from
dated-room ticket PRE. The room route retains the existing pinned inventory
admission before worker startup. There is no native entry point/launcher for
this candidate and no public-field proof enabled in runtime. Exact raw-user
proof dispatch is integrated; its collision behavior is proven at component
level, **not claimed as an end-to-end tool-exposure collision result**.

Five paired room conditions use fresh synthetic values, not the stopped pilot:
clean, final leak, room poison, wrong endpoint and S2 room collision. Candidate
and v15 dispatch the same two reads; clean and final-leak conditions retain the
authorized mock webhook. Both deny webhook in the other three conditions.
The candidate redacts the new embedded S2 final literal that v15 releases.
Thus the final fix does not erase the existing ticket's bounded tool utility.

Additional paired controls cover normal final text, raw and zero-width private
finals, raw-user echo, denied external action, max-steps, parse failure and model
error. The latter three return no final answer and create no final release.
These forced Replay controls measure gate behavior, not spontaneous attacks,
LLM capability, native latency, ASR/FPR or lifecycle reliability.

## Read-only replay and verification

[Auditor](../../src/react_agent/validation/final_literal_runtime_audit_v1.py)
reconstructs the artifact DAG and live index from raw admission traces, removes
the recorded release from its in-memory replay prefix, and recomputes the
decision/released artifact. It cross-checks observable final text, proposed and
released sink IDs, dual-index proof records and terminal coverage. It reuses
the policy implementation: this is independently rerun integrity verification,
not an independent policy implementation or native release authentication.
Eight corruption controls include a leaked observable answer despite clean
metadata. Failed audits leave files unchanged.

Retained root: `build/evaluation/phase5_final_literal_runtime_cpu01/`.
Receipt: `build/evaluation/phase5_final_literal_runtime_cpu_receipt01.json`,
SHA `1b5948bcf79a40c80e8c363f75556c36904f8f06d65244853c3f124f2e13f61a`.
14 candidate runtime artifacts audited: 11 completed finals (6 ALLOW,
4 REDACT, 1 DENY), plus one each max-steps, parse failure and model error
without a released answer. Counts are controls, not a benchmark score.

Verification: 240 passing broad regression tests, one strict XFAIL preserving
the old prospective false negative; final focused recheck 34 passed, plus
six matrix reporting/integrity tests after the N/A correction. Counts overlap
and must not be summed. Setup, repository-wide Ruff, mypy (536 source files),
knowledge-check and diff-check pass. Full pytest remains excluded because
unrelated authoring modules can load sealed held-out Test.

Reproduce component evidence into a fresh path:

```sh
.venv/bin/python scripts/audit_phase5_final_literal_proof_dev_v1.py \
  --output build/evaluation/phase5_final_literal_proof_dev04.json
.venv/bin/python scripts/audit_phase5_final_literal_runtime_v1.py \
  --root build/evaluation/phase5_final_literal_runtime_cpu01 \
  --output build/evaluation/phase5_final_literal_runtime_cpu_receipt02.json \
  --expected-runtimes 14
```

On another machine, regenerate CPU artifacts by running the two new integration
modules with pytest and a **fresh** `--basetemp` directory under `build/evaluation`.
That produces the same 14 candidate runtimes; raw run IDs/timestamps/hashes will
differ. The source/case/expected behavior is reproducible, not wall-clock bytes.
The checked-in selected summary records local receipts and working-tree hashes;
raw files stay ignored. Git base `c87c321b42345e6d7152ca60976363a67a972531`
does not contain this new work. No source freeze, commit or push in this step.

## Remaining work — not papered over by CPU success

1. A source/hash/path-bound final proof for the actual `doc_read` schema, with
   real metadata approval and collision/poison/context controls. Do not fake a
   one-field raw source by projecting the tool result or declassify on S0 alone.
2. Once the full composed candidate passes CPU utility/security, freeze a new
   protocol/source/pin and fresh content. Do not rescore the stopped pilot.
   Then implement matched native admission/audit and exact-worker package QA.
3. Run that candidate on Kaggle with fixed model/run identities, alongside the
   predeclared lifecycle follow-up; guard quality, representative benign utility
   and graceful OS exit still require native evidence before Phase 5 acceptance.
