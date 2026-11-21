import smtplib
from email.message import EmailMessage
from typing import Any

import pytest
from pydantic import SecretStr

from react_agent.demo.gmail_sender import DryRunSender, GmailSender, SendError

PASSWORD = "abcd efgh ijkl mnop"  # noqa: S105 - fake test value


class FakeSMTP:
    instances: list["FakeSMTP"] = []
    fail_login = False

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host, self.port, self.calls = host, port, []  # type: ignore[var-annotated]
        self.messages: list[EmailMessage] = []
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *args: Any) -> None:
        self.calls.append("quit")

    def starttls(self, context: Any = None) -> None:
        self.calls.append("starttls")

    def login(self, user: str, password: str) -> None:
        self.calls.append("login")
        if FakeSMTP.fail_login:
            raise smtplib.SMTPAuthenticationError(535, b"bad " + password.encode())

    def send_message(self, message: EmailMessage) -> None:
        self.calls.append("send")
        self.messages.append(message)


@pytest.fixture(autouse=True)
def _reset() -> None:
    FakeSMTP.instances.clear()
    FakeSMTP.fail_login = False


def sender() -> GmailSender:
    return GmailSender("demo@gmail.com", SecretStr(PASSWORD), smtp_factory=FakeSMTP)  # type: ignore[arg-type]


def test_starttls_before_login_and_message_fields() -> None:
    sender().send("huy@university.example", "Tiêu đề", "Nội dung")
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.gmail.com", 587)
    assert smtp.calls[:3] == ["starttls", "login", "send"]
    message = smtp.messages[0]
    assert message["To"] == "huy@university.example" and message["From"] == "demo@gmail.com"
    assert message.get_content().strip() == "Nội dung"


def test_header_injection_refused() -> None:
    with pytest.raises(SendError):
        sender().send("huy@university.example", "a\r\nBcc: evil@x.example", "b")
    with pytest.raises(SendError):
        DryRunSender().send("huy@university.example\nBcc: x@y.example", "a", "b")
    assert all("send" not in s.calls for s in FakeSMTP.instances)


def test_auth_error_does_not_leak_password() -> None:
    FakeSMTP.fail_login = True
    with pytest.raises(SendError) as info:
        sender().send("huy@university.example", "S", "B")
    assert PASSWORD not in str(info.value) and info.value.__cause__ is None
    assert PASSWORD not in repr(sender().__dict__)


def test_requires_credentials() -> None:
    with pytest.raises(ValueError):
        GmailSender("", SecretStr(""))
