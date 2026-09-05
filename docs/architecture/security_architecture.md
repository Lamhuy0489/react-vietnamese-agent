# Security Architecture

| Level | Cumulative addition |
|---|---|
| A0 | Baseline schema validation and bounded tools only |
| A1 | Rule/regex guard |
| A2 | Model-based guard |
| A3 | Data-sensitivity control |
| A4 | Untrusted-data/control-influence tracking |
| A5 | Session-level sensitivity + trust policy |
| A6 | Artifact provenance with Pre/Post/Final gates |

A0 purity is required for an interpretable baseline. A6 is the central
technical contribution, but provenance is conservative evidence tracking—not
a claim that the system perfectly knows which text influenced the model.
