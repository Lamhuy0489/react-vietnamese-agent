# Typed field-reference prototype v1 — bounded dataflow experiment

2026-09-25. Owner explicitly approved a separate limited provenance/final
restructure prototype, preserving benchmark and old results, integrating only
after controls. No production runtime, benchmark, model prompt or A0–A6 release
is replaced. This is a text-field component experiment, not a new agent.

## Interfaces and trust boundary (before implementation)

Host supplies a hash-pinned Grant: run/task/raw-user/catalog identities, readable
document IDs, allowed output field selectors, S0 clearance, budget. It is public
authorization metadata, contains no expected answer/attack labels/oracle. A real
natural-language-to-Grant compiler is NOT implemented; correct host authorization
is an explicit assumption. This experiment must not be reported as paraphrase
comprehension, independently reviewed labels or an end-to-end LLM utility gain.

Host reads documents through the existing Tool Broker and admits only successful
original doc_read `{doc_id,title,content}` string records matching the catalog.
References bind run, grant, admitted artifact ID, full source hash, field path and
text type. Only `/content` and `/title` text selectors, explicitly allowed by the
grant, can be released. Unknown/forged/cross-run/changed refs fail closed. A source
root is never fabricated from a projected field. Repeated real observations are
distinct roots and can be referenced without globally declaring ambiguity.

Plan: 1–8 text references, a fixed separator from empty/space/newline, and up to
four closed transforms from base64/hex. No model-supplied literal, free-form final,
destination, expression, Python code or arbitrary template is accepted. Concatenation
joins all selected labels; encoding preserves them. Host-rendered value lineage
and all observed exposure IDs are recorded separately, never claimed as model
causal lineage. The immutable ArtifactStore enforces no label downgrade/trust upgrade.

Final sink requires allowed fields, S0 effective sensitivity, and an explicit
host upstream-veto flag (default denies). Trust remains independent; public
UNTRUSTED data is data, never execution authority. This flag is a component
interface, not a working LLM guard or proof of control-flow protection. Denied
or malformed output returns no value. No external sink is implemented in v1.
Limits: 64 broker observations, 64 KiB source/text output, 8 refs, 4 transforms.

## Matched controls and decision rule

Compare the same renderer/reference language/Grant/inputs under two named
component arms: conservative exposure-baseline and selected-field candidate.
These are NOT official A5/A6 scores. Baseline uses maximum observed sensitivity;
candidate uses selected value parents. Grant scope/budgets/upstream veto apply
to both. Old v12 and doc_read results are not merged with these measurements.

Before executing the matrix lock a fresh synthetic fixture and eight benign
cases (public prose, multiline, public/private collision, repeated public read,
public Base64, public hex, two public fields concatenated, trusted public) plus
eight deny cases (private identity/Base64/hex, mixed public-private, ungranted
field, wrong source hash, unknown reference, upstream veto). Additionally unit
test raw literals, cross-run/grant, malformed schema, missing metadata, tool
failure, transform budget, S1/S2 × TRUSTED/UNTRUSTED and byte budgets.

Candidate must retain all declared public outputs and deny all declared negative
cases to warrant a follow-up integration experiment. If it fails, retain the
failure and do not silently change the controls or call the phase complete.
Record actual Broker traces, append-only artifacts, plan, final decision/output,
source/fixture/Grant hashes and CPU timings. No inference, Test, external network,
benchmark regeneration or source-freeze commit is needed for this prototype.

Follow-up (not implied by CPU pass): explicit intent-source validation, controlled
ReAct plan interface, prior veto composition, unknown/free-form handling, mock
external sink integration, and one comparable A0–A6 representation before a
source-pinned native experiment. No guarantee against control-flow/implicit-flow
attacks or arbitrary semantic disclosure is claimed.
