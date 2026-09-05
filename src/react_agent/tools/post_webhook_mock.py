"""Log-only webhook sink with no HTTP or network dependency."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from react_agent.schemas.tool import ToolResult
from react_agent.tools.base import BaseTool


class PostWebhookInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str = Field(min_length=1)
    payload: dict[str, Any]


class PostWebhookMockTool(BaseTool[PostWebhookInput]):
    name = "post_webhook_mock"
    description = "Mô phỏng webhook và chỉ trả log; không thực hiện HTTP."
    input_model = PostWebhookInput

    def _run(self, arguments: PostWebhookInput) -> object:
        return {
            "status": "simulated",
            "endpoint": arguments.endpoint,
            "payload": arguments.payload,
        }

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        result = super().execute(call_id, arguments)
        if result.ok and isinstance(result.content, dict):
            result.content["request_id"] = f"mock_hook_{call_id.removeprefix('call_')}"
        return result
