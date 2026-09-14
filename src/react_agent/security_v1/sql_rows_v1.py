"""Non-executing finite SQL grammar and host row inventory; no evaluator imports."""

from __future__ import annotations

import json
import re
from typing import Self

from pydantic import model_validator

from react_agent.foundation.artifacts import Immutable, SourceType
from react_agent.foundation.runtime_hooks import SourceCatalog
from react_agent.security_v1.resource_bindings_v1 import EXTENSION_ID

IDENT = r"[A-Za-z_][A-Za-z0-9_]{0,63}"
VALUE = r"'(?:AWB|AUX)_[A-Z][A-Z0-9_]{0,63}'"
SELECT = re.compile(
    rf"\s*SELECT\s+(?P<columns>{IDENT}(?:\s*,\s*{IDENT})*)"
    rf"\s+FROM\s+(?P<table>{IDENT})\s+WHERE\s+(?P<key>{IDENT})\s*"
    rf"(?:=\s*(?P<one>{VALUE})|IN\s*\(\s*(?P<many>{VALUE}(?:\s*,\s*{VALUE})*)\s*\))\s*",
    re.IGNORECASE | re.ASCII,
)


class RowSelection(Immutable):
    table: str
    columns: tuple[str, ...]
    key: str
    values: tuple[str, ...]

    @property
    def accessed_columns(self) -> tuple[str, ...]:
        return tuple(sorted(set((*self.columns, self.key))))


def parse_rows(query: object) -> RowSelection | None:
    if not isinstance(query, str) or len(query) > 2000:
        return None
    match = SELECT.fullmatch(query)
    if match is None:
        return None
    columns = tuple(part.strip().casefold() for part in match["columns"].split(","))
    values = tuple(value.strip()[1:-1] for value in (match["one"] or match["many"]).split(","))
    if (
        not values
        or len(values) > 32
        or len(columns) > 32
        or len(columns) != len(set(columns))
        or len(values) != len(set(values))
        or any(EXTENSION_ID.fullmatch(v) is None for v in values)
    ):
        return None
    return RowSelection(
        table=match["table"].casefold(),
        columns=tuple(sorted(columns)),
        key=match["key"].casefold(),
        values=tuple(sorted(values)),
    )


class RowBinding(Immutable):
    table: str
    key: str
    value: str

    @model_validator(mode="after")
    def identifiers(self) -> Self:
        if any(re.fullmatch(IDENT, x) is None or x != x.casefold() for x in (self.table, self.key)):
            raise ValueError("canonical table/key identifiers required")
        if EXTENSION_ID.fullmatch(self.value) is None or self.value.casefold() in {
            self.table,
            self.key,
        }:
            raise ValueError("bounded synthetic row identity required")
        return self


class RowBindings(Immutable):
    rows: tuple[RowBinding, ...] = ()

    @model_validator(mode="after")
    def unambiguous(self) -> Self:
        identities = tuple(r.value for r in self.rows)
        if (
            len(identities) > 256
            or len(set(identities)) != len(identities)
            or identities != tuple(sorted(identities))
        ):
            raise ValueError("bounded canonical unambiguous row inventory required")
        return self

    @classmethod
    def from_catalog(cls, catalog: SourceCatalog) -> RowBindings:
        rows = []
        for binding in catalog.bindings:
            if (
                binding.tool != "db_query"
                or EXTENSION_ID.fullmatch(binding.label.source_id) is None
            ):
                continue
            arguments = json.loads(binding.arguments_json)
            query = arguments.get("query")
            selection = parse_rows(query)
            if (
                set(arguments) != {"query"}
                or selection is None
                or binding.label.source_type != SourceType.DATABASE
                or selection.values != (binding.label.source_id,)
            ):
                raise ValueError("host row source requires exact finite single-row binding")
            rows.append(
                RowBinding(table=selection.table, key=selection.key, value=selection.values[0])
            )
        unique = {row.value: row for row in rows}
        if any(unique[row.value] != row for row in rows):
            raise ValueError("row identity maps to conflicting table or key")
        return cls(rows=tuple(unique[value] for value in sorted(unique)))
