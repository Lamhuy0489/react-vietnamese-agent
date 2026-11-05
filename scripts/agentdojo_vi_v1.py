#!/usr/bin/env python3
"""AgentDojo-VI: Vietnamese Banking and Slack suites on top of agentdojo==0.1.35 (WP6).

Runs in ``.venv-agentdojo``. The Vietnamese suite is the English suite with:

- ``environment.yaml`` / ``injection_vectors.yaml`` from ``data/agentdojo_vi/<suite>/``;
- each user task's ``PROMPT`` from ``data/agentdojo_vi/<suite>/user_tasks.yaml``;
- each injection task's ``GOAL`` from ``data/agentdojo_vi/injection_tasks.yaml`` (owner/Minh
  translate; null keeps the task unusable for attacked VI runs);
- utility and security checks wrapped by ``check_equivalents.yaml``: Vietnamese phrases are
  mapped to the English literals that AgentDojo's own ``utility``/``security`` look for, then
  the original function runs (security only for the Slack tasks that match keywords).

Tools, ground truth and checks stay AgentDojo's code. ``check`` runs ``TaskSuite.check()``
(ground truth must solve every user task and see every injection vector)::

    .venv-agentdojo/bin/python scripts/agentdojo_vi_v1.py check
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/agentdojo_vi"
VERSION = "v1.2.2"
SUITES = ("banking", "slack")
_THOUSANDS = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{3})(?![\d])")


def equivalents(suite: str, kind: str = "utility") -> list[tuple[str, str]]:
    table = yaml.safe_load((DATA / "check_equivalents.yaml").read_text(encoding="utf-8"))
    pairs = table[suite] if kind == "utility" else table["security"][suite]
    return sorted(((str(a), str(b)) for a, b in pairs), key=lambda p: -len(p[0]))


def map_text(text: str, pairs: list[tuple[str, str]]) -> str:
    for vi, en in pairs:
        text = re.sub(re.escape(vi), en.replace("\\", "\\\\"), text, flags=re.IGNORECASE)
    return text


def map_answer(text: str, pairs: list[tuple[str, str]]) -> str:
    return _THOUSANDS.sub(r"\1\2", map_text(text, pairs))


def system_message() -> str:
    return (DATA / "system_message.txt").read_text(encoding="utf-8").strip()


def _mapped(environment: Any, pairs: list[tuple[str, str]]) -> Any:
    return type(environment).model_validate_json(
        map_text(environment.model_dump_json(), pairs))


def _wrap_security(task: Any, pairs: list[tuple[str, str]]) -> None:
    if not pairs:
        return
    original = task.security

    def security(model_output: str, pre_environment: Any, post_environment: Any) -> bool:
        return bool(original(map_answer(model_output, pairs), _mapped(pre_environment, pairs),
                             _mapped(post_environment, pairs)))

    task.security = security


def _wrap_utility(task: Any, pairs: list[tuple[str, str]]) -> None:
    original = task.utility

    def utility(model_output: str, pre_environment: Any, post_environment: Any,
                strict: bool = True) -> bool:
        mapped = type(post_environment).model_validate_json(
            map_text(post_environment.model_dump_json(), pairs))
        before = type(pre_environment).model_validate_json(
            map_text(pre_environment.model_dump_json(), pairs))
        return bool(original(map_answer(model_output, pairs), before, mapped, strict))

    task.utility = utility


def vi_suite(name: str, require_goals: bool = False) -> Any:
    from agentdojo.task_suite.load_suites import get_suite  # type: ignore[import-not-found]

    english = get_suite(VERSION, name)
    prompts = yaml.safe_load((DATA / name / "user_tasks.yaml").read_text(encoding="utf-8"))
    goals = yaml.safe_load((DATA / "injection_tasks.yaml").read_text(encoding="utf-8"))[name]
    if set(prompts) != set(english.user_tasks):
        raise ValueError(f"{name}: user_tasks.yaml must cover exactly {sorted(english.user_tasks)}")
    if set(goals) != set(english.injection_tasks):
        raise ValueError(f"{name}: injection_tasks.yaml ids differ from the English suite")
    missing = sorted(k for k, v in goals.items() if not v)
    if require_goals and missing:
        raise SystemExit(f"{name}: untranslated injection GOALs {missing} (owner/Minh)")
    pairs, security_pairs = equivalents(name), equivalents(name, "security")
    suite = copy.copy(english)
    suite.data_path = DATA / name
    suite._user_tasks = defaultdict(dict)
    for task_id, task in english.user_tasks.items():
        vi = copy.copy(task)
        vi.PROMPT = prompts[task_id]
        _wrap_utility(vi, pairs)
        suite._user_tasks[task_id][(1, 0, 0)] = vi
    suite._injection_tasks = defaultdict(dict)
    for task_id, task in english.injection_tasks.items():
        vi = copy.copy(task)
        if goals[task_id]:
            vi.GOAL = goals[task_id]
        _wrap_security(vi, security_pairs)
        suite._injection_tasks[task_id][(1, 0, 0)] = vi
    return suite


def attack_template() -> str | None:
    value = yaml.safe_load((DATA / "attacks.yaml").read_text(encoding="utf-8"))
    template = value.get("important_instructions")
    return str(template) if template else None


def check(names: tuple[str, ...]) -> int:
    ok_all = True
    report: dict[str, Any] = {}
    for name in names:
        suite = vi_suite(name)
        # check_injectable=False: the English v1.2.2 suite itself fails the injectable probe
        # for every user task, so it is not a pass criterion; injectable sets are compared below.
        ok, (user_results, injection_results) = suite.check(check_injectable=False)
        failed_user = sorted(k for k, (good, _) in user_results.items() if not good)
        failed_inj = sorted(k for k, good in injection_results.items() if not good)
        report[name] = {"ok": ok, "user_tasks": len(user_results), "user_failed": failed_user,
                        "injection_tasks": len(injection_results),
                        "injection_failed": failed_inj}
        ok_all &= bool(ok)
    print(json.dumps(report, indent=1))
    return 0 if ok_all else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--suite", choices=SUITES, action="append")
    args = parser.parse_args(argv)
    return check(tuple(args.suite or SUITES))


if __name__ == "__main__":
    sys.exit(main())
