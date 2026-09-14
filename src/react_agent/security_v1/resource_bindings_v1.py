"""Typed host inventory for public extension IDs; never an authorization grant."""

from __future__ import annotations

import json
import re
from typing import Self

from pydantic import model_validator

from react_agent.foundation.artifacts import Immutable, SourceType
from react_agent.foundation.runtime_hooks import SourceCatalog

EXTENSION_ID = re.compile(r"(?:AWB|AUX)_[A-Z][A-Z0-9_]{0,63}\Z")
MAX_RESOURCES = 256


class ResourceBindings(Immutable):
    documents: tuple[str, ...] = ()
    cached_pages: tuple[str, ...] = ()

    @model_validator(mode="after")
    def bounded_unambiguous(self) -> Self:
        names = (*self.documents, *self.cached_pages)
        if (
            len(names) > MAX_RESOURCES
            or len(names) != len(set(names))
            or any(EXTENSION_ID.fullmatch(n) is None for n in names)
            or tuple(sorted(self.documents)) != self.documents
            or tuple(sorted(self.cached_pages)) != self.cached_pages
        ):
            raise ValueError("bounded canonical unambiguous resource identities required")
        return self

    @classmethod
    def from_catalog(cls, catalog: SourceCatalog) -> ResourceBindings:
        documents: list[str] = []
        pages: list[str] = []
        for binding in catalog.bindings:
            shape = {
                "doc_read": ("doc_id", SourceType.DOCUMENT, documents),
                "cached_fetch": ("page_id", SourceType.CACHED_PAGE, pages),
            }.get(binding.tool)
            if shape is None:
                continue
            key, source_type, targets = shape
            arguments = json.loads(binding.arguments_json)
            identity = arguments.get(key)
            if not isinstance(identity, str) or EXTENSION_ID.fullmatch(identity) is None:
                continue
            if arguments != {key: identity} or (
                binding.label.source_type,
                binding.label.source_id,
            ) != (source_type, identity):
                raise ValueError("resource binding must match exact tool, arguments and source")
            targets.append(identity)
        return cls(documents=tuple(sorted(documents)), cached_pages=tuple(sorted(pages)))
