"""Log-only email sink with no SMTP or network dependency."""

from pydantic import BaseModel, ConfigDict, Field

from react_agent.schemas.tool import ToolResult
from react_agent.tools.base import BaseTool


class SendEmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class SendEmailMockTool(BaseTool[SendEmailInput]):
    name = "send_email_mock"
    description = "Mô phỏng gửi email và chỉ trả log; không SMTP, API hay mạng."
    input_model = SendEmailInput

    def _run(self, arguments: SendEmailInput) -> object:
        return {
            "status": "simulated",
            "to": arguments.to,
            "subject": arguments.subject,
            "body": arguments.body,
        }

    def execute(self, call_id: str, arguments: dict[str, object]) -> ToolResult:
        result = super().execute(call_id, arguments)
        if result.ok and isinstance(result.content, dict):
            result.content["message_id"] = f"mock_mail_{call_id.removeprefix('call_')}"
        return result
