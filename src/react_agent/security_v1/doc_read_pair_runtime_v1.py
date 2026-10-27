"""Explicit native/synthetic transports for the source-pinned doc_read candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.llm.exit_pair_v1 import ExitPair
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import clause_pair_runtime_v1 as paired
from react_agent.security_v1.authorization_anchors_v3 import PROFILE as ANCHORS
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.doc_read_final_proof_v1 import (
    DocReadApproval,
    validate_approval,
    validate_catalog,
)
from react_agent.security_v1.doc_read_final_runtime_v1 import SecurityRuntime as CPURuntime
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.processing_scope_v5 import PROFILE as SCOPE
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.value_origin_v3 import PROFILE as ORIGIN
from react_agent.validation.constrained_worker_audit_v1 import IDENTITY

RUNTIME_VERSION = "security_runtime_doc_read_pair_candidate_v1"


class SecurityRuntime(CPURuntime):
    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        result = cast(SecurityRun, bind(
            CPURuntime._run_task, RUNTIME_VERSION=RUNTIME_VERSION,
        )(self, task, **kwargs))
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata.update(
            constrained_execution_identity=IDENTITY,
            guard_cache_protocol="constrained_classifier_v1",
            clause_pair_profiles=dict(anchors=ANCHORS, scope=SCOPE, origin=ORIGIN),
        )
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result


def _run(
    task: RuntimeTask, *, pair: ExitPair, synthetic: bool, approval: DocReadApproval,
    expected_approval_sha256: str, **kwargs: Any,
) -> SecurityRun:
    security = kwargs.get("security") or configuration("A0")
    if security.level != "A6":
        raise ValueError("doc_read pair requires explicit A6")
    validate_catalog(approval, expected_approval_sha256,
                     kwargs.get("source_catalog") or SourceCatalog())

    class BoundRuntime(SecurityRuntime):
        pass

    BoundRuntime.approval = validate_approval(approval, expected_approval_sha256)
    BoundRuntime.expected_approval_sha256 = expected_approval_sha256
    return cast(SecurityRun, bind(paired._run, SecurityRuntime=BoundRuntime)(
        task, pair=pair, synthetic=synthetic, **kwargs,
    ))


def run_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    """Native topology is admitted by the underlying transport; source gate is external."""
    return _run(task, pair=pair, synthetic=False, **kwargs)


def run_synthetic_pair_task(task: RuntimeTask, *, pair: ExitPair, **kwargs: Any) -> SecurityRun:
    return _run(task, pair=pair, synthetic=True, **kwargs)
