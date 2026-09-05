"""Validate, execute, time-bound, normalize, and trace every tool call."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from itertools import count

from react_agent.logging import TraceLogger
from react_agent.schemas.tool import ToolCall, ToolError, ToolResult
from react_agent.schemas.trace import TraceEvent
from react_agent.tools.registry import ToolRegistry


class ToolBroker:
    def __init__(
        self,
        registry: ToolRegistry,
        logger: TraceLogger,
        *,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.registry = registry
        self.logger = logger
        self.timeout_seconds = timeout_seconds
        self._counter = count(1)

    def execute(
        self,
        name: str,
        arguments: dict[str, object],
        *,
        run_id: str,
        task_id: str,
        step: int,
    ) -> ToolResult:
        call = ToolCall(
            call_id=f"call_{next(self._counter):06d}",
            name=name,
            arguments=arguments,
        )
        self._log(run_id, task_id, step, "tool_call_proposed", call.call_id, call.model_dump())
        tool = self.registry.get(name)
        if tool is None:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=name,
                ok=False,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Unknown tool: {name}",
                    retryable=True,
                ),
            )
            self._log_result(run_id, task_id, step, result)
            return result

        self._log(run_id, task_id, step, "tool_call_executed", call.call_id, {})
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(tool.execute, call.call_id, arguments)
        try:
            result = future.result(timeout=self.timeout_seconds)
        except TimeoutError:
            future.cancel()
            result = ToolResult(
                call_id=call.call_id,
                tool_name=name,
                ok=False,
                error=ToolError(
                    code="TOOL_TIMEOUT",
                    message="Tool execution exceeded its timeout.",
                    retryable=True,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - broker is the runtime exception boundary
            result = ToolResult(
                call_id=call.call_id,
                tool_name=name,
                ok=False,
                error=ToolError(
                    code="TOOL_RUNTIME_ERROR",
                    message=f"{type(exc).__name__}: {exc}",
                    retryable=True,
                ),
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        self._log_result(run_id, task_id, step, result)
        return result

    def _log_result(self, run_id: str, task_id: str, step: int, result: ToolResult) -> None:
        self._log(
            run_id,
            task_id,
            step,
            "tool_result",
            result.call_id,
            result.model_dump(mode="json"),
        )

    def _log(
        self,
        run_id: str,
        task_id: str,
        step: int,
        event: str,
        call_id: str,
        data: dict[str, object],
    ) -> None:
        self.logger.log(
            TraceEvent(
                run_id=run_id,
                task_id=task_id,
                step=step,
                event=event,  # type: ignore[arg-type]
                call_id=call_id,
                data=data,
            )
        )
