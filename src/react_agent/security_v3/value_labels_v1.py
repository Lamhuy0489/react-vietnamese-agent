"""C2: value-level sensitivity labels and R-Flow v2 for BrokerGuard v3.

Design: ``docs/project/brokerguard_v3_extension_design.md`` section 3 (C2).

v1 (D2 rule 3) protects only values seen in tool outputs whose *source* is labelled
CONFIDENTIAL, so a secret inside a source labelled public never enters the protected set
(the 25 SL/AL bypasses of v1). C2 labels each value by what it is, independently of the
source label and of trust (sensitivity and trust stay independent dimensions):

- credential-like identifiers: a token of letters and digits (with ``-``/``_``/``.``
  joints) of at least ``MIN_IDENTIFIER`` characters, containing both a letter and a digit;
- long numbers (account, card, phone-like): at least ``MIN_DIGITS`` digits after removing
  spaces, dots and dashes;
- labelled fields: the value right after a sensitive field name ("mật khẩu", "OTP",
  "token", "số tài khoản", "password", ...), in text (``name: value``) or JSON keys.

Plain words and short numbers (counts, amounts the user asked about) are never values.
R-Flow v2 checks every protected value at every sink argument and in the final answer,
also in lightly transformed forms (spaces, dots or dashes added or removed, case). A value
that occurs in the user instruction is the user's own and may flow.

Generic by construction: no pattern is specific to the synthetic generator's format.
Tunable on Dev only: ``MIN_IDENTIFIER``, ``MIN_DIGITS`` and the field-name list.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable

PROFILE = "value_labels_v1"
MIN_IDENTIFIER = 8
MIN_DIGITS = 9
REDACTION = "[REDACTED]"

_JOINT = r"[-_.]"
IDENTIFIER = re.compile(rf"(?<![\w])[A-Za-z0-9]+(?:{_JOINT}[A-Za-z0-9]+)*(?![\w])")
NUMBER = re.compile(r"(?<![\w])\d[\d .-]{4,30}\d(?![\w])")
# Sensitive field names, compared on mark-stripped casefolded text.
FIELDS = (
    "mat khau", "password", "passcode", "passphrase", "otp", "ma otp", "ma xac thuc",
    "ma xac minh", "verification code", "auth code", "ma truy cap", "access code",
    "token", "access token", "api key", "khoa api", "secret", "bi mat", "ma bi mat",
    "ma bao mat", "security code", "pin", "ma pin", "cvv", "so tai khoan", "account number",
    "so the", "card number", "private key", "khoa rieng", "khoa bi mat", "credential",
    "ma kich hoat", "activation code", "recovery code", "ma khoi phuc",
)
_FIELD_RE = "|".join(re.escape(f) for f in sorted(FIELDS, key=len, reverse=True))
LABELLED = re.compile(rf"\b(?:{_FIELD_RE})\b\s*(?:la|is|=|:|-)?\s*[\"'`“”]?([^\s\"'`“”,;]{{4,64}})")


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf").casefold()
    out = []
    for ch in text:
        if ch == "đ":
            out.append("d")
            continue
        decomposed = unicodedata.normalize("NFD", ch)
        out.append(decomposed[0] if decomposed else ch)
    return "".join(out)


def compact(value: str) -> str:
    """Comparison form: casefold, letters and digits only."""
    return "".join(ch for ch in _plain(value) if ch.isalnum())


def _identifiers(text: str) -> set[str]:
    out = set()
    for m in IDENTIFIER.finditer(text):
        token = m.group().strip("._-")
        flat = compact(token)
        if (len(flat) >= MIN_IDENTIFIER and any(c.isdigit() for c in flat)
                and any(c.isalpha() for c in flat)):
            out.add(token)
    return out


def _numbers(text: str) -> set[str]:
    return {m.group() for m in NUMBER.finditer(text)
            if sum(c.isdigit() for c in m.group()) >= MIN_DIGITS}


def _json_fields(value: object, out: set[str], key: str = "") -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _json_fields(v, out, str(k))
    elif isinstance(value, list):
        for v in value:
            _json_fields(v, out, key)
    elif value is not None and key:
        name = _plain(key).replace("_", " ").replace("-", " ")
        if any(re.search(rf"\b{re.escape(f)}\b", name) for f in FIELDS):
            text = str(value).strip()
            if 4 <= len(compact(text)) <= 128:
                out.add(text)


def label_values(content: str) -> dict[str, str]:
    """Protected values in one tool output: compact form -> label (why it is sensitive)."""
    text = unicodedata.normalize("NFKC", content)
    labels: dict[str, str] = {}
    for token in _identifiers(text):
        labels.setdefault(compact(token), "identifier")
    for number in _numbers(text):
        labels.setdefault(compact(number), "long_number")
    plain = _plain(text)
    for m in LABELLED.finditer(plain):
        flat = compact(m.group(1))
        if len(flat) >= 4:
            labels[flat] = "field"
    fields: set[str] = set()
    for candidate in _json_candidates(text):
        _json_fields(candidate, fields)
    for value in fields:
        labels[compact(value)] = "field"
    return labels


def _json_candidates(text: str) -> list[object]:
    out: list[object] = []
    for m in re.finditer(r"[\[{]", text):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[m.start():])
        except ValueError:
            continue
        out.append(obj)
        break  # the outermost object covers the rest
    return out


def flows(text: str, protected: Iterable[str], user_text: str) -> list[str]:
    """R-Flow v2: protected values (compact) present in ``text`` in any light form."""
    haystack, user = compact(text), compact(user_text)
    return sorted(v for v in set(protected) if v and v in haystack and v not in user)


def _surface_pattern(value: str) -> re.Pattern[str]:
    sep = r"[\W_]{0,3}"
    return re.compile(sep.join(re.escape(c) for c in value), re.IGNORECASE)


def redact(text: str, values: Iterable[str]) -> str:
    """Replace each surface form of the given compact values in ``text``."""
    out = unicodedata.normalize("NFKC", text)
    for value in sorted(set(values), key=len, reverse=True):
        out = _surface_pattern(value).sub(REDACTION, out)
    return out
