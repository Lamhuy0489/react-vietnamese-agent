# Architecture

The project is a single-agent ReAct evaluation system with deterministic mock
tools, observable traces, security configurations A0–A6, and a separate
evaluation pipeline.

```mermaid
flowchart LR
    Task[Task] --> Runtime[Agent Runtime]
    Runtime --> Backend[LLM Backend]
    Backend --> Parser[Structured Parser]
    Parser --> Gates[Security Engine A0-A6]
    Gates --> Broker[Tool Broker]
    Broker --> Tools[8 Mock Tools]
    Tools --> Artifacts[Artifact Store]
    Artifacts --> Runtime
    Runtime --> Final[Final Answer]
    Runtime --> Trace[Observable Trace]
    Trace --> Eval[Offline Evaluator]
```

The Phase 1 implementation freezes the runtime, schema, broker, tool, and trace
interfaces. Later phases add normalization, artifact/provenance tracking,
security gates, and evaluation without moving core logic into notebooks.

Detailed contracts:

- `docs/architecture/runtime.md`
- `docs/architecture/tool_contracts.md`
- `docs/architecture/security_architecture.md`
- `docs/architecture/module_map.md`
