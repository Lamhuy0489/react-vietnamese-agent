"""Opt-in host destination provenance for the v4 safe-email candidate.

The frozen :mod:`value_origin_v3` index already records email-shaped text
lexically.  The v4 parser's scoped private-payload prohibition is therefore a
separate authorization concern; this profile makes the pairing explicit and
proves that no new destination authority is copied from model or tool data.
For the current email grammar the candidate records are intentionally
byte-for-byte equivalent to v3, while a future parser change must still pass
the exact raw-host check below.

No model output, tool result, or transformed artifact can create destination
authority.  The candidate admits an email/endpoint only when the v4 parser
found it in the exact raw host instruction and keeps the source's sensitivity
and trust labels.  The frozen v3 index remains untouched and callers must opt
in explicitly.
"""

from __future__ import annotations

from typing import Any

from react_agent.foundation.artifacts import Artifact, ArtifactType, SourceType
from react_agent.security_v1.authorization_anchors_v4 import extract_anchors
from react_agent.security_v1.value_origin import (
    MAX_INDEX_BYTES,
    MAX_RECORDS,
    OriginError,
    OriginRecord,
    ValueType,
    canonical_value,
)
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex as PreviousIndex

PROFILE = "host_destination_origin_v4_email_candidate"


class ValueOriginIndex(PreviousIndex):
    """v3 typed extraction paired with v4 raw-user anchor evidence."""

    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "profile": PROFILE}

    def _extract(self, artifact: Artifact) -> list[OriginRecord]:
        # Keep every v3/v2 admission and its validation.  The supplemental
        # records below are intentionally restricted to the exact host root.
        records = super()._extract(artifact)
        raw = artifact.content()
        if (
            artifact.source_type == SourceType.USER
            and artifact.artifact_type == ArtifactType.USER_INPUT
            and artifact.producer == "host_context"
            and not artifact.parents
            and not artifact.transformations
            and isinstance(raw, str)
        ):
            anchors = extract_anchors(raw)
            existing = {(r.pointer, r.value_type, r.value) for r in records}
            for kind, values in (
                (ValueType.EMAIL, anchors.emails),
                (ValueType.URL, anchors.endpoints),
            ):
                for value in values:
                    # The parser is not allowed to manufacture a destination;
                    # this check also protects against future parser changes.
                    if value not in raw:
                        raise OriginError("destination absent from raw host source")
                    canonical = canonical_value(value, kind)
                    key = ("", kind, canonical)
                    if key in existing:
                        continue
                    records.append(
                        OriginRecord(
                            artifact_id=artifact.artifact_id,
                            source_sha256=artifact.content_hash,
                            pointer="",
                            value_type=kind,
                            value=canonical,
                            sensitivity=artifact.sensitivity,
                            trust=artifact.trust,
                        )
                    )
                    existing.add(key)
        if (
            len(records) > MAX_RECORDS
            or self._record_bytes
            + sum(len(record.model_dump_json().encode("utf-8")) for record in records)
            > MAX_INDEX_BYTES
        ):
            raise OriginError("destination extraction exceeds index budget")
        return records
