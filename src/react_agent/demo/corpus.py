"""Demo environment: the clean v1.1 environment plus labelled demo documents.

``data/demo/demo_documents.json`` holds the clean demo documents and
``data/demo/injected_documents.json`` (optional, written by the team) the injected ones.
Each record carries host labels: ``sensitivity`` S0/S2 and ``trust`` T0 (trusted) or
T1/T2 (untrusted). Labels go to the host source catalog, never to the model.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from react_agent.foundation.artifacts import Sensitivity, SourceType, Trust, canonical_json
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.tools import doc_search_v2
from react_agent.tools.factory import build_clean_registry
from react_agent.tools.registry import ToolRegistry

DEMO_FILES = ("demo_documents.json", "injected_documents.json")


class DemoDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    doc_id: str = Field(pattern=r"^(DEMO|INJ|UP)_[0-9]{3}$")
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    sensitivity: Literal["S0", "S2"] = "S0"
    trust: Literal["T0", "T1", "T2"] = "T1"

    def label(self) -> SourceLabel:
        return SourceLabel(
            source_type=SourceType.DOCUMENT,
            source_id=self.doc_id,
            sensitivity=Sensitivity(self.sensitivity),
            trust=Trust.TRUSTED if self.trust == "T0" else Trust.UNTRUSTED,
            legacy_trust=self.trust,
        )


def load_demo_documents(demo_data: Path) -> list[DemoDocument]:
    documents: list[DemoDocument] = []
    for name in DEMO_FILES:
        path = demo_data / name
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            documents.extend(DemoDocument.model_validate(item) for item in raw)
    ids = [d.doc_id for d in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate doc_id in the demo documents")
    return documents


def catalog_for(documents: list[DemoDocument]) -> SourceCatalog:
    return SourceCatalog(bindings=tuple(
        SourceBinding(tool="doc_read", arguments_json=canonical_json({"doc_id": d.doc_id}),
                      label=d.label())
        for d in documents))


def build_environment(
    clean: Path, documents: list[DemoDocument], destination: Path
) -> tuple[ToolRegistry, SourceCatalog]:
    """Fresh copy of the clean environment with the demo documents appended."""
    source, dest = clean.resolve(), destination.resolve()
    if dest.exists() or dest.is_relative_to(source):
        raise ValueError("demo environment destination must be fresh and outside the clean one")
    shutil.copytree(source, dest)
    path = dest / "documents" / "documents.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    existing = {r["doc_id"] for r in records}
    for d in documents:
        if d.doc_id in existing:
            raise ValueError(f"demo doc_id {d.doc_id} collides with the clean environment")
        records.append({"doc_id": d.doc_id, "title": d.title, "content": d.content})
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = doc_search_v2.apply_e2(build_clean_registry(dest), dest)
    return registry, catalog_for(documents)
