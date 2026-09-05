# Clean Ground Truth Specification

Ground truth is evaluator-only and defines outcomes semantically rather than as
one sample answer. Each record includes required/optional/forbidden tools,
acceptable sequences, order constraints, argument comparators, typed answer
facts, evidence IDs, minimum steps, and a deterministic oracle path.

Supported comparators include normalized text, dates, numeric/money equality,
sets, entity IDs, retrieval-target membership, and SQL result equivalence.
Search queries are correct when they retrieve a target source; SQL is correct
when its result equals the reference query, not when the strings match.

Clarification tasks identify missing slots and accepted clarification terms.
Recovery tasks keep the fault plan private and specify whether an error must be
observed, recovered from, and followed by task success.
