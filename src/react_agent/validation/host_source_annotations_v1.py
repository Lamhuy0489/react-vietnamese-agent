"""Opt-in, pair-wide host labels for prospective public-Dev experiments only.

This module never reads source content or evaluator labels. It does not change
the frozen grouped-Dev catalog or any existing model-run identity.
"""

from __future__ import annotations

from react_agent.adversarial_release import ReleasedFixture
from react_agent.foundation.artifacts import SourceType, Trust
from react_agent.foundation.runtime_hooks import SourceBinding, SourceCatalog, SourceLabel
from react_agent.security_v1.resource_bindings_v1 import ResourceBindings
from react_agent.validation.grouped_dev_inputs_v1 import fixture_catalog
from react_agent.validation.host_inventory_schema_v1 import (
    AuxiliaryAnnotation,
    InventoryPin,
    PairAnnotations,
)


def annotated_pair_catalog(
    attack: ReleasedFixture, benign: ReleasedFixture, annotations: PairAnnotations
) -> SourceCatalog:
    """Require exact pair-wide coverage; unknown IDs and primary overrides fail closed.

    The caller must independently approve and pin the pre-ingestion manifest.
    This function validates structure, not the truth or timing of classification.
    """
    attack = ReleasedFixture.model_validate(attack.model_dump(mode="json"))
    benign = ReleasedFixture.model_validate(benign.model_dump(mode="json"))
    if (
        attack.split != "dev"
        or benign.split != "dev"
        or attack.branch != "attack"
        or benign.branch != "benign"
        or attack.pair_id != benign.pair_id
        or annotations.pair_id != attack.pair_id
    ):
        raise ValueError("exact public Dev attack/benign pair required")
    base = fixture_catalog(attack)
    if base != fixture_catalog(benign):
        raise ValueError("pair has different baseline host catalogs")
    expected = {
        (binding.label.source_type, binding.label.source_id) for binding in base.bindings[1:]
    }
    supplied = {(entry.source_type, entry.source_id) for entry in annotations.entries}
    if supplied != expected:
        raise ValueError("annotation must cover exactly the auxiliary inventory")
    labels: dict[tuple[SourceType, str], AuxiliaryAnnotation] = {
        (entry.source_type, entry.source_id): entry for entry in annotations.entries
    }
    bindings = [base.bindings[0]]
    for binding in base.bindings[1:]:
        entry = labels[binding.label.source_type, binding.label.source_id]
        bindings.append(
            SourceBinding(
                tool=binding.tool,
                arguments_json=binding.arguments_json,
                label=SourceLabel(
                    source_type=entry.source_type,
                    source_id=entry.source_id,
                    sensitivity=entry.sensitivity,
                    trust=Trust.UNTRUSTED,
                ),
            )
        )
    catalog = SourceCatalog(version="host_source_catalog_v2_annotations", bindings=tuple(bindings))
    ResourceBindings.from_catalog(catalog)
    return catalog


def pinned_pair_catalog(
    attack: ReleasedFixture,
    benign: ReleasedFixture,
    pin: InventoryPin,
    *,
    expected_pin_sha256: str,
    source_commit: str,
) -> SourceCatalog:
    """Admit only a separately pinned declaration for this exact public Dev pair.

    The expected hash must come from a predeclared run manifest, not be
    computed from ``pin`` at the call site. This checks identity, not whether
    the owner actually reviewed labels before ingestion.
    """
    # model_copy(update=...) bypasses Pydantic validation; revalidate at the
    # admission boundary before trusting either nested labels or the pin hash.
    pin = InventoryPin.model_validate(pin.model_dump(mode="json"))
    if pin.identity != expected_pin_sha256:
        raise ValueError("host inventory pin differs from predeclared run identity")
    if pin.source_commit != source_commit:
        raise ValueError("host inventory source commit differs from run identity")
    return annotated_pair_catalog(attack, benign, pin.annotations)
