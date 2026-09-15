# Phase 5 bare-JSON candidate — CPU preflight

2026-09-15. Candidate source `f7492fae80876891237fcd37084e79ed5af60a2e`.

The candidate is a separate prompt-only protocol following the terminal observer
finding. It adds a bare-JSON/no-Markdown instruction, while parser, schema,
model, generation, tools, fallback and lifecycle configuration remain fixed.

The exact archive and expanded package mounts both passed. Each used a fresh
isolated Python 3.11 environment, offline wheels, source/hash verification,
eight tool schemas, 21 public clean Dummy tasks and missing-only resume. The
candidate observer exercised CALC/DOC × A2/A6 in three synthetic conditions:
valid (4/4 completed), trailing-comma (4/4 retained model errors), and fenced
(4/4 retained model errors). No model weights were loaded, no GPU was used and
no Test/private ground truth was accessed. These CPU conditions test plumbing,
not LLM quality or a claim that prompt wording fixes native behavior.

Receipt: [preflight manifest](../../experiments/manifests/phase5_guard_bare_json_package_v1_preflight01.json).
Package: `build/kaggle/phase5_guard_bare_json_package_v1_preflight01`.
Access check 2026-09-15: owner `huylmhuhu`, GPU remaining 22.80h, guard15
Dataset ready/current v1. Candidate was submitted once as private notebook
[guard-bare-json-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-guard-bare-json-v1),
version1, kernel ID134511636; remote source hash matches the package. It was
`RUNNING` at submission receipt time. [Submission receipt](../../experiments/manifests/phase5_guard_bare_json_submission01.json).

Open: verify terminal, download fresh output, run a source/bootstrap/native audit
twice, and record guard framing, tool path, timing and lifecycle. Keep the closed
observer v2 output immutable. Phase 5 acceptance remains open; no Test run or
semantic retry is authorized.
