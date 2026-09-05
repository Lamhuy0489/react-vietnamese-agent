# Module Map

Planned package boundaries:

```text
react_agent
├── agent
├── llm
├── schemas
├── parser
├── tools
├── broker
├── environment
├── logging
├── normalization
├── artifacts
├── provenance
├── security
└── evaluation
```

Phase 1 creates only baseline/runtime modules. Later package directories are
added in their owning phase rather than as premature placeholder code. Run
`python scripts/generate_code_map.py` to regenerate the import graph from real
source imports.
