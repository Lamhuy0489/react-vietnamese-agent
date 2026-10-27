"""Bounded full-value encoding screen for FINAL only; no grant or source inference."""
from __future__ import annotations

import base64
from typing import Any, cast

from react_agent.foundation.artifacts import Sensitivity
from react_agent.security_v1.final_entitlements import EntitledFinalRelease
from react_agent.security_v1.final_entitlements_v2 import (
    FinalEntitlement,
    release_final_with_entitlement,
    strict_protected_matches,
)
from react_agent.security_v1.guard_bare_json_v1 import bind
from react_agent.security_v1.value_origin import (
    MAX_BYTES,
    MAX_SCAN_WORK,
    OriginError,
    ProtectedMatch,
)
from react_agent.security_v1.value_origin_v3 import ValueOriginIndex
from react_agent.serving.structured_api_v1 import sha

PROFILE = "final_encoded_full_value_v1"


def encoded_matches(index: ValueOriginIndex, text: str) -> list[dict[str, Any]]:
    """Detect only full canonical UTF-8 values, never arbitrary decoding/semantic lineage.

    Standard/URL Base64 padded/unpadded and lower/upper hex are covered. Exact
    substrings are conservatively rejected even when a public value collides.
    No transformed representation is granted by a raw-value entitlement.
    """
    if not index.complete or len(text.encode()) > MAX_BYTES:
        raise OriginError("encoded screening unavailable or exceeds byte budget")
    work = 0
    matches = []
    for origin in index.records:
        if origin.sensitivity <= Sensitivity.PUBLIC:
            continue
        raw = origin.value.encode("utf-8")
        if not raw:
            raise OriginError("empty protected encoding")
        standard, url = base64.b64encode(raw).decode(), base64.urlsafe_b64encode(raw).decode()
        values = {"base64": standard, "base64_unpadded": standard.rstrip("="),
                  "base64url": url, "base64url_unpadded": url.rstrip("="),
                  "hex_lower": raw.hex(), "hex_upper": raw.hex().upper()}
        for encoding, value in values.items():
            work += len(text) + len(value)
            if work > MAX_SCAN_WORK:
                raise OriginError("encoded screening exceeds work budget")
            start = text.find(value)
            if start >= 0:
                matches.append({"artifact_id": origin.artifact_id, "pointer": origin.pointer,
                    "source_sha256": origin.source_sha256, "encoding": encoding,
                    "encoded_sha256": sha(value.encode()), "start": start,
                    "end": start + len(value)})
    return matches


class EncodedFinalGate:
    """Reuse the frozen release algorithm with an additional conservative screen."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def __call__(self, index: ValueOriginIndex, proposal_id: str, user_id: str,
                 grant: FinalEntitlement) -> EntitledFinalRelease:
        before = index.snapshot()
        detections: list[dict[str, Any]] = []
        errors: list[str] = []

        def screen(bound: ValueOriginIndex, text: str) -> tuple[ProtectedMatch, ...]:
            raw = strict_protected_matches(bound, text)
            try:
                hits = encoded_matches(bound, text)
            except OriginError:
                errors.append("ENCODED_SCREEN_UNAVAILABLE")
                raise
            detections.extend(hits)
            if hits:
                raise OriginError("encoded protected value in final")
            return raw

        release = cast(EntitledFinalRelease, bind(release_final_with_entitlement,
            strict_protected_matches=screen, RELEASE_PROFILE=PROFILE)(
                index, proposal_id, user_id, grant))
        if index.snapshot() != before:
            raise OriginError("final screen mutated source index")
        self.records.append({"profile": PROFILE, "proposal_id": proposal_id,
            "index_sha256": index.identity, "encoded_matches": detections,
            "screen_errors": errors, "release": release.model_dump(mode="json")})
        return release
