"""Backend-independent A0 ReAct state machine."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from react_agent.agent.context import ContextBuilder
from react_agent.agent.state import RunResult, RuntimeConfig, TerminalStatus
from react_agent.broker import ToolBroker
from react_agent.llm.base import GenerationConfig, LLMBackend
from react_agent.logging import TraceLogger
from react_agent.parser import ParseError, StructuredParser
from react_agent.schemas.agent_output import ActionTurn, FinalTurn
from react_agent.schemas.task import RuntimeTask
from react_agent.schemas.trace import EventName, TraceEvent
from react_agent.tools.registry import ToolRegistry

FORMAT_CORRECTION = (
    "Đầu ra trước không đúng schema JSON bắt buộc. "
    "Hãy trả về đúng một JSON object action hoặc final_answer."
)


class AgentRuntime:
    def __init__(
        self,
        backend: LLMBackend,
        registry: ToolRegistry,
        *,
        runtime_config: RuntimeConfig | None = None,
        generation_config: GenerationConfig | None = None,
    ) -> None:
        self.backend = backend
        self.registry = registry
        self.runtime_config = runtime_config or RuntimeConfig()
        self.generation_config = generation_config or GenerationConfig()

    def run(self, task: RuntimeTask, *, trace_path: Path | None = None) -> RunResult:
        run_id = f"run_{uuid4().hex}"
        logger = TraceLogger(trace_path)
        parser = StructuredParser(self.registry)
        broker = ToolBroker(
            self.registry,
            logger,
            timeout_seconds=self.runtime_config.tool_timeout_seconds,
        )
        context_builder = ContextBuilder(self.registry.definitions())
        history: list[tuple[str, str]] = []
        tool_sequence: list[str] = []
        parse_errors = 0

        self._log(
            logger,
            run_id,
            task.task_id,
            0,
            "run_start",
            {
                "config_id": self.runtime_config.config_id,
                "model_id": self.backend.model_id,
                "model_revision": self.backend.model_revision,
                "generation": self.generation_config.model_dump(),
            },
        )

        for step in range(1, self.runtime_config.max_steps + 1):
            correction: str | None = None
            for retry in range(self.runtime_config.max_format_retries_per_step + 1):
                messages = context_builder.build(task, history, correction)
                try:
                    response = self.backend.generate(messages, self.generation_config)
                except Exception as exc:  # noqa: BLE001 - runtime terminal boundary
                    return self._finish(
                        logger,
                        run_id,
                        task.task_id,
                        "model_error",
                        step - 1,
                        tool_sequence,
                        parse_errors,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                self._log(
                    logger,
                    run_id,
                    task.task_id,
                    step,
                    "model_output",
                    {"raw_output": response.text, "retry": retry},
                )
                try:
                    turn = parser.parse(response.text)
                except ParseError as exc:
                    parse_errors += 1
                    self._log(
                        logger,
                        run_id,
                        task.task_id,
                        step,
                        "parse_error",
                        {"code": exc.code, "message": exc.message, "retry": retry},
                    )
                    if retry >= self.runtime_config.max_format_retries_per_step:
                        return self._finish(
                            logger,
                            run_id,
                            task.task_id,
                            "parse_failure",
                            step - 1,
                            tool_sequence,
                            parse_errors,
                        )
                    correction = FORMAT_CORRECTION
                    continue
                break

            if isinstance(turn, FinalTurn):
                answer = turn.final_answer.answer
                self._log(
                    logger,
                    run_id,
                    task.task_id,
                    step,
                    "final_answer",
                    {"answer": answer},
                )
                return self._finish(
                    logger,
                    run_id,
                    task.task_id,
                    "completed",
                    step,
                    tool_sequence,
                    parse_errors,
                    final_answer=answer,
                )

            if isinstance(turn, ActionTurn):
                action_json = turn.model_dump_json()
                result = broker.execute(
                    turn.action.name,
                    turn.action.arguments,
                    run_id=run_id,
                    task_id=task.task_id,
                    step=step,
                )
                tool_sequence.append(turn.action.name)
                history.append((action_json, result.model_dump_json()))

        return self._finish(
            logger,
            run_id,
            task.task_id,
            "max_steps",
            self.runtime_config.max_steps,
            tool_sequence,
            parse_errors,
        )

    def _finish(
        self,
        logger: TraceLogger,
        run_id: str,
        task_id: str,
        status: TerminalStatus,
        steps: int,
        tool_sequence: list[str],
        parse_errors: int,
        *,
        final_answer: str | None = None,
        error: str | None = None,
    ) -> RunResult:
        data: dict[str, object] = {"status": status, "steps": steps}
        if error is not None:
            data["error"] = error
        self._log(logger, run_id, task_id, steps, "run_end", data)
        return RunResult(
            run_id=run_id,
            task_id=task_id,
            status=status,
            steps=steps,
            final_answer=final_answer,
            tool_sequence=list(tool_sequence),
            parse_errors=parse_errors,
        )

    @staticmethod
    def _log(
        logger: TraceLogger,
        run_id: str,
        task_id: str,
        step: int,
        event: EventName,
        data: dict[str, object],
    ) -> None:
        logger.log(
            TraceEvent(
                run_id=run_id,
                task_id=task_id,
                step=step,
                event=event,
                data=data,
            )
        )
