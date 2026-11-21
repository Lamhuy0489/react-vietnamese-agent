"""Gmail SMTP sender (STARTTLS + App Password) and a dry-run stand-in.

Called only by the outbox after the user confirmed a message the guard had allowed.
The password is never logged or put into exception messages.
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Protocol

from pydantic import SecretStr

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587


class SendError(Exception):
    """Delivery failed; the message carries no credential."""


class Sender(Protocol):
    def send(self, to: str, subject: str, body: str) -> str: ...


def _clean_header(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise SendError("header contains a line break")
    return value


class DryRunSender:
    """Records what would be sent; no network."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, body: str) -> str:
        self.sent.append((_clean_header(to), _clean_header(subject), body))
        return f"dry-run-{len(self.sent)}"


class GmailSender:
    def __init__(self, user: str, app_password: SecretStr, *, timeout: float = 15.0,
                 smtp_factory: type[smtplib.SMTP] = smtplib.SMTP) -> None:
        if not user or not app_password.get_secret_value():
            raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD are required for live e-mail")
        self.user = user
        self._password = app_password
        self.timeout = timeout
        self._smtp_factory = smtp_factory

    def send(self, to: str, subject: str, body: str) -> str:
        message = EmailMessage()
        message["From"] = self.user
        message["To"] = _clean_header(to)
        message["Subject"] = _clean_header(subject)
        message["Message-ID"] = make_msgid(domain="brokerguard.demo")
        message.set_content(body)
        try:
            with self._smtp_factory(SMTP_HOST, SMTP_PORT, timeout=self.timeout) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(self.user, self._password.get_secret_value())
                smtp.send_message(message)
        except smtplib.SMTPAuthenticationError:
            raise SendError("Gmail từ chối đăng nhập (kiểm tra App Password)") from None
        except (smtplib.SMTPException, OSError) as exc:
            raise SendError(f"Gửi thất bại: {type(exc).__name__}") from None
        return str(message["Message-ID"])
