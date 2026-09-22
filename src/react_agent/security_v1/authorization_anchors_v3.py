"""Bounded raw-user command grammar, with conservative quotation and revocation.

Destination grants are not payload or final-answer release grants. No model,
normalizer, benchmark metadata or tool observation participates in this parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.rules import EMAIL, AuthorizationAnchors

PROFILE = "raw_user_clause_anchors_v3"
RESOURCE = r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+"
FIELD = r"[a-z][a-z0-9_]{0,63}"
SEND = re.compile(
    r"^\s*(?:chỉ\s+|chi\s+)?(?:(?:hãy|hay|please)\s+)?"
    r"(?:gửi|gởi|gui|send|post)\s+",
    re.I,
)
SEND_WORD = re.compile(r"\b(?:gửi|gởi|gui|send|post)\b", re.I)
NEGATIVE = re.compile(
    r"\b(?:không|khong|đừng|chớ|not|never)\b|\b(?:dung|cho)\s+(?:gui|send|post|doc)\b",
    re.I,
)
REVOKE = re.compile(r"\b(?:thu hồi quyền|hủy yêu cầu|huy yeu cau|revoke|cancel)\b", re.I)
CONDITIONAL = re.compile(r"\b(?:nếu|neu|if|unless|khi|when)\b", re.I)
REPORTED = re.compile(
    r"(?<![\w@./+-])(?:ví dụ|vi du|minh họa|trích dẫn|trich dan|nói rằng|noi rang|"
    r"yêu cầu sau|hướng dẫn sau|lệnh sau|example|quote|says?|said|instruction below)"
    r"(?![\w@./+-])",
    re.I,
)
SEPARATOR = re.compile(
    r"[;\n]+|[.!?](?=\s|$)|,\s*(?=(?:chỉ\s+)?(?:gửi|gởi|gui|send|post)\s)",
    re.I,
)
READ = re.compile(
    rf"(?:(?:hãy|hay|please)\s+)?(?:đọc|doc|read|tra)\s+"
    rf"(?:{RESOURCE}(?:(?:,\s*|\s+(?:và|and)\s+){RESOURCE})*|"
    rf"{FIELD}(?:\s+(?:và|and)\s+{FIELD})*\s+của\s+{RESOURCE}\s+trong\s+{FIELD})",
)
SELECT = re.compile(rf"[Cc]hỉ lấy [\w ]{{1,80}} từ {RESOURCE}")
CONTEXT = re.compile(r"[Cc]ache là bản cũ")
PAYLOAD_BAN = re.compile(
    rf"(?:[Mm]ã đối soát|[Dd]ữ liệu|[Nn]ội dung|[Mm]ã) {RESOURCE} "
    r"chỉ được đọc, không được gửi(?: hoặc đưa vào câu trả lời)?",
)
DESTINATION = re.compile(r"\b(?:đến|tới|den|toi|to)\s+(\S+)", re.I)
ENDPOINT = re.compile(r"(?:https?://|mock://)[A-Za-z0-9_./~:%+?=&#-]{1,512}")
QUOTES = frozenset("\"'`“”‘’>«»")


@dataclass(frozen=True)
class Clause:
    start: int
    end: int
    kind: str


@dataclass(frozen=True)
class AnchorAudit:
    profile: str
    anchors: AuthorizationAnchors
    clauses: tuple[Clause, ...]
    blocked_by: str | None


def _kind(text: str) -> str:
    if NEGATIVE.search(text):
        if PAYLOAD_BAN.fullmatch(text):
            return "payload_prohibition"
        return "revocation" if SEND_WORD.search(text) else "other_prohibition"
    if SEND.match(text):
        return "send"
    # Case-insensitive verbs but case-sensitive resource/SQL identifiers.
    lowered_verb = re.sub(r"^(Đọc|Doc|Read|Tra|Please|Hãy|Hay)\b", lambda m: m[0].lower(), text)
    if READ.fullmatch(lowered_verb) or SELECT.fullmatch(text):
        return "read"
    if CONTEXT.fullmatch(text):
        return "context"
    return "unsupported"


def audit_anchors(raw_user: str) -> AnchorAudit:
    """Retain original offsets; fail closed on quoted/reported/conditional text.

    Unsupported preceding prose cannot introduce a later send instruction.
    Any unscoped send prohibition revokes all destinations, regardless of order.
    A narrow named-resource payload ban does not revoke destination authority;
    the existing sensitivity/value/final gates remain independently mandatory.
    """
    clauses: list[Clause] = []
    start = 0
    for boundary in (*SEPARATOR.finditer(raw_user), None):
        end = len(raw_user) if boundary is None else boundary.start()
        left = start + len(raw_user[start:end]) - len(raw_user[start:end].lstrip())
        right = end - len(raw_user[start:end]) + len(raw_user[start:end].rstrip())
        if left < right:
            clauses.append(Clause(left, right, _kind(raw_user[left:right])))
        start = len(raw_user) if boundary is None else boundary.end()
    blocked = (
        "quotation"
        if any(c in QUOTES for c in raw_user)
        else "conditional"
        if CONDITIONAL.search(raw_user)
        else "reported_instruction"
        if REPORTED.search(raw_user)
        else "revocation"
        if REVOKE.search(raw_user) or any(c.kind == "revocation" for c in clauses)
        else None
    )
    emails: set[str] = set()
    endpoints: set[str] = set()
    if blocked is None:
        context_supported = True
        for clause in clauses:
            text = raw_user[clause.start : clause.end]
            if clause.kind == "send" and context_supported:
                command = SEND.sub("", text, count=1)
                destinations = [m[1].rstrip(".,!?)") for m in DESTINATION.finditer(command)]
                direct = re.fullmatch(r"(\S+)\s+payload\s+[\w ]{1,100}", command)
                if direct and ENDPOINT.fullmatch(direct[1]):
                    destinations.append(direct[1])
                webhook = "webhook" in command.casefold() or text.casefold().startswith("post ")
                for destination in destinations:
                    if ENDPOINT.fullmatch(destination) and (webhook or direct):
                        endpoints.add(destination)
                    elif not webhook and EMAIL.fullmatch(destination):
                        emails.add(destination)
            elif clause.kind not in {"read", "context", "payload_prohibition"}:
                context_supported = False
    anchors = AuthorizationAnchors(
        emails=tuple(sorted(emails)),
        endpoints=tuple(sorted(endpoints)),
        raw_user_sha256=text_hash(raw_user),
    )
    return AnchorAudit(PROFILE, anchors, tuple(clauses), blocked)


def extract_anchors(raw_user: str) -> AuthorizationAnchors:
    return audit_anchors(raw_user).anchors
