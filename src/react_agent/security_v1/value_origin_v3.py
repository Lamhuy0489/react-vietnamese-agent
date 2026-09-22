"""Supplement exact raw-host destination literals, not model-inferred origins."""

from __future__ import annotations

from typing import Any

from react_agent.foundation.artifacts import Artifact, ArtifactType, SourceType
from react_agent.security_v1.authorization_anchors_v3 import extract_anchors
from react_agent.security_v1.value_origin import (
    MAX_INDEX_BYTES,
    MAX_RECORDS,
    OriginError,
    OriginRecord,
    ValueType,
    canonical_value,
)
from react_agent.security_v1.value_origin_v2 import ValueOriginIndex as PreviousIndex

PROFILE = "host_destination_origin_v3"


class ValueOriginIndex(PreviousIndex):
    def snapshot(self) -> dict[str, Any]:
        return {**super().snapshot(), "profile": PROFILE}

    def _extract(self, artifact: Artifact) -> list[OriginRecord]:
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
            for kind, values in (
                (ValueType.EMAIL, anchors.emails),
                (ValueType.URL, anchors.endpoints),
            ):
                for value in values:
                    # Only literal spans in this exact admitted source. Never copy
                    # provenance from a different root or reduce a source's labels.
                    if value not in raw:
                        raise OriginError("destination absent from raw host source")
                    records.append(
                        OriginRecord(
                            artifact_id=artifact.artifact_id,
                            source_sha256=artifact.content_hash,
                            pointer="",
                            value_type=kind,
                            value=canonical_value(value, kind),
                            sensitivity=artifact.sensitivity,
                            trust=artifact.trust,
                        )
                    )
        records = list({(r.pointer, r.value_type, r.value): r for r in records}.values())
        if (
            len(records) > MAX_RECORDS
            or self._record_bytes + sum(len(r.model_dump_json().encode("utf-8")) for r in records)
            > MAX_INDEX_BYTES
        ):
            raise OriginError("destination extraction exceeds index budget")
        return records
