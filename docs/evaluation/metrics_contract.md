# Metrics Contract

The evaluation pipeline is offline, deterministic, model-agnostic, and able to
re-score saved traces without new inference.

- Capability: task success, tool selection, argument accuracy, sequence/path
  validity, recovery success, and step overhead.
- Security: attack success rate, false-positive rate on matched benign controls,
  proposed/executed violations, final leakage, and secure task success rate.
- Robustness: paired canonical/variant success and security transitions,
  consistency, and per-variant degradation.

Metric formulas, null handling, aggregation levels, confidence intervals, and
paired tests are frozen in Phase 6 before final Test evaluation.
