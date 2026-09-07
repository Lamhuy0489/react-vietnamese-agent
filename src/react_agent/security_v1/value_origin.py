"""Run-local, typed observable origin evidence; never causal model attribution."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from pydantic import Field

from react_agent.foundation.artifacts import (
    Artifact,
    ArtifactStore,
    ArtifactType,
    Immutable,
    Sensitivity,
    SourceType,
    Trust,
    canonical_json,
    join_sensitivity,
    join_trust,
)
from react_agent.foundation.normalization import normalize, text_hash

MAX_BYTES = 131_072
MAX_DEPTH = 32
MAX_RECORDS = 10_000
MAX_MATCHES = 4096
MAX_SCAN_WORK = 8_388_608
MAX_SOURCES = 4096
MAX_INDEX_BYTES = 8_388_608
PROFILE = "typed_value_origin_v1"


class ValueType(StrEnum):
    EMAIL = "EMAIL"
    URL = "URL"
    STUDENT_ID = "STUDENT_ID"
    COURSE_CODE = "COURSE_CODE"
    PHONE = "PHONE"
    GPA = "GPA"
    MONEY = "MONEY"
    DATE = "DATE"
    IDENTIFIER = "IDENTIFIER"
    FREE_TEXT = "FREE_TEXT"


PATTERNS = {
    ValueType.EMAIL: r"[A-Za-z0-9_.+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,20}",
    ValueType.URL: r"(?:https?://|mock://)[^\s<>\"'`]{1,512}",
    ValueType.STUDENT_ID: r"SV[0-9]{6,12}",
    ValueType.COURSE_CODE: r"[A-Z]{2,6}[0-9]{3,4}",
    ValueType.PHONE: r"\+?[0-9]{9,15}",
    ValueType.DATE: r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
    ValueType.IDENTIFIER: r"[A-Za-z0-9][A-Za-z0-9_-]{5,63}",
}
FIELDS = {
    "email": ValueType.EMAIL,
    "url": ValueType.URL,
    "endpoint": ValueType.URL,
    "student_id": ValueType.STUDENT_ID,
    "course_code": ValueType.COURSE_CODE,
    "phone": ValueType.PHONE,
    "gpa": ValueType.GPA,
    "amount": ValueType.MONEY,
    "money": ValueType.MONEY,
    "date": ValueType.DATE,
    "internal_record_id": ValueType.IDENTIFIER,
    "record_id": ValueType.IDENTIFIER,
}
LEXICAL = (
    ValueType.EMAIL,
    ValueType.URL,
    ValueType.STUDENT_ID,
    ValueType.COURSE_CODE,
    ValueType.DATE,
)
DECIMAL = re.compile(r"[+-]?[0-9]{1,12}(?:\.[0-9]{1,8})?")
GPA_CUE = re.compile(r"(?:\bgpa|điểm trung bình)\s*[:=]?\s*$", re.I)
MONEY_CUE = re.compile(r"(?:\bamount|\bmoney|số tiền)\s*[:=]?\s*$", re.I)


class OriginError(ValueError):
    """Sanitized integrity/coverage failure; never include source content."""


def canonical_value(value: object, kind: ValueType) -> str:
    if kind in {ValueType.GPA, ValueType.MONEY}:
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
            raise ValueError("typed finite decimal required")
        raw = str(value)
        if DECIMAL.fullmatch(raw) is None:
            raise ValueError("bounded plain decimal required")
        try:
            number = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("invalid numeric value") from exc
        if not number.is_finite() or (kind == ValueType.GPA and not 0 <= number <= 4):
            raise ValueError("numeric value outside profile")
        return "0" if number == 0 else format(number.normalize(), "f")
    if not isinstance(value, str):
        raise ValueError("typed string required")
    if kind == ValueType.FREE_TEXT:
        if not 12 <= len(value) <= 32768 or not value.strip():
            raise ValueError("free text outside profile")
    elif re.fullmatch(PATTERNS[kind], value) is None:
        raise ValueError("string outside typed profile")
    if kind == ValueType.DATE:
        date.fromisoformat(value)
    return value


class OriginRecord(Immutable):
    artifact_id: str
    source_sha256: str
    pointer: str
    value_type: ValueType
    value: str
    sensitivity: Sensitivity
    trust: Trust


class OriginAssessment(Immutable):
    known: bool
    origins: tuple[OriginRecord, ...] = ()
    max_sensitivity: Sensitivity | None = None
    trust: Trust | None = None


class ProtectedMatch(Immutable):
    origin: OriginRecord
    view: str
    start: int = Field(ge=0)
    end: int = Field(ge=1)


def bounded_span(text: str, start: int, end: int, kind: ValueType) -> bool:
    if kind == ValueType.FREE_TEXT:
        return True
    extra = (
        "._+-@"
        if kind == ValueType.EMAIL
        else "."
        if kind in {ValueType.GPA, ValueType.MONEY}
        else "_-/"
    )
    return not (
        start > 0
        and (text[start - 1].isalnum() or text[start - 1] in extra)
        or end < len(text)
        and (text[end].isalnum() or text[end] in extra)
    )


def spans(text: str, value: str, kind: ValueType) -> tuple[tuple[int, int], ...]:
    found = []
    if kind in {ValueType.GPA, ValueType.MONEY}:
        cue = GPA_CUE if kind == ValueType.GPA else MONEY_CUE
        for match in DECIMAL.finditer(text):
            if not bounded_span(text, match.start(), match.end(), kind):
                continue
            try:
                same = canonical_value(match.group(), kind) == value
            except ValueError:
                continue
            integral = Decimal(value) == Decimal(value).to_integral_value()
            if same and (
                not integral or cue.search(text[max(0, match.start() - 32) : match.start()])
            ):
                found.append(match.span())
    else:
        for match in re.finditer(re.escape(value), text):
            if bounded_span(text, match.start(), match.end(), kind):
                found.append(match.span())
    return tuple(found)


class ValueOriginIndex:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        self._records: list[OriginRecord] = []
        self._admitted: dict[str, str] = {}
        self._last_step = 0
        self._complete = True
        self._record_bytes = 0

    @property
    def complete(self) -> bool:
        return self._complete

    @property
    def records(self) -> tuple[OriginRecord, ...]:
        return tuple(self._records)

    @property
    def last_observed_step(self) -> int:
        return self._last_step

    def snapshot(self) -> dict[str, Any]:
        return {
            "profile": PROFILE,
            "run_id": self.store.run_id,
            "complete": self.complete,
            "last_observed_step": self._last_step,
            "source_sha256": dict(self._admitted),
            "records": [r.model_dump(mode="json") for r in self.records],
        }

    @property
    def identity(self) -> str:
        return text_hash(canonical_json(self.snapshot()))

    def add_artifact(self, artifact_id: str, *, observed_step: int) -> None:
        if not self.complete:
            raise OriginError("index incomplete; fresh task required")
        try:
            artifact = self.store.get(artifact_id)
            if (
                type(observed_step) is not int
                or observed_step < self._last_step
                or artifact.created_step > observed_step
            ):
                raise OriginError("non-monotone/future observation")
            eligible_user = (
                artifact.source_type == SourceType.USER
                and artifact.producer == "host_context"
                and artifact.artifact_type == ArtifactType.USER_INPUT
            )
            eligible_tool = (
                artifact.producer == "tool_source_snapshot"
                and artifact.source_type
                not in {SourceType.USER, SourceType.SYSTEM, SourceType.MODEL}
            )
            if (
                artifact.parents
                or artifact.transformations
                or artifact.artifact_type
                in {
                    ArtifactType.MODEL_OUTPUT,
                    ArtifactType.TOOL_ARGUMENT,
                    ArtifactType.FINAL_RESPONSE,
                    ArtifactType.NORMALIZED_VIEW,
                }
                or not (eligible_user or eligible_tool)
            ):
                raise OriginError("only observed raw source roots are eligible")
            if artifact_id in self._admitted:
                self._last_step = observed_step
                return
            if len(artifact.raw_json.encode("utf-8")) > MAX_BYTES:
                raise OriginError("source exceeds byte budget")
            if len(self._admitted) >= MAX_SOURCES:
                raise OriginError("index exceeds source budget")
            pending = self._extract(artifact)
            if len(self._records) + len(pending) > MAX_RECORDS:
                raise OriginError("index exceeds record budget")
        except (ValueError, RecursionError) as exc:
            self._complete = False
            raise OriginError("source admission failed; coverage incomplete") from exc
        self._records.extend(pending)
        self._record_bytes += sum(len(r.model_dump_json().encode("utf-8")) for r in pending)
        self._admitted[artifact_id] = artifact.content_hash
        self._last_step = observed_step

    def _extract(self, artifact: Artifact) -> list[OriginRecord]:
        result: dict[tuple[str, ValueType, str], OriginRecord] = {}
        pending_bytes = 0

        def emit(value: object, kind: ValueType, pointer: str) -> None:
            nonlocal pending_bytes
            try:
                canonical = canonical_value(value, kind)
            except ValueError:
                return  # Unassessed by the frozen extraction profile, not a coverage success claim.
            if (pointer, kind, canonical) in result:
                return
            record = OriginRecord(
                artifact_id=artifact.artifact_id,
                source_sha256=artifact.content_hash,
                pointer=pointer,
                value_type=kind,
                value=canonical,
                sensitivity=artifact.sensitivity,
                trust=artifact.trust,
            )
            pending_bytes += len(record.model_dump_json().encode("utf-8"))
            if pending_bytes + self._record_bytes > MAX_INDEX_BYTES:
                raise OriginError("index exceeds byte budget")
            result[(pointer, kind, canonical)] = record
            if len(result) > MAX_RECORDS:
                raise OriginError("source exceeds record budget")

        def walk(value: Any, pointer: str, field: str, depth: int) -> None:
            if depth > MAX_DEPTH:
                raise OriginError("source exceeds nesting budget")
            if isinstance(value, dict):
                table = (
                    artifact.source_type == SourceType.DATABASE
                    and {"columns", "rows"} <= value.keys()
                )
                if table:
                    columns, rows = value["columns"], value["rows"]
                    if (
                        not isinstance(columns, list)
                        or not all(isinstance(c, str) for c in columns)
                        or len({c.casefold() for c in columns}) != len(columns)
                        or not isinstance(rows, list)
                    ):
                        raise OriginError("ambiguous database result schema")
                    for i, row in enumerate(rows):
                        if not isinstance(row, list) or len(row) != len(columns):
                            raise OriginError("database row/column mismatch")
                        for j, item in enumerate(row):
                            walk(item, pointer + f"/rows/{i}/{j}", columns[j].casefold(), depth + 3)
                for key, item in value.items():
                    if table and key in {"columns", "rows"}:
                        continue
                    escaped = key.replace("~", "~0").replace("/", "~1")
                    walk(item, pointer + "/" + escaped, key.casefold(), depth + 1)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    walk(item, pointer + "/" + str(i), field, depth + 1)
            else:
                if field in FIELDS:
                    emit(value, FIELDS[field], pointer)
                if isinstance(value, str):
                    if len(value) > 32768:
                        raise OriginError("scalar exceeds text budget")
                    typed_whole = any(re.fullmatch(PATTERNS[k], value) for k in LEXICAL)
                    if field not in FIELDS and not typed_whole:
                        emit(value, ValueType.FREE_TEXT, pointer)
                    for kind in LEXICAL:
                        for match in re.finditer(PATTERNS[kind], value):
                            if bounded_span(value, match.start(), match.end(), kind):
                                emit(match.group(), kind, pointer)

        walk(artifact.content(), "", "", 0)
        return list(result.values())

    def find_origins(self, value: object, kind: ValueType) -> OriginAssessment:
        if not self.complete:
            raise OriginError("index coverage incomplete")
        key = canonical_value(value, kind)
        matches = tuple(r for r in self.records if r.value_type == kind and r.value == key)
        return OriginAssessment(
            known=bool(matches),
            origins=matches,
            max_sensitivity=join_sensitivity(*(r.sensitivity for r in matches))
            if matches
            else None,
            trust=join_trust(*(r.trust for r in matches)) if matches else None,
        )

    def protected_matches(
        self, text: str, *, clearance: Sensitivity = Sensitivity.PUBLIC
    ) -> tuple[ProtectedMatch, ...]:
        if not self.complete or len(text.encode("utf-8")) > MAX_BYTES:
            raise OriginError("protected scan unavailable or exceeds budget")
        normalized = normalize(text, "security_v1").normalized_text
        protected = tuple(r for r in self.records if r.sensitivity > clearance)
        if len(protected) * max(len(text), len(normalized)) > MAX_SCAN_WORK:
            raise OriginError("protected scan exceeds work budget")
        result = []
        for record in protected:
            normalized_value = normalize(record.value, "security_v1").normalized_text
            if not normalized_value.strip():
                raise OriginError("protected value has no usable normalized representation")
            raw_spans = spans(text, record.value, record.value_type)
            for start, end in raw_spans:
                result.append(ProtectedMatch(origin=record, view="raw_v1", start=start, end=end))
            # Detection-only normalized evidence never grants an origin or raw offset.
            if not raw_spans and (normalized != text or normalized_value != record.value):
                for start, end in spans(normalized, normalized_value, record.value_type):
                    result.append(
                        ProtectedMatch(origin=record, view="security_v1", start=start, end=end)
                    )
            if len(result) > MAX_MATCHES:
                raise OriginError("protected scan exceeds match budget")
        return tuple(result)
