#!/usr/bin/env python3
"""Micro-benchmark of the broker gate: v1 (D2) against BrokerGuard v3, no LLM.

For every Dev v4.1 fixture: build the policy from u (v3 includes the P(u) extraction),
feed the fixture's source content to ``post`` (C2 labels it) and decide the oracle's sink
actions with ``pre``. Times are wall-clock per call (``perf_counter_ns``), the median of
``--repeat`` runs per fixture, reported as median / p95 / max in microseconds. The tool
calls themselves are not executed, so this isolates the gate's own cost; the end-to-end
latency share comes from ``run_metrics_v1`` (``gate_pre_seconds``) in agent runs.

Dev only; source content is passed to the policy and never printed.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust
from react_agent.schemas.agent_output import Action
from react_agent.security_v1.contracts import PolicyObservation, configuration
from react_agent.security_v1.runtime_d2_v1 import _HOLDER as D2_HOLDER
from react_agent.security_v1.runtime_d2_v1 import D2Policy
from react_agent.security_v3 import brokerguard_v3_v1 as v3

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/adversarial/release_dev4_1"
SINKS = {"send_email_mock", "post_webhook_mock"}


def _quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
    return {"n": len(ordered), "median_us": round(statistics.median(ordered), 1),
            "p95_us": round(p95, 1), "max_us": round(ordered[-1], 1)}


def _timed(fn: Callable[[], Any], repeat: int) -> tuple[float, Any]:
    best: list[float] = []
    out: Any = None
    for _ in range(repeat):
        start = time.perf_counter_ns()
        out = fn()
        best.append((time.perf_counter_ns() - start) / 1000)
    return statistics.median(best), out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/rebuild_c/broker_microbench_v1.json")
    args = parser.parse_args()
    oracles = {o["family_id"]: o for o in json.loads(
        (RELEASE / "private/oracles.json").read_text(encoding="utf-8"))}
    rows = [json.loads(line) for branch in ("benign_auth", "benign_plain", "attack")
            for line in (RELEASE / f"dev_{branch}.jsonl").read_text(encoding="utf-8").splitlines()
            if line]
    policies: dict[str, Callable[[str], Any]] = {
        "v1": lambda u: D2Policy(configuration("A1"), u),
        "v3": lambda u: v3.BrokerGuardV3Policy(configuration("A1"), u),
    }
    report: dict[str, Any] = {"release": "dev4_1", "fixtures": len(rows), "repeat": args.repeat,
                              "python": platform.python_version(), "machine": platform.machine(),
                              "results": {}}
    token = D2_HOLDER.set([])
    try:
        for name, make in policies.items():
            build, post, pre = [], [], []
            for row in rows:
                user = row["task"]["instruction"]
                oracle = oracles[row["family_id"]]
                spec = (oracle.get("auth_oracle") if row["branch"] == "benign_auth"
                        else oracle["oracle"]) or {}
                key = "negative_actions" if row["branch"] == "attack" else "safe_actions"
                actions = [Action(name=a["name"], arguments=a["arguments"])
                           for a in spec.get(key, []) if a["name"] in SINKS]
                t_build, policy = _timed(lambda u=user, m=make: m(u), args.repeat)
                build.append(t_build)
                observation = PolicyObservation(
                    artifact_id="ART_BENCH", content=row["content"], source_type=SourceType.TOOL,
                    sensitivity=Sensitivity.PUBLIC, trust=Trust.UNTRUSTED)
                t_post, _ = _timed(lambda p=policy, o=observation: p.post(o), 1)
                post.append(t_post)
                for action in actions:
                    t_pre, _ = _timed(lambda p=policy, a=action: p.pre(a), args.repeat)
                    pre.append(t_pre)
            report["results"][name] = {"build_policy": _quantiles(build),
                                       "post_observation": _quantiles(post),
                                       "pre_sink_call": _quantiles(pre)}
            print(name, json.dumps(report["results"][name]), flush=True)
    finally:
        D2_HOLDER.reset(token)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
