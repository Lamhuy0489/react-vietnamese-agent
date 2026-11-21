"""Turn the traces of one run into steps a person can read in the chat."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Vietnamese explanations of the gate reasons (unknown codes are shown as they are).
REASONS_VI: dict[str, str] = {
    "PASS_THROUGH": "Cho qua",
    "INTENT_NOT_GRANTED": "Lệnh của người dùng không cho phép hành động này tới đích này",
    "INTENT_FORBIDDEN": "Người dùng đã cấm hành động này",
    "INTENT_NO_TARGET": "Lệnh không nêu đích nhận",
    "INTENT_NO_ACTION_VERB": "Lệnh không có động từ yêu cầu hành động",
    "INTENT_MENTION_ONLY": "Đích chỉ được nhắc tới, không được yêu cầu gửi",
    "INTENT_QUOTED": "Đích nằm trong phần trích dẫn",
    "INTENT_REPORTED": "Đích nằm trong lời thuật lại",
    "INTENT_REFERENCE_ONLY": "Đích chỉ được tham chiếu",
    "INTENT_CONDITIONAL": "Quyền chỉ có khi thỏa điều kiện",
    "INTENT_AMBIGUOUS_NEGATION": "Lệnh có phủ định không rõ",
    "CONFIRMATION_REQUIRED": "Cần người dùng xác nhận",
    "PINNED_PARAMETER_CHANGED": "Tham số người dùng đã nêu bị đổi",
    "PROVENANCE_SENSITIVE_PAYLOAD": "Nội dung gửi đi chứa dữ liệu mật",
    "PROVENANCE_SENSITIVE_FINAL": "Câu trả lời chứa dữ liệu mật",
    "UNTRUSTED_CONTROL_INFLUENCE": "Hành động bị dẫn dắt bởi nội dung không tin cậy",
    "SECURITY_POLICY_DENIED": "Chính sách an ninh từ chối",
    "RULE_GUARD_ERROR": "Lỗi ở lớp luật",
}
SINKS = {"send_email_mock", "post_webhook_mock"}
PREVIEW = 600


def explain(reasons: list[str]) -> str:
    return "; ".join(REASONS_VI.get(r, r) for r in reasons) or "Không rõ lý do"


def _preview(value: object, limit: int = PREVIEW) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)
    return text if len(text) <= limit else text[:limit] + " …"


@dataclass
class Step:
    index: int
    tool: str
    arguments: dict[str, Any]
    allowed: bool = True
    reasons: list[str] = field(default_factory=list)
    component: str | None = None
    ok: bool | None = None
    result_preview: str = ""
    result: object = None

    @property
    def is_sink(self) -> bool:
        return self.tool in SINKS

    def title(self) -> str:
        if not self.allowed:
            return f"⛔ Bước {self.index}: {self.tool} bị chặn"
        mark = "✅" if self.ok else "⚠️"
        return f"{mark} Bước {self.index}: {self.tool}"

    def body(self) -> str:
        lines = [f"Tham số: `{json.dumps(self.arguments, ensure_ascii=False)}`"]
        if not self.allowed:
            lines.append(f"Lý do ({self.component}): {explain(self.reasons)}")
        elif self.result_preview:
            lines.append(f"Kết quả:\n```\n{self.result_preview}\n```")
        return "\n\n".join(lines)


@dataclass
class TurnView:
    status: str
    final_answer: str | None
    steps: list[Step]

    @property
    def blocked(self) -> list[Step]:
        return [s for s in self.steps if not s.allowed]

    def allowed_emails(self) -> list[dict[str, str]]:
        """``send_email_mock`` calls the broker executed after every gate allowed them."""
        out = []
        for s in self.steps:
            content = s.result
            if (s.tool == "send_email_mock" and s.allowed and s.ok
                    and isinstance(content, dict) and content.get("status") == "simulated"):
                out.append({k: str(content[k]) for k in ("to", "subject", "body")})
        return out


def _events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_turn(execution: Path) -> TurnView:
    """Parse ``trace_security.jsonl`` (gate decisions) and ``trace_legacy.jsonl`` (results)."""
    results: dict[str, dict[str, Any]] = {}
    status, final = "unknown", None
    for event in _events(execution / "trace_legacy.jsonl"):
        data = event.get("data") or {}
        if event.get("event") == "tool_result":
            results[str(data.get("call_id"))] = data
        elif event.get("event") == "final_answer":
            final = data.get("answer")
        elif event.get("event") == "run_end":
            status = str(data.get("status"))
    steps: dict[str, Step] = {}
    for event in _events(execution / "trace_security.jsonl"):
        kind = event.get("event")
        data = json.loads(event.get("data_json") or "{}")
        if kind == "proposal":
            action = data.get("action") or {}
            pid = str(data.get("proposal_id") or f"p{len(steps) + 1}")
            steps[pid] = Step(len(steps) + 1, str(action.get("name")),
                              dict(action.get("arguments") or {}))
        elif kind == "decision" and data.get("proposal_id") in steps:
            step = steps[data["proposal_id"]]
            if data.get("effect") != "ALLOW" and step.allowed:
                step.allowed = False
                step.reasons = list(data.get("reasons") or [])
                step.component = data.get("component")
        elif kind == "broker_result" and data.get("proposal_id") in steps:
            step = steps[data["proposal_id"]]
            step.ok = bool(data.get("ok"))
            result = results.get(str(data.get("call_id")), {})
            payload = result.get("content") if result.get("ok") else result.get("error")
            step.result = payload
            step.result_preview = _preview(payload) if payload is not None else ""
    return TurnView(status, final, list(steps.values()))
