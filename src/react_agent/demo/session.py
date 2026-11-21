"""One chat session: each message is one independent task on the frozen runtimes.

Modes: ``A0`` (``Phase5ClosureRuntime``, level A0, no defence) and ``V3`` (BrokerGuard v3
with all components and the P2 sandwich prompt, level A1), the configuration evaluated
in the paper. No pinned file is changed; the runtime classes are used as they are.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from react_agent.config import load_generation_config, load_runtime_config
from react_agent.demo.config import ROOT, DemoConfig, Mode
from react_agent.demo.corpus import DemoDocument, build_environment, load_demo_documents
from react_agent.demo.gmail_sender import DryRunSender, GmailSender, Sender
from react_agent.demo.outbox import Outbox, OutboxItem
from react_agent.demo.trace_view import TurnView, read_turn
from react_agent.llm.base import GenerationConfig, ModelResponse
from react_agent.prompts import a0_rebuild
from react_agent.security_v1 import a6_provenance_v3
from react_agent.security_v1.contracts import configuration
from react_agent.security_v1.phase5_closure_runtime_v1 import Phase5ClosureRuntime
from react_agent.security_v3 import brokerguard_v3_v1 as v3mod
from react_agent.security_v3.prompt_baselines import PromptBaselineBackend
from react_agent.tools.registry import ToolRegistry

_ACTIVATED = False
_ACTIVATE_LOCK = threading.Lock()


def activate_profiles() -> None:
    """Prompt v3 and A6 provenance v3, as every v3 runner does (process-wide, once)."""
    global _ACTIVATED
    with _ACTIVATE_LOCK:
        if not _ACTIVATED:
            a0_rebuild.activate("v3")
            a6_provenance_v3.activate()
            _ACTIVATED = True


class ScriptedBackend:
    """Offline backend replaying fixed agent turns (tests and rehearsal without a model)."""

    infra_failures = 0

    def __init__(self, turns: list[dict[str, Any]] | None = None) -> None:
        self.model_id, self.model_revision = "scripted", "demo"
        default = [{"final_answer": {"answer": "Chế độ chạy thử: chưa nối model."}}]
        self.turns = list(turns or default)

    def probe(self) -> None:
        return None

    def generate(self, messages: list[dict[str, str]], config: GenerationConfig) -> ModelResponse:
        del messages, config
        turn = self.turns.pop(0) if self.turns else {"final_answer": {"answer": "Hết kịch bản."}}
        return ModelResponse(text=json.dumps(turn, ensure_ascii=False),
                             model_id=self.model_id, model_revision=self.model_revision)


BackendFactory = Callable[[ToolRegistry], Any]


def api_backend_factory(config: DemoConfig) -> BackendFactory:
    from react_agent.llm.openai_compat_v1 import OpenAICompatBackend, OrderedHTTPSJSON

    if not config.base_url or not config.api_key.get_secret_value():
        raise ValueError("Set VLLM_BASE_URL and VLLM_API_KEY (or DEMO_DRY_RUN=1)")

    def build(registry: ToolRegistry) -> Any:
        return OpenAICompatBackend(
            OrderedHTTPSJSON(config.base_url, config.api_key.get_secret_value(),
                             timeout=config.request_timeout),
            repo=config.model_repo, revision=config.model_revision,
            tool_definitions=registry.definitions())

    return build


@dataclass
class DemoTask:
    task_id: str
    instruction: str


@dataclass
class TurnResult:
    turn_id: str
    mode: Mode
    instruction: str
    view: TurnView
    outbox_items: list[OutboxItem] = field(default_factory=list)
    error: str | None = None


def make_sender(config: DemoConfig) -> Sender:
    if config.email_live:
        return GmailSender(config.gmail_user, config.gmail_app_password)
    return DryRunSender()


class DemoSession:
    def __init__(self, config: DemoConfig, *, backend_factory: BackendFactory | None = None,
                 sender: Sender | None = None) -> None:
        activate_profiles()
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid4().hex[:6]
        self.folder = config.runs_dir / self.session_id
        self.documents: list[DemoDocument] = load_demo_documents(config.demo_data)
        if backend_factory is None:
            backend_factory = ((lambda registry: ScriptedBackend()) if config.dry_run
                               else api_backend_factory(config))
        self.backend_factory = backend_factory
        self.outbox = Outbox(sender or make_sender(config), config.email_allowlist,
                             daily_limit=config.email_daily_limit, footer=config.email_footer,
                             log_path=self.folder / "outbox.jsonl")
        self.runtime_config = load_runtime_config(ROOT / "configs/agent/A0.yaml")
        self.generation_config = load_generation_config(ROOT / "configs/runtime/default.yaml")
        self.turns: list[TurnResult] = []
        self._lock = threading.Lock()  # one turn at a time (shared process-wide profiles)

    def run(self, message: str, mode: Mode) -> TurnResult:
        message = message.strip()
        if not message:
            raise ValueError("empty message")
        with self._lock:
            turn_id = f"turn_{len(self.turns) + 1:03d}"
            folder = self.folder / turn_id
            registry, catalog = build_environment(
                self.config.clean_environment, self.documents, folder / "environment")
            backend = self.backend_factory(registry)
            if mode == "V3":
                runtime: Any = v3mod.BrokerGuardV3Runtime(
                    PromptBaselineBackend(backend, sandwich=True), registry,
                    runtime_config=self.runtime_config,
                    generation_config=self.generation_config)
                security = configuration("A1")
            else:
                runtime = Phase5ClosureRuntime(
                    backend, registry, runtime_config=self.runtime_config,
                    generation_config=self.generation_config)
                security = configuration("A0")
            task = DemoTask(f"demo_{self.session_id}_{turn_id}", message)
            error = None
            try:
                runtime.run_instrumented(
                    task, output=folder / "execution", source_catalog=catalog,
                    security_config=security, guard_factory=None, guard_execution=None)
            except Exception as exc:  # noqa: BLE001 - shown to the presenter, run kept on disk
                error = f"{type(exc).__name__}: {exc}"
            view = read_turn(folder / "execution")
            items = [self.outbox.add(m["to"], m["subject"], m["body"], turn_id=turn_id)
                     for m in view.allowed_emails()]
            result = TurnResult(turn_id, mode, message, view, items, error)
            self.turns.append(result)
            return result

