#!/usr/bin/env python3
"""Run AgentDojo (Banking, Slack) against a vLLM endpoint (Study 2, WP6).

Runs in the separate venv ``.venv-agentdojo`` (``requirements-agentdojo.txt`` pins
``agentdojo==0.1.35``)::

    set -a; . build/kaggle/<serve folder>/endpoint.env; set +a
    .venv-agentdojo/bin/python scripts/run_agentdojo_api_v1.py --model-key qwen3_8b \
        --suite banking --attack important_instructions --defense none --lang en

The agent is AgentDojo's own prompting pipeline (``LocalLLM``: tools described in the
system prompt, calls parsed from the text), so it needs no server-side tool parser. Qwen3
models get ``chat_template_kwargs`` from the backbone config (thinking off), like the main
harness. Attacks and defenses are AgentDojo's built-ins; nothing here authors attack text.
``--lang vi`` loads the Vietnamese suite from ``data/agentdojo_vi/`` (not built yet).
Logs go to ``results/rebuild_b/agentdojo_<lang>_<suite>_<attack>_<defense>_<K>/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.2.2"
SUITES = ("banking", "slack")
DEFENSES = ("none", "spotlighting_with_delimiting", "repeat_user_prompt",
            "transformers_pi_detector")


def model_spec(config: Path, key: str) -> dict[str, Any]:
    spec: dict[str, Any] = yaml.safe_load(config.read_text(encoding="utf-8"))[key]
    if spec.get("from") == "backbones_v2":
        spec = model_spec(config.with_name("backbones_v2.yaml"), key)
    return spec


class _Completions:
    """``client.chat.completions`` that adds fixed ``extra_body`` to every request."""

    def __init__(self, inner: Any, extra_body: dict[str, Any]) -> None:
        self._inner, self._extra = inner, extra_body

    def create(self, **kwargs: Any) -> Any:
        if self._extra:
            kwargs["extra_body"] = {**self._extra, **kwargs.get("extra_body", {})}
        return self._inner.create(**kwargs)


class _Chat:
    def __init__(self, completions: _Completions) -> None:
        self.completions = completions


class ClientWithExtras:
    """Duck-typed ``openai.OpenAI`` for ``LocalLLM`` (only ``chat.completions`` is used)."""

    def __init__(self, client: Any, extra_body: dict[str, Any]) -> None:
        self._client = client
        self.chat = _Chat(_Completions(client.chat.completions, extra_body))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def served_model(client: Any, repo: str) -> str:
    ids = [m.id for m in client.models.list().data]
    match = [i for i in ids if i.split("@")[0] == repo]
    if len(match) != 1:
        raise SystemExit(f"endpoint serves {ids}, expected one {repo}@<revision>")
    return str(match[0])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-key", default="qwen3_8b")
    parser.add_argument("--models-config", default="configs/models/backbones_v3.yaml")
    parser.add_argument("--suite", choices=SUITES, required=True)
    parser.add_argument("--attack", default="important_instructions",
                        help="AgentDojo attack name, or 'none' for utility only")
    parser.add_argument("--defense", choices=DEFENSES, default="none")
    parser.add_argument("--lang", choices=["en", "vi"], default="en")
    parser.add_argument("--user-tasks", nargs="*", help="subset, e.g. user_task_0 user_task_1")
    parser.add_argument("--injection-tasks", nargs="*")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    vi: Any = None
    template: str | None = None
    if args.lang == "vi":
        sys.path.insert(0, str(ROOT / "scripts"))
        import agentdojo_vi_v1 as vi  # Vietnamese suites (data/agentdojo_vi/)

        if args.attack not in ("none", "important_instructions"):
            raise SystemExit("AgentDojo-VI supports --attack none or important_instructions")
        if args.attack != "none":
            template = vi.attack_template()
            if not template:
                raise SystemExit("data/agentdojo_vi/attacks.yaml not translated yet (owner/Minh)")

    import openai  # type: ignore[import-not-found]
    from agentdojo.agent_pipeline.agent_pipeline import (  # type: ignore[import-not-found]
        AgentPipeline,
        PipelineConfig,
    )
    from agentdojo.agent_pipeline.llms.local_llm import (  # type: ignore[import-not-found]
        LocalLLM,
    )
    from agentdojo.attacks.attack_registry import (  # type: ignore[import-not-found]
        load_attack,
    )
    from agentdojo.benchmark import (  # type: ignore[import-not-found]
        benchmark_suite_with_injections,
        benchmark_suite_without_injections,
    )
    from agentdojo.logging import OutputLogger  # type: ignore[import-not-found]
    from agentdojo.task_suite.load_suites import get_suite  # type: ignore[import-not-found]

    base_url, api_key = os.environ.get("VLLM_BASE_URL"), os.environ.get("VLLM_API_KEY")
    if not base_url or not api_key:
        raise SystemExit("Set VLLM_BASE_URL (https://.../v1) and VLLM_API_KEY")
    spec = model_spec(ROOT / args.models_config, args.model_key)
    raw = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=180, max_retries=3)
    served = served_model(raw, spec["repo"])
    client = ClientWithExtras(raw, {"chat_template_kwargs": spec["chat_template_kwargs"]}
                              if spec.get("chat_template_kwargs") else {})
    llm = LocalLLM(client, served)  # temperature 0, AgentDojo defaults otherwise
    pipeline = AgentPipeline.from_config(PipelineConfig(
        llm=llm, model_id=served, system_message_name=None,
        system_message=vi.system_message() if vi else None,
        defense=None if args.defense == "none" else args.defense))
    pipeline.name = "local"  # AgentDojo's name for a local model (attack prose: "Local model")

    suite = (vi.vi_suite(args.suite, require_goals=args.attack != "none") if vi
             else get_suite(VERSION, args.suite))
    name = f"agentdojo_{args.lang}_{args.suite}_{args.attack}_{args.defense}_{args.model_key}"
    output = (args.output or ROOT / "results/rebuild_b" / name).resolve()
    output.mkdir(parents=True, exist_ok=True)
    identity = {"benchmark": "agentdojo", "version": VERSION, "suite": args.suite,
                "lang": args.lang, "attack": args.attack, "defense": args.defense,
                "model_key": args.model_key, "served_model": served,
                "chat_template_kwargs": spec.get("chat_template_kwargs") or {},
                "user_tasks": args.user_tasks, "injection_tasks": args.injection_tasks}
    if vi:
        identity["vi_data_sha256"] = {
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted((ROOT / "data/agentdojo_vi").rglob("*")) if f.is_file()}
    path = output / "identity.json"
    if path.exists() and json.loads(path.read_text()) != identity:
        raise SystemExit("Output directory belongs to other inputs; choose a fresh --output")
    path.write_text(json.dumps(identity, indent=1) + "\n")

    with OutputLogger(str(output / "logs"), live=None):
        if args.attack == "none":
            results = benchmark_suite_without_injections(
                pipeline, suite, logdir=output / "logs", force_rerun=False,
                user_tasks=args.user_tasks, benchmark_version=VERSION)
        else:
            attacker = load_attack(args.attack, suite, pipeline)
            if template:
                attacker.jailbreak = template  # translated important_instructions template
            results = benchmark_suite_with_injections(
                pipeline, suite, attacker, logdir=output / "logs", force_rerun=False,
                user_tasks=args.user_tasks, injection_tasks=args.injection_tasks,
                verbose=False, benchmark_version=VERSION)
    utility = results["utility_results"]
    security = results["security_results"]
    summary = {
        "pairs": len(utility),
        "utility": f"{sum(utility.values())}/{len(utility)}",
        # AgentDojo's security_results is True when the injection task succeeded.
        "attack_success": (f"{sum(security.values())}/{len(security)}"
                           if args.attack != "none" else None),
        "injection_tasks_solvable": results.get("injection_tasks_utility_results"),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
