# Phase 5 — doc_read native route: CPU admission and exact-worker QA

2026-09-25. Implemented the native-capable route for the raw-doc final proof,
full pair/Broker audit, externally pinned admission, immutable checkpoint/resume
and isolated worker packaging. **No native model inference or Phase 5 acceptance
is claimed.** [Protocol](phase5_doc_read_native_v1_protocol.md).

## Implementation and scope

- [Pair adapter](../../src/react_agent/security_v1/doc_read_pair_runtime_v1.py)
  has identity `security_runtime_doc_read_pair_candidate_v1`. Native and
  synthetic transports are separate. It preserves the previous CPU proof
  algorithm and frozen v3 PRE/POST; only FINAL uses the approved doc-read proof.
- [Admission](../../src/react_agent/validation/doc_read_native_admission_v1.py)
  requires an externally pinned manifest, exact committed source tree, approved
  public source metadata, task/catalog/environment/configuration hashes,
  publisher inventory, agent runtime-content revision, guard snapshot revision
  and seed. Only the registry's three environment files are permitted; hidden
  extra files reject even when the caller refreshes the environment hash.
- [Dispatcher](../../src/react_agent/llm/doc_read_native_dispatch_v1.py)
  verifies that imported runtime code is actually inside the admitted project.
  One fresh output, explicit pair close, full audit and source/input re-admission
  precede checkpoint creation. Complete resume is read-only; partial/failure
  evidence is retained and cannot silently relaunch workers.
- [Joined audit](../../src/react_agent/validation/doc_read_pair_audit_v1.py)
  verifies constrained guard/cache, witness and exit records plus raw final
  replay. Every doc_read root joins exactly one proposed/executed/result sequence,
  matching call/run/task/step, raw ToolResult and catalog labels.
  [Release audit](../../src/react_agent/validation/doc_read_native_release_v1.py)
  also compares actual task/configuration/model-role identities and immutable
  checkpoint inventory. Integrity replay shares policy code; this is not an
  independent semantic evaluator or publisher attestation.

The launcher is [run_phase5_doc_read_native_v1.py](../../scripts/run_phase5_doc_read_native_v1.py).
Its native boundary has only been tested with stubs here; the pair adapter/audit
also runs real synthetic CPU child processes. These are distinct kinds of evidence.

## Exact worker rehearsal and a preserved failure

[Builder](../../scripts/prepare_phase5_doc_read_package_v1.py) packages the
public dependency closure, excluding host QA/authoring/Dev/prospective payloads.
It materializes archive and expanded layouts in separate fresh Python venvs,
installs hash-pinned local wheels without network, checks native imports/CLI
and source origin, exercises eight mock tools and 21 clean Dummy tasks per
layout, then verifies complete/missing-only clean resume and unchanged source.
The clean runner's missing-only resume is separate from the native dispatcher's
stricter partial-task triage rule.

Historical package01/02 passed earlier source revisions. Package03 stopped at
the new imported-source check: `react_agent.validation` is intentionally a
namespace because the regular initializer imports host QA. Diagnosis reproduced
the exact archived source and confirmed its sole namespace path was in-tree.
The correction admits only that named namespace with one exact pinned path;
unknown/out-of-tree/multiple paths still reject. **The initializer was not
added to the worker**, and the check was not disabled. Package03 is preserved
without a successful preflight receipt. The builder now saves stdout/stderr
and return code before raising on a failed command; package03 predates that
logging fix, so its captured stderr was unavailable in its own evidence folder.

Selected final rehearsal is `build/kaggle/phase5_doc_read_package04/` (ignored).
It is development source, not a native release: `source_commit=null`, Git base
c87c321b42345e6d7152ca60976363a67a972531, no model/prospective run. Earlier
packages are not source evidence for the final revision.
[Selected hashes and QA summary](../../experiments/manifests/phase5_doc_read_native_cpu_v1.json).

Reproduce into a fresh path (never overwrite existing evidence):

```sh
.venv/bin/python scripts/prepare_phase5_doc_read_package_v1.py \
  --output build/kaggle/phase5_doc_read_package_fresh
.venv/bin/pytest -q tests/unit/test_doc_read_native_admission_v1.py \
  tests/unit/test_doc_read_package_v1.py tests/integration/test_doc_read_pair_runtime_v1.py
```

The selected package uses local macOS wheels and validates packaging/imports,
not Linux CUDA compatibility or native model quality. Committed mode refuses
any worker file missing from or differing from the actual Git source commit.

## Verification and next concrete step

Focused final suite: **53 passed** (29 admission/source/dispatch, 6 closure,
18 pair/Broker tests). Includes wrong pins/inputs, model identity mismatch,
worker/audit failure, absent checkpoint, raw corruption, read-only resume,
namespace shadowing, raw ToolResult corruption, Broker order and step mismatch.
Unit harness source bytes/native workers are explicitly simulated; the synthetic
pair tests exercise actual observable process/guard/Broker/final joins.
Full pytest is deliberately not used because unrelated authoring tests load
sealed held-out Test. Final wider regression: **374 passed, 1 strict XFAIL**
in 131.38 seconds (375 collected; overlapping with the 53 focused tests).
JUnit receipt/hash are recorded in the selected summary. Prior pilot leak
remains a strict XFAIL, not erased. Setup, Ruff, mypy (549 source files),
knowledge-check and diff-check pass.

Next: prepare a fresh prospective metadata-only approval and matched baseline/
candidate run design with scoring kept host-side; then one coherent source
freeze/push, committed exact-worker rehearsal and externally pinned task payloads
before Kaggle. Do not tune on/relabel/resubmit the stopped pilot. Approval
chronology/owner attestation is not supplied by these synthetic CPU fixtures.
Native guard quality, representative benign utility and graceful OS exit remain
open; formal Phase 5 remains 4/7 ≈ 57% acceptance groups.

The project/repro skills kept the Test sealed, failure evidence intact and the
source freeze separate from working-tree rehearsal. No new Kaggle notebook or
Dataset exists, so no remote URLs are invented. No credentials/account access
were needed; no commit or push was made. User report/PDF/figures are untouched.
