"""Opt-in conservative raw-user sentence anchors; not general language authorization."""

from __future__ import annotations

import re

from react_agent.foundation.normalization import text_hash
from react_agent.security_v1.rules import (
    NEGATED,
    AuthorizationAnchors,
)
from react_agent.security_v1.rules import (
    extract_anchors as original,
)

PROFILE = "raw_user_sentence_anchors_v2"
READ = re.compile(r"^\s*(?:(?:hãy|hay|please)\s+)?(?:đọc|doc|read|tra)\b", re.I)
SEND = re.compile(
    r"^\s*(?:chỉ\s+|chi\s+)?(?:(?:hãy|hay|please)\s+)?(?:gửi|gởi|gui|send|post)\b", re.I
)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-ZĐÀ-Ỹ])")
QUOTES = ('"', "'", "`", "“", "”", "‘", "’", ">")


def extract_anchors(raw_user: str) -> AuthorizationAnchors:
    """Retain v1 grants; extend only unquoted, nonnegative read-then-send blocks.

    A negation/conditional or quotation anywhere in the original semicolon/newline
    block suppresses extensions for that block. Never strip those constructs to
    promote their contents. URLs and emails are not split at internal dots.
    """
    baseline = original(raw_user)
    emails, endpoints = set(baseline.emails), set(baseline.endpoints)
    for block in re.split(r"[\n;]", raw_user):
        if NEGATED.search(block) or any(mark in block for mark in QUOTES):
            continue
        sentences = SENTENCE.split(block)
        if len(sentences) < 2 or not READ.search(sentences[0]):
            continue
        # Every prior sentence must be an explicit read directive, never prose
        # like "example", a reported instruction, conditional or role dialogue.
        for index, sentence in enumerate(sentences[1:], 1):
            if not all(READ.search(s) for s in sentences[:index]):
                break
            if not SEND.search(sentence):
                continue
            candidate = re.sub(r"^\s*(?:chỉ|chi)\s+", "", sentence, flags=re.I)
            found = original(candidate)
            emails.update(
                address
                for address in found.emails
                if re.search(re.escape(address) + r"(?=$|[\s,;.!?)])", candidate)
            )
            endpoints.update(found.endpoints)
    return AuthorizationAnchors(
        emails=tuple(sorted(emails)),
        endpoints=tuple(sorted(endpoints)),
        raw_user_sha256=text_hash(raw_user),
    )
