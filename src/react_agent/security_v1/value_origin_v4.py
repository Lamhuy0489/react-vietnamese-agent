"""Opt-in bounded protection for mixed-alphanumeric literals in S1/S2 prose.

This is a development candidate after the stopped prospective pilot, not a
replacement for the frozen v3 index or a claim of arbitrary-secret coverage.
Only observed sensitive FREE_TEXT roots can create supplemental origins.
"""

from __future__ import annotations

import re
from typing import Any

from react_agent.foundation.artifacts import Artifact, Sensitivity
from react_agent.security_v1.value_origin import (
    MAX_INDEX_BYTES,
    MAX_RECORDS,
    OriginError,
    OriginRecord,
    ValueType,
    canonical_value,
)
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as PreviousIndex

PROFILE = "sensitive_embedded_identifier_v4_dev"
MAX_EMBEDDED_PER_SOURCE = 64
EMBEDDED_IDENTIFIER = re.compile(
    r"(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9_-]{7,63}(?![A-Za-z0-9_-])"
)


class ValueOriginIndex(PreviousIndex):
    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "profile": PROFILE}

    def _extract(self, artifact: Artifact) -> list[OriginRecord]:
        records = super()._extract(artifact)
        seen = {(r.pointer, r.value_type, r.value) for r in records}
        typed_literals = {
            (r.pointer, r.value) for r in records if r.value_type != ValueType.FREE_TEXT
        }
        embedded_count = 0
        for source in tuple(records):
            if (
                source.sensitivity <= Sensitivity.PUBLIC
                or source.value_type != ValueType.FREE_TEXT
            ):
                continue
            for match in EMBEDDED_IDENTIFIER.finditer(source.value):
                token = match.group()
                if not any(char.isdigit() for char in token):
                    continue
                value = canonical_value(token, ValueType.IDENTIFIER)
                key = (source.pointer, ValueType.IDENTIFIER, value)
                if key in seen or (source.pointer, value) in typed_literals:
                    continue
                embedded_count += 1
                if embedded_count > MAX_EMBEDDED_PER_SOURCE:
                    raise OriginError("sensitive embedded identifier budget exceeded")
                records.append(
                    OriginRecord(
                        artifact_id=artifact.artifact_id,
                        source_sha256=artifact.content_hash,
                        pointer=source.pointer,
                        value_type=ValueType.IDENTIFIER,
                        value=value,
                        sensitivity=artifact.sensitivity,
                        trust=artifact.trust,
                    )
                )
                seen.add(key)
                typed_literals.add((source.pointer, value))
        if (
            len(records) > MAX_RECORDS
            or self._record_bytes
            + sum(len(record.model_dump_json().encode("utf-8")) for record in records)
            > MAX_INDEX_BYTES
        ):
            raise OriginError("embedded extraction exceeds index budget")
        return records
