# Clean Benchmark Categories

| Category | Count | Operational definition |
|---|---:|---|
| `single_source` | 40 | Search/read one internal document or cached page. |
| `parameter_extraction` | 40 | Convert user constraints into correct tool arguments. |
| `multi_step` | 50 | At least one later action depends on an earlier result. |
| `db_document` | 40 | Requires both database and document evidence. |
| `ambiguous` | 25 | Ask for one objectively missing slot without guessing. |
| `error_recovery` | 30 | Encounter a deterministic fault and recover. |
| `no_tool` | 25 | Answer only from information already in the instruction. |

Difficulty is structural: easy is direct/no-tool or one required call, medium
uses two to three dependent calls, and hard uses at least three calls or an
explicit recovery path.
