"""D2 without the A1 rule layer (Study 2 Dev tuning round 2, configuration ``d2nrp2``).

D2 (``runtime_d2_v1``) keeps the frozen A1 rule layer (``rules_v1``) under the
control/data rules. On Dev round 1 most benign_auth losses of D2+P2 came from that
layer (``RULE_INJECTION_SIGNAL`` + ``UNAUTHORIZED_EXTERNAL_ACTION``), while D2 rules 2-3
already cover redirection and secret flow. This variant runs the same D2 policy with
the rule layer switched off (``rule=False``), everything else unchanged: same runtime
path, same rules 1-4, same redaction, same tool limits.

The pinned D2 files are not edited (their hashes are part of D2 run identities); the
policy is swapped in with ``bind`` exactly as D2 swaps in its own.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from react_agent.schemas.task import RuntimeTask
from react_agent.security_v1.contracts import SecurityConfig
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.phase5_runtime import Phase5Runtime
from react_agent.security_v1.rules import RulePolicy
from react_agent.security_v1.runtime import SecurityRun
from react_agent.security_v1.runtime_d2_v1 import (
    D2Runtime,
    _D2Phase5Runtime,
    _make_parser,
    _RegisteredD2GuardPolicy,
    _RegisteredD2Policy,
)
from react_agent.security_v1.runtime_v5 import SecurityRuntime as V5Runtime
from react_agent.security_v1.runtime_v14_email_origin_candidate import (
    SecurityRuntime as EmailRuntime,
)

DEFENSE = "D2-NR"


class NoRuleD2Policy(_RegisteredD2Policy):
    """D2 rules 1-4 with the A1 rule component disabled (pass-through)."""

    def __init__(self, config: SecurityConfig, raw_user: str) -> None:
        super().__init__(config, raw_user)
        anchors = getattr(self.component, "anchors", None)
        self.component = RulePolicy(config.model_copy(update={"rule": False}), raw_user)
        if anchors is not None:
            self.component.anchors = anchors


class _NoRulePhase5Runtime(_D2Phase5Runtime):
    _run_task = bind(
        Phase5Runtime._run_task,
        EmailRuntime=SimpleNamespace(_run_task=bind(
            EmailRuntime._run_task,
            V5Runtime=SimpleNamespace(
                _run_task=bind(V5Runtime._run_task, StructuredParser=_make_parser)),
            CandidateRuntimePolicy=NoRuleD2Policy,
            CandidateA2Policy=_RegisteredD2GuardPolicy,
        )),
    )


class D2NoRuleRuntime(D2Runtime, _NoRulePhase5Runtime):
    """D2Runtime whose A1 path builds ``NoRuleD2Policy``; metadata records the variant."""

    def _run_task(self, task: RuntimeTask, **kwargs: Any) -> SecurityRun:
        result = super()._run_task(task, **kwargs)
        path = Path(kwargs["output"]) / "run_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["defense_v2"].update({"defense": DEFENSE, "a1_rule_layer": False})
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        return result
