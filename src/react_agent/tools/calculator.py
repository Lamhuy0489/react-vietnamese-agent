"""Safe arithmetic evaluator with a small AST whitelist."""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from react_agent.tools.base import BaseTool, ToolExecutionError

Number = int | float
BINARY_OPERATORS: dict[type[ast.operator], Callable[[Number, Number], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str = Field(min_length=1, max_length=200)


class CalculatorTool(BaseTool[CalculatorInput]):
    name = "calculator"
    description = "Tính biểu thức số học đơn giản bằng AST whitelist."
    input_model = CalculatorInput

    def _run(self, arguments: CalculatorInput) -> object:
        try:
            tree = ast.parse(arguments.expression, mode="eval")
            value = self._evaluate(tree.body)
        except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
            raise ToolExecutionError(
                "INVALID_EXPRESSION", "Expression is not supported.", retryable=True
            ) from exc
        if abs(value) > 10**15:
            raise ToolExecutionError(
                "INVALID_EXPRESSION", "Result exceeds the allowed range.", retryable=True
            )
        return {"value": value}

    def _evaluate(self, node: ast.AST) -> Number:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("exponent is too large")
            return BINARY_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
            return UNARY_OPERATORS[type(node.op)](self._evaluate(node.operand))
        raise ValueError(f"unsupported expression node: {type(node).__name__}")
