"""C3: parameter integrity, pinning the values the user stated for a granted sink.

Design: ``docs/project/brokerguard_v3_extension_design.md`` section 3 (C3).

A tampering attack keeps the user's destination and changes a parameter (an amount, a
status, a unit, a code). C1 grants the sink; C3 checks its arguments against the clause of
u that granted it. Pinned literals of that clause:

- numbers ("4200", "6,5") after the sending verb and outside arithmetic expressions
  (operands and values read earlier are inputs); a unit stated with the number ("45 cm3")
  conflicts when the payload drops it and uses another known unit; a unit named after
  "đơn vị/unit" ("với đơn vị psi") must be present;
- booleans true/false with polarity: one after a negation ("cấm đổi sang false") is a
  forbidden value, not a pinned one ("đúng/sai" are not pinned: too ambiguous);
- identifiers stated by the user (letters and digits, e.g. "REMIT_9901");
- when u declares the values fixed ("cấm chỉnh sửa", "không thay đổi", "forbidding
  modifying"), every number stated in that sentence.

A call violates C3 when a pinned literal is missing from its data arguments (compared in
compact form) or when it carries the opposite of a pinned boolean. A call matched by
several grants (same tool and target) passes if any one of them is satisfied.
Tunable on Dev only: the unit list and which literal kinds are pinned.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from react_agent.security_v3.intent_policy_v1 import (
    SINKS,
    Grant,
    Polarity,
    normalise_target,
    strip_marks,
)
from react_agent.security_v3.value_labels_v1 import compact

PROFILE = "param_pinning_v1"
UNITS = ("ml", "l", "lit", "cm3", "cm2", "cm", "mm", "m3", "m2", "m", "km", "kg", "g", "mg",
         "tan", "tấn", "%", "vnd", "đ", "usd", "eur", "kwh", "mw", "gb", "mb", "tb",
         # common measurement units (a general lexicon, not tuned per case)
         "psi", "mmhg", "bar", "kpa", "pa", "hz", "khz", "mhz", "ghz", "kv", "kw", "°c", "°f",
         "lb", "lbs", "oz", "ton", "tons", "ft", "inch", "mi", "cc", "iu", "mmol", "bpm",
         "mm2", "km2", "ha", "lux", "db", "rpm", "kcal")
_UNIT_RE = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
INTEGRITY = re.compile(
    r"\b(?:cam|khong duoc|khong|dung|forbid\w*|prohibit\w*|not|never|must not|do not)"
    r"(?:\s+\S+){0,3}?\s+(?:chinh sua|thay doi|sua doi|modify\w*|alter\w*|chang\w*|"
    r"edit\w*|tamper\w*)\b")
UNIT_SET = frozenset(strip_marks(u) for u in UNITS)
EXPLICIT_UNIT = re.compile(
    r"\b(?:don vi(?: tinh| do)?|unit|units|units of)\s+([a-z0-9%°/]{1,12})\b")
UNIT_WORD = re.compile(rf"(?<![\w])(?:{_UNIT_RE})(?![\w])")
NUMBER = re.compile(rf"(?<![\w.,])(\d+(?:[.,]\d+)*)(?:\s*({_UNIT_RE}))?(?![\w])")
BOOLEAN = re.compile(r"\b(true|false)\b")
IDENT = re.compile(r"(?<![\w-])(?=[\w-]*\d)(?=[\w-]*[a-z])[a-z0-9][\w-]{3,63}(?![\w-])")
ARITHMETIC = re.compile(r"\d+(?:[.,]\d+)*(?:\s*[-+*/×÷x]\s*\d+(?:[.,]\d+)*)+")
# Run on the folded clause (diacritics kept). Without diacritics "dung"/"cam" are also
# "dùng"/"cảm", so they count only right before a change or send verb.
NEGATION = re.compile(r"\b(?:không|khong|đừng|cấm|nghiêm cấm|nghiem cam|chớ|tránh|never|not|"
                      r"do not|don't|must not|forbid\w*|prohibit\w*|avoid)\b|"
                      r"\b(?:dung|cam)\s+(?=(?:thay|doi|gui|chinh|sua|chuyen)\b)")
SEND_VERB = re.compile(r"\b(?:gui|goi|send|sends|sending|forward|post|chuyen|transmit\w*|update|"
                       r"cap nhat|email|e-mail|thong bao|notify|report|bao cao|deliver|"
                       r"submit|nop|relay|dispatch)\b")
OPPOSITE = {"true": "false", "false": "true"}


@dataclass(frozen=True)
class Pins:
    literals: tuple[str, ...]  # compact forms that must be present
    booleans: tuple[str, ...]  # stated values
    forbidden: tuple[str, ...] = ()  # values the user rules out ("cấm đổi sang false")
    units: tuple[tuple[str, str], ...] = ()  # (number, unit) stated together


def pins(grant: Grant) -> Pins:
    # Literals before the sending verb are what the agent reads ("lấy 5000 ... gửi 4200").
    verb = SEND_VERB.search(strip_marks(grant.text))
    text = grant.text[verb.start():] if verb else grant.text
    literals: list[str] = []
    units: list[tuple[str, str]] = []
    operands = {i for m in ARITHMETIC.finditer(text) for i in range(m.start(), m.end())}
    for m in NUMBER.finditer(text):
        if m.start() in operands:
            continue  # "tính 500 + 250": operands are inputs, not stated parameters
        literals.append(compact(m.group(1)))
        if m.group(2):
            units.append((compact(m.group(1)), compact(m.group(2))))
    # "với đơn vị psi", "in units of kg": the user names the unit explicitly; it must stay.
    literals += [compact(m.group(1)) for m in EXPLICIT_UNIT.finditer(strip_marks(text))
                 if m.group(1) in UNIT_SET]  # "đơn vị" is also "agency": units only
    # "cấm chỉnh sửa lãi suất": the user declares the values of the sentence fixed, so the
    # numbers stated before the sending verb ("lấy lãi suất 6.5 rồi gửi") are pinned too.
    if INTEGRITY.search(strip_marks(grant.sentence)):
        sentence_ops = {i for m in ARITHMETIC.finditer(grant.sentence)
                        for i in range(m.start(), m.end())}
        literals += [compact(m.group(1)) for m in NUMBER.finditer(grant.sentence)
                     if m.start() not in sentence_ops]
    stated = {u for _, u in units}
    units += [("", compact(m.group())) for m in UNIT_WORD.finditer(text)
              if compact(m.group()) not in stated and len(m.group()) > 1]
    literals += [compact(m.group()) for m in IDENT.finditer(text)
                 if not NUMBER.fullmatch(m.group())]
    allowed: set[str] = set()
    forbidden: set[str] = set()
    cursor = 0
    for m in BOOLEAN.finditer(text):
        negated = bool(NEGATION.search(text, cursor, m.start()))
        (forbidden if negated else allowed).add(m.group(1))
        cursor = m.end()
    return Pins(tuple(dict.fromkeys(v for v in literals if v)),
                tuple(sorted(allowed - forbidden)), tuple(sorted(forbidden)), tuple(units))


def check(tool: str, arguments: Mapping[str, object],
          grants: Sequence[Grant]) -> tuple[str, list[str]] | None:
    """None if the call keeps the pinned values of some matching grant, else a reason."""
    if tool not in SINKS:
        return None
    key, _ = SINKS[tool]
    target = normalise_target(str(arguments.get(key) or ""))
    matching = [g for g in grants
                if g.tool == tool and g.target == target and g.polarity is Polarity.ALLOW]
    if not matching:
        return None  # C1 decides grants; nothing pinned here
    payload = " ".join(str(v) for k, v in arguments.items() if k != key).casefold()
    flat = compact(payload)
    words = set(re.findall(r"\b(?:true|false)\b", payload))
    missing_best: list[str] | None = None
    for grant in matching:
        p = pins(grant)
        missing = [v for v in p.literals if v not in flat]
        flipped = [OPPOSITE[b] for b in p.booleans if OPPOSITE[b] in words and b not in words]
        flipped += [b for b in p.forbidden if b in words and b not in p.booleans]
        # A unit only conflicts when the number is written with another known unit
        # ("45 m3" for "45 cm3"); "8200" + "unit": "kg" or "$" spellings pass.
        # A unit conflicts when the payload drops it and uses another known unit, next to the
        # number ("45 m3" for "45 cm3") or in its own field ("unit": "m3"); "$" spellings pass.
        units_used = {compact(u.group()) for u in UNIT_WORD.finditer(payload)}
        for _number, unit in p.units:
            if unit not in units_used and units_used - {unit}:
                flipped.append(unit)
        if not missing and not flipped:
            return None
        bad = missing + flipped
        if missing_best is None or len(bad) < len(missing_best):
            missing_best = bad
    return "PINNED_PARAMETER_CHANGED", missing_best or []
