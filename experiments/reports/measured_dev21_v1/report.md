# Measured clean_v1.1 Dev pilot

21 fixed Dev tasks; 95% cluster-bootstrap intervals (5,000 draws, seed 2026).

| Model | Strict success | 95% CI | Mean s/task | Median | p95 | Output tok/s* | Peak GiB GPU0 / GPU1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemma4 | 6/21 (28.6%) | 9.5%–50.0% | 11.66 | 11.25 | 24.47 | 8.11 | 2.79 / 13.16 |
| qwen7b | 3/21 (14.3%) | 0.0%–31.6% | 10.92 | 7.48 | 21.46 | 9.27 | 7.16 / 8.90 |

*Generation throughput includes prefill and special output tokens; tokenizers differ.
Task times include tool calls and schema retries; load/warm-up are separate in JSON.
Single run per condition: spread reflects task differences, not repeat-run variance.
Strict success requires annotated paths; correct final facts alone may fail.
Historical Qwen 3B is excluded from controlled timing comparisons. Test remains sealed.
See docs/evaluation/dev21_performance_protocol.md for design and limitations.

## Execution and setup

| Model | Schema validity | Calls / parse errors | Input / output tokens | Load / warm-up s | Latency SD s | Success-only mean s (n) |
| --- | --- | --- | --- | --- | --- | --- |
| gemma4 | 100.00% | 59 / 0 | 74686 / 1982 | 47.13 / 2.16 | 7.54 | 7.33 (6) |
| qwen7b | 94.74% | 57 / 3 | 68117 / 2120 | 40.29 / 1.62 | 8.23 | 2.47 (3) |

Success-only subsets differ; their latency is not a matched speed comparison.

## Category diagnostics

| Category | gemma4 | qwen7b |
| --- | --- | --- |
| ambiguous | 1/3 | 0/3 |
| db_document | 0/3 | 0/3 |
| error_recovery | 0/3 | 0/3 |
| multi_step | 2/3 | 0/3 |
| no_tool | 3/3 | 3/3 |
| parameter_extraction | 0/3 | 0/3 |
| single_source | 0/3 | 0/3 |

## Failure indicators (overlap; do not sum)

| Indicator | gemma4 | qwen7b |
| --- | --- | --- |
| answer_facts | 9 | 14 |
| arguments | 13 | 15 |
| clarification_question | 0 | 2 |
| fault_observation | 3 | 2 |
| forbidden_tool | 0 | 2 |
| required_evidence | 10 | 12 |
| terminal:max_steps | 1 | 0 |
| tool_sequence | 13 | 14 |
| unresolved_tool_error | 4 | 7 |

## Paired differences (left minus right)

| Pair | Success difference pp [95% CI] | Mean latency s [95% CI] |
| --- | --- | --- |
| gemma4 − qwen7b | 14.29 [0.00, 31.58] | 0.75 [-3.69, 4.83] |
