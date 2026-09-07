"""Deterministic optional Unicode views, never a semantic/security classifier."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

Profile = Literal["raw_v1", "unicode_v1", "security_v1"]
PROFILES: tuple[Profile, ...] = ("raw_v1", "unicode_v1", "security_v1")
ZERO_WIDTH = frozenset("\u200b\u200c\u200d\u2060\ufeff")
VERSION = "normalizer_v1"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="strict")).hexdigest()


@dataclass(frozen=True)
class Operation:
    stage: str
    before_hash: str
    after_hash: str
    changed: bool


@dataclass(frozen=True)
class Features:
    zero_width_positions: tuple[tuple[int, str], ...]
    control_character_count: int
    format_character_count: int
    unusual_whitespace_count: int
    alphabetic_count: int
    ascii_letter_ratio: float
    diacritic_letter_ratio: float
    underscore_density: float


@dataclass(frozen=True)
class NormalizationResult:
    raw_text: str
    normalized_text: str
    profile: Profile
    normalizer_version: str
    unicode_version: str
    input_hash: str
    output_hash: str
    cache_key: str
    operations: tuple[Operation, ...]
    features: Features


def inspect(text: str) -> Features:
    # Canonical composition makes the denominator independent of NFC/NFD spelling.
    letters = [c for c in unicodedata.normalize("NFC", text) if c.isalpha()]
    accented = sum(
        c in "đĐ" or any(unicodedata.combining(d) for d in unicodedata.normalize("NFD", c))
        for c in letters
    )
    return Features(
        zero_width_positions=tuple(
            (i, f"U+{ord(c):04X}") for i, c in enumerate(text) if c in ZERO_WIDTH
        ),
        control_character_count=sum(unicodedata.category(c) == "Cc" for c in text),
        format_character_count=sum(unicodedata.category(c) == "Cf" for c in text),
        unusual_whitespace_count=sum(c.isspace() and c not in " \n" for c in text),
        alphabetic_count=len(letters),
        ascii_letter_ratio=sum(c.isascii() for c in letters) / max(1, len(letters)),
        diacritic_letter_ratio=accented / max(1, len(letters)),
        underscore_density=text.count("_") / max(1, len(text)),
    )


def normalize(text: str, profile: Profile = "raw_v1") -> NormalizationResult:
    if not isinstance(text, str) or profile not in PROFILES:
        raise ValueError("strict text and a known versioned profile required")
    initial = text_hash(text)
    current = text
    operations = []

    def stage(name: str, result: str) -> None:
        nonlocal current
        operations.append(Operation(name, text_hash(current), text_hash(result), current != result))
        current = result

    if profile != "raw_v1":
        stage("unicode_nfkc", unicodedata.normalize("NFKC", current))
    if profile == "security_v1":
        stage("remove_explicit_zero_width", "".join(c for c in current if c not in ZERO_WIDTH))
        stage("unicode_nfkc_recompose", unicodedata.normalize("NFKC", current))
        stage(
            "line_endings",
            current.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\u0085", "\n")
            .replace("\u2028", "\n")
            .replace("\u2029", "\n\n"),
        )
        stage(
            "inline_whitespace", "\n".join(re.sub(r"[^\S\n]+", " ", s) for s in current.split("\n"))
        )
    return NormalizationResult(
        raw_text=text,
        normalized_text=current,
        profile=profile,
        normalizer_version=VERSION,
        unicode_version=unicodedata.unidata_version,
        input_hash=initial,
        output_hash=text_hash(current),
        cache_key=text_hash("\0".join((initial, profile, VERSION, unicodedata.unidata_version))),
        operations=tuple(operations),
        features=inspect(text),
    )
