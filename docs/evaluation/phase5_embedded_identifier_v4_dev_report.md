# Phase 5 — embedded sensitive identifier v4, development-only

The stopped prospective pilot found a specific final-sink blind spot:
mixed-alphanumeric private literals embedded in S2 free text were not
independently indexed. This new opt-in **development** candidate adds a
bounded supplemental `IDENTIFIER` origin for mixed letter/digit tokens of
length 8–64 from observed S1/S2 `FREE_TEXT` roots. It preserves the original
artifact ID, source hash, JSON pointer, sensitivity and trust. Public S0
prose never creates a protected supplemental origin. Values already covered
by a typed origin are not duplicated. A 64-token/source and existing index
record/byte budget fail closed when exceeded.

Implementation: [`value_origin_v4.py`](../../src/react_agent/security_v1/value_origin_v4.py).
It subclasses v3; frozen v3, v12 and v15 runtime dispatch are unchanged.
It does **not** recognize arbitrary secrets, quoted paraphrases, encoded
values, tokens shorter than eight characters or values outside this ASCII
profile. Indexing common mixed-alphanumeric terms may increase false blocks;
the tiny unit controls do not estimate that cost.

Five independent synthetic Dev unit controls pass: v3 misses a new
`ORBITALPHA5629` specimen while v4 preserves its S2 origin; the existing
final entitlement sink redacts it; public text and common prose remain
unprotected by this supplemental extractor; typed `ROOM3176` is not
duplicated; and exhausted budget invalidates index coverage. These controls
do **not** rerun or rescore the stopped prospective casebook. There is no
native/model execution, runtime integration, Phase 5 acceptance change or
claim of general secret-leak prevention.
The combined seven-module room/inventory/package/v4 suite reports
65 passed, 1 strict XFAIL; the XFAIL remains the **old** stopped pilot's
final leak, not a test of this new runtime (which does not yet exist).

Next: independently measure protected-literal recall *and* benign
false-blocks on a broader synthetic Dev corpus, then decide whether a
separately versioned runtime is warranted. Any later prospective comparison
needs a new protocol, source freeze, pin and fresh content; the failed pilot
remains a negative finding.

Postscript: the [18-case Dev matrix](phase5_embedded_identifier_dev_matrix_v1_report.md)
now finds 6/6 narrow leaks blocked but 3/3 user/public collisions suppressed.
The declared gate rejects runtime integration of v4 as-is. The paragraph
above records the prior planned next step, not an outstanding acceptance claim.
