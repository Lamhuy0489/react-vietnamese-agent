"""Public-only released fixtures. No private oracle, scorer or authoring selection loader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from react_agent.authoring.linked_resources import LinkedResources, build_linked_registry
from react_agent.authoring.overlays import build_overlay_registry
from react_agent.schemas.adversarial_workbench import (
    OverlayScenario,
    PublicWorkbenchTask,
    StrictRecord,
)
from react_agent.tools.registry import ToolRegistry


class ReleasedFixture(StrictRecord):
    schema_version: Literal["adversarial_release_fixture_v2"] = "adversarial_release_fixture_v2"
    variant_id: str = Field(pattern=r"^(ATK|BEN)_CAND_[A-Z]+_[A-Z_]+$")
    pair_id: str
    family_id: str
    canonical_id: str
    group_id: str
    split: Literal["dev", "test"]
    branch: Literal["attack", "benign"]
    variant_type: Literal["no_diacritic", "word_boundary", "zero_width", "code_mix", "paraphrase"]
    task: PublicWorkbenchTask
    overlay: OverlayScenario
    resources: LinkedResources | None

    @model_validator(mode="after")
    def identity(self) -> Self:
        pair = self.family_id + "_" + self.variant_type.upper()
        if (
            self.pair_id != pair
            or self.variant_id != ("ATK_" if self.branch == "attack" else "BEN_") + pair
            or self.task.task_id != self.overlay.task_id
            or (self.resources is not None and self.resources.task_id != self.task.task_id)
        ):
            raise ValueError("release fixture identity mismatch")
        return self

    def registry(self, clean: Path, destination: Path) -> ToolRegistry:
        """Only this environment enters tools; only self.task enters the model prompt."""
        if self.resources is not None:
            return build_linked_registry(
                clean, destination, self.overlay, self.resources, self.branch
            )
        return build_overlay_registry(clean, destination, self.overlay, self.branch)


def load_split(
    release: Path, split: Literal["dev", "test"] = "dev", *, allow_held_out: bool = False
) -> list[ReleasedFixture]:
    """Default Dev path does not parse/open Test payload files. Explicit Test scope required."""
    if split not in {"dev", "test"} or (split == "test" and not allow_held_out):
        raise ValueError("held-out loading requires explicit evaluation scope")
    seal_path = release / "seal.json"
    if not seal_path.is_file():
        raise ValueError("release must be sealed before runtime loading")
    seal = json.loads(seal_path.read_text())
    if seal.get("test_sealed") is not True or seal.get("phase3_accepted") is not True:
        raise ValueError("unaccepted release")
    rows = []
    for branch in ("attack", "benign"):
        name = f"{split}_{branch}.jsonl"
        payload = (release / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != seal["release_sha256"][name]:
            raise ValueError("release split hash mismatch")
        items = [ReleasedFixture.model_validate_json(s) for s in payload.splitlines()]
        if len(items) != (200 if split == "dev" else 150) or any(
            r.branch != branch or r.split != split for r in items
        ):
            raise ValueError("release split count/branch mismatch")
        rows.extend(items)
    if len({r.variant_id for r in rows}) != len(rows):
        raise ValueError("duplicate released variant")
    return rows
