"""Bounded typed-field admission: no silent omission of unsupported values.

Adds the project's synthetic student IDs without modifying the sealed v1
extractor. Unknown typed values invalidate coverage instead of being dropped.
"""

from __future__ import annotations

import re
from typing import Any

from react_agent.foundation.artifacts import Artifact, SourceType, join_sensitivity, join_trust
from react_agent.security_v1.value_origin import (
    FIELDS,
    MAX_DEPTH,
    MAX_INDEX_BYTES,
    MAX_RECORDS,
    OriginAssessment,
    OriginError,
    OriginRecord,
    ValueType,
    bounded_span,
    canonical_value,
)
from react_agent.security_v1.value_origin import (
    ValueOriginIndex as LegacyIndex,
)

PROFILE = "typed_value_origin_v2"
SYNTHETIC_STUDENT_ID = re.compile(r"SV_SYN_[0-9]{3,12}")


class ValueOriginIndex(LegacyIndex):
    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "profile": PROFILE}

    def find_origins(self, value: object, kind: ValueType) -> OriginAssessment:
        if (
            kind != ValueType.STUDENT_ID
            or not isinstance(value, str)
            or not SYNTHETIC_STUDENT_ID.fullmatch(value)
        ):
            return super().find_origins(value, kind)
        if not self.complete:
            raise OriginError("index coverage incomplete")
        origins = tuple(r for r in self.records if r.value_type == kind and r.value == value)
        return OriginAssessment(
            known=bool(origins),
            origins=origins,
            max_sensitivity=join_sensitivity(*(r.sensitivity for r in origins))
            if origins
            else None,
            trust=join_trust(*(r.trust for r in origins)) if origins else None,
        )

    def _extract(self, artifact: Artifact) -> list[OriginRecord]:
        records = super()._extract(artifact)

        def walk(value: Any, pointer: str, field: str, depth: int = 0) -> None:
            if depth > MAX_DEPTH:
                raise OriginError("source exceeds nesting budget")
            if isinstance(value, dict):
                if field in FIELDS:
                    raise OriginError("typed scalar has unsupported container")
                table = (
                    artifact.source_type == SourceType.DATABASE
                    and {"columns", "rows"} <= value.keys()
                )
                if table:
                    # The frozen extractor already validates shape, duplicate
                    # columns and row widths before this supplemental traversal.
                    for i, row in enumerate(value["rows"]):
                        for j, item in enumerate(row):
                            walk(
                                item,
                                pointer + f"/rows/{i}/{j}",
                                value["columns"][j].casefold(),
                                depth + 3,
                            )
                for key, child in value.items():
                    if table and key in {"columns", "rows"}:
                        continue
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    walk(child, pointer + "/" + escaped, key.casefold(), depth + 1)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    walk(item, pointer + "/" + str(i), field, depth + 1)
            elif field in FIELDS and value is not None:
                kind = FIELDS[field]
                try:
                    canonical_value(value, kind)
                except ValueError as exc:
                    if (
                        kind != ValueType.STUDENT_ID
                        or not isinstance(value, str)
                        or not SYNTHETIC_STUDENT_ID.fullmatch(value)
                    ):
                        raise OriginError("typed field outside admitted profile") from exc
            if isinstance(value, str):
                for match in SYNTHETIC_STUDENT_ID.finditer(value):
                    if not bounded_span(value, match.start(), match.end(), ValueType.STUDENT_ID):
                        continue
                    records.append(
                        OriginRecord(
                            artifact_id=artifact.artifact_id,
                            source_sha256=artifact.content_hash,
                            pointer=pointer,
                            value_type=ValueType.STUDENT_ID,
                            value=match.group(),
                            sensitivity=artifact.sensitivity,
                            trust=artifact.trust,
                        )
                    )

        walk(artifact.content(), "", "")
        records = list({(r.pointer, r.value_type, r.value): r for r in records}.values())
        if (
            len(records) > MAX_RECORDS
            or self._record_bytes
            + sum(len(record.model_dump_json().encode("utf-8")) for record in records)
            > MAX_INDEX_BYTES
        ):
            raise OriginError("extended extraction exceeds index budget")
        return records
