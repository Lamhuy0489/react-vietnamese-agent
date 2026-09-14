# Bounded SQL row scope v5 / runtime v10

Successor to immutable scope v4/runtime v9. Phase 5 only; no benchmark rewrite,
Test/private oracle, SQL execution outside Broker, prompt/model/guard change or
semantic retry. Inputs: raw user instruction and host SourceCatalog metadata.

Recognize only explicit identifier projections, one table and WHERE key = literal
or key IN (literals). Values are bounded AWB/AUX synthetic identifiers, not SQL
expressions. Track projected columns separately from the predicate column. No
star, aliases, functions, joins, OR, nested queries, comments, semicolon, COLLATE,
quoted identifiers, parameters or arbitrary string literals. Unsupported means
unassessed, not authorized. The parser neither imports SQLite nor executes SQL.

Host row bindings derive only exact single-row database source identities from
canonical catalog bindings, never payload contents or evaluator row grants.
Inventory is not permission. For bound row environments all DB reads require
supported finite rows, matching table/key, and raw-user column grants for every
selected row. Dropping WHERE, adding a row/column or changing table/key cannot
inherit permission. Unfiltered legacy SQL retains v4 behavior only without a host
row inventory; unsupported filtered SQL fails closed. A0–A3 do not enforce v5.

Authorization extraction is deliberately bounded: affirmative, unquoted,
unconditional read clauses with exactly one known row; explicit `cột/column/
trường/field name`, or `Đọc/read name [và/and name] của/of row`. A named table in
the clause must match the host row binding. Preserve the raw instruction hash,
negative/conditional rejection, per-row column pairs and fresh state. Missing
columns remain denied; do not infer `note` from “số ghế” or consult an oracle.
Predicate-key access is tracked, not implicitly permission to project that key.

Runtime v10 and a separate pair adapter compose v5 with existing v4 resource
bindings; no global patch. Original prompts, tool arguments/results, guard and
transport stay unchanged. Alternate SQL spellings without exact source labels
retain conservative catalog defaults; no invented S0 label inheritance.

Acceptance: parser mutation/limits, row/column binding negatives, read-only public
Dev selection, actual-spawn A0–A6 Broker traversal and pre-execution denials,
independent runtime/guard joins, full setup/Ruff/mypy/pytest, immutable source/
raw/data hashes and knowledge handoff. CPU scripted evidence is not native GPU
quality, ASR/FPR or broad language understanding. Grouped Dev dispatch remains
disabled until exact package/run identity and native preflight are complete.
