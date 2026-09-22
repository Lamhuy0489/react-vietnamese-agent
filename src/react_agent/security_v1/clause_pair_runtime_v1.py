"""Versioned v12 + constrained guard + ExitPair composition; no global patching."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import constrained_runtime_v1 as constrained
from react_agent.security_v1 import exit_pair_runtime_v1 as observed
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.constrained_host_v1 import ConstrainedRoleBackend
from react_agent.security_v1.guard_bare_json_v1 import PROMPT, bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.processing_scope_v5 import ProcessingScope
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v12 import SecurityRuntime as V12Runtime
from react_agent.security_v1.sql_rows_v1 import RowBindings
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY

RUNTIME_VERSION = "security_runtime_v12_constrained_exit_v1"


class SecurityRuntime(V12Runtime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        if not isinstance(kwargs.get("_worker"), ConstrainedRoleBackend):
            raise ValueError("clause pair requires its task-owned constrained role")
        loop = SimpleNamespace(
            _run_task=bind(
                V5Runtime._run_task,
                WarmModelGuard=constrained.HostClassifier,
                PROMPT=PROMPT,
            )
        )
        body = bind(V12Runtime._run_task, V5Runtime=loop, RUNTIME_VERSION=RUNTIME_VERSION)
        result = cast(SecurityRun, body(self, task, **kwargs))
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata.update(
            constrained_execution_identity=IDENTITY,
            guard_cache_protocol="constrained_classifier_v1",
            clause_pair_profiles=dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
        )
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result


def _run(task: RuntimeTask, *, pair: ExitPair, synthetic: bool, **kwargs: Any) -> SecurityRun:
    # Preserve native admission, role ownership, failure receipts and observer
    # cleanup. Only the per-task host runtime and pre-start scope parser change.
    catalog = kwargs.get("source_catalog") or SourceCatalog()
    scope = partial(
        ProcessingScope,
        resources=ResourceBindings.from_catalog(catalog),
        rows=RowBindings.from_catalog(catalog),
    )
    inner = bind(constrained._run, SecurityRuntime=SecurityRuntime, ProcessingScope=scope)
    bindings = SimpleNamespace(
        run_pair_task=bind(constrained.run_pair_task, _run=inner),
        run_synthetic_pair_task=bind(constrained.run_synthetic_pair_task, _run=inner),
    )
    return cast(
        SecurityRun,
        bind(observed._run, baseline=bindings)(
            task,
            pair=pair,
            synthetic=synthetic,
            **kwargs,
        ),
    )


def run_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    return _run(task, pair=pair, synthetic=False, **kwargs)


def run_synthetic_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    return _run(task, pair=pair, synthetic=True, **kwargs)
