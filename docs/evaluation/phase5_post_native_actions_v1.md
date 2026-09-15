# Phase 5 — work after the first complete native schedule

2026-09-15. This plan preserves the [112-task baseline](phase5_grouped_v3_complete_report.md).
It does not authorize replacing its failures, changing dataset grants, selecting
the best rerun, or promoting to Phase6/7. The following are separate work items,
not completed implementations or scheduled GPU jobs.

## 1. Make malformed guard output diagnosable without storing raw text

Update2026-09-15: the opt-in CPU component is implemented and71focused tests
pass; [contract](../architecture/phase5_guard_diagnostics_v2_contract.md).
The separate versioned observer/join is now also implemented:139 focused CPU
tests pass, including real spawned A2–A6 scripted runs and adversarial evidence
mutations. [Observer/host witness contract](../architecture/phase5_guard_observer_v2_contract.md),
[QA](../../experiments/manifests/phase5_guard_observer_v2_cpu01.json).
Neither component is wired into native workers. Next is a separate synthetic
native protocol and isolated package preflight, not a Dev rerun or prompt repair.

Update after package acceptance: the lazy HF observer composition and separate
four-task synthetic runner now have an [accepted CPU package rehearsal](phase5_observer_package_v2_report.md).
Both archive/expanded layouts pass; actual HF execution remains pending. Next
are the native metrics/source audit and notebook launcher for this schedule,
followed by a freshly verified package and remote admission.

Observed:30 PRE responses are malformed JSON on SOURCEBINDING/LINKPAGE/QUERYLEAK;
all30 become model_error, with18 further POST backend failures after retirement.
The current sidecar stores only hash, character count and `json_syntax`; this
cannot distinguish a Markdown wrapper, syntax truncation or another format error.
Do not infer the missing raw response or silently relax the accepted parser.

Next concrete implementation: a versioned diagnostic sidecar with bounded enum/
boolean fields for JSON framing, optional fence presence, parser-error category
and offset, size/depth limits, plus existing identity hashes. No snippets, free
text, hidden reasoning, secrets or oracle values; no prompt/policy behavior change.
Use explicitly synthetic valid/malformed JSON fixtures to test determinism,
privacy, size limits and trace joins. Keep diagnostic v1 and native baseline intact.

Only after CPU/schema/reproducibility checks freeze a separate synthetic native
diagnostic protocol. Keep new probes independent from Test and retain every
failure. A candidate prompt/parser/runtime change is a distinct later decision,
not an automatic consequence of adding observability. Verify whether POST
BACKEND_FAILURE propagation follows the intended fail-closed policy before
changing retirement behavior.

## 2. Review user-task/tool grounding without rewriting the benchmark

LINKMAIL/ENCODED finalize without actions; ROWLIST A0–A3 query a nonexistent
table, A4–A6 refuse reads with the known missing-column-grant boundary. Inspect
only public user instructions, tool schema/catalog and observable traces. Check
which intended steps and permissions were actually provided; never derive
runtime authorization or resource names from private ground truth.
New synthetic positive/negative controls can test an explicitly declared
grounding improvement. Preserve existing task/overlay hashes and original
results; do not claim a data fix or benign-utility gain until separately measured.

## 3. Diagnose graceful lifecycle and finish acceptance mapping

All192 workers were reaped and112 task VRAM recoveries passed, but13 workers
needed TERMINATE. Native normal shutdown is therefore not uniformly graceful.
Use saved lifecycle/timing evidence to locate shutdown stages, then a separate
synthetic CPU process control before any native diagnostic. Do not silently
increase deadlines or change the worker topology of the baseline.

Close each affected detailed DoD with evidence, not a file count or schedule
percentage. Freeze rules, guard prompt/model, policy and architecture only after
the remaining semantic/lifecycle checks pass. No new inference job is pending
at the end of the first complete schedule; the immediate next step is item1's
CPU-only diagnostic implementation.
