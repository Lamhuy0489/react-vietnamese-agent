"""A6 v3: A6 v2 plus clause-level document anchors when the user quotes text (rebuild R2).

The frozen v4/v5 processing scope drops every user resource anchor as soon as the
raw instruction contains a quote mark, so an instruction that spells out an exact
JSON payload ("…gửi … payload chính xác {"request":"CITE803"}…") can no longer read
the document it names in another clause ("Đọc AWB_SOURCECLAIM."). On the full
Dev run this denied the first read of every AWB_SOURCECLAIM variant at A4–A6
(decision log 2026-10-26).

A6 v3 keeps that scope and adds anchors found in the instruction with every
balanced quoted span removed, using the same frozen clause rules. Quoted text
never creates an anchor; unbalanced quotes or a ``>`` reply marker add nothing.
Anchors come only from the user instruction, which attack payloads never reach.
Only document and cached-page anchors are added, only at A6; A0–A5, rule and
guard vetoes and every sealed file are untouched.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import react_agent.security_v1.runtime_v14_email_origin_candidate as runtime_v14
from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1 import a6_provenance_v2
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.processing_scope_v5 import ProcessingScope as V5Scope
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.sql_rows_v1 import RowBindings

PROFILE = "a6_provenance_v3"
QUOTE_MARKS = ('"', "'", "`", "“", "”", ">")
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'|`[^`]*`|“[^“”]*”")
_ORIGINAL_SCOPE = getattr(runtime_v14, "ProcessingScope")  # noqa: B009 - not re-exported
_ORIGINAL_RUN = Phase5Runtime._run_task


def unquoted(raw_user: str) -> str | None:
    """The instruction without its quoted spans, or None when quoting is not balanced."""
    stripped = QUOTED.sub(" ", raw_user)
    return None if any(mark in stripped for mark in QUOTE_MARKS) else stripped


class ClauseAnchoredScope(V5Scope):
    def __init__(self, raw_user: str, *, resources: ResourceBindings, rows: RowBindings,
                 enforce: bool = True) -> None:
        super().__init__(raw_user, resources=resources, rows=rows, enforce=enforce)
        if not any(mark in raw_user for mark in QUOTE_MARKS):
            return
        text = unquoted(raw_user)
        if text is None:
            return
        found = V5Scope(text, resources=resources, rows=rows, enforce=enforce).anchors
        if not (found.documents or found.cached_pages):
            return
        self.anchors = self.anchors.model_copy(update={
            "documents": tuple(sorted({*self.anchors.documents, *found.documents})),
            "cached_pages": tuple(sorted({*self.anchors.cached_pages, *found.cached_pages})),
            "explicit_scope": True,
        })


def _run_task(self: Phase5Runtime, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
    level = (kwargs.get("security_config") or configuration("A0")).level
    if level != "A6":
        return _ORIGINAL_RUN(self, task, **kwargs)
    setattr(runtime_v14, "ProcessingScope", ClauseAnchoredScope)  # noqa: B010
    try:
        return _ORIGINAL_RUN(self, task, **kwargs)
    finally:
        setattr(runtime_v14, "ProcessingScope", _ORIGINAL_SCOPE)  # noqa: B010


def profile() -> dict[str, str]:
    return {"name": PROFILE, "module_sha256": hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest(),
        "base": a6_provenance_v2.profile()["module_sha256"]}


def activate() -> dict[str, str]:
    a6_provenance_v2.activate()
    Phase5Runtime._run_task = _run_task  # type: ignore[method-assign]
    return profile()


def deactivate() -> None:
    a6_provenance_v2.deactivate()
    Phase5Runtime._run_task = _ORIGINAL_RUN  # type: ignore[method-assign]
    setattr(runtime_v14, "ProcessingScope", _ORIGINAL_SCOPE)  # noqa: B010
