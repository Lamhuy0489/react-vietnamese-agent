# Runtime Contract

Phase 1 will freeze interfaces for Agent Runtime, LLM Backend, Structured
Parser, Tool Broker, Tool Registry, Trace Logger, and the eight mock tools.

The runtime accepts a public task and model/backend configuration, then loops
over structured `action` or `final` outputs until completion or the maximum
step limit. It never receives evaluator-only ground truth. Each run starts with
fresh state and emits an observable trace without hidden reasoning.

Security levels are injected through stable gate interfaces so A0–A6 can run
on the same runtime. In rebuild A every level runs on the frozen
`Phase5ClosureRuntime`; A6 uses the value-provenance policy of
`security_v1/a6_provenance_v2.py`, switched on by `activate()` and recorded in
each run identity (`a6_policy`). Notebooks only load configuration, invoke package code,
and save artifacts.
