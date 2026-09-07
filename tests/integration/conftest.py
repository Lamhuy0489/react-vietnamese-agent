"""Construction QA is not a development suite once its Test scenarios are sealed."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORING_MODULES = {
    "test_adversarial_workbench.py",
    "test_canonical_candidates.py",
    "test_candidate_review.py",
    "test_canonical_revision.py",
    "test_mechanism_batch.py",
    "test_linked_scope.py",
    "test_transaction_batch.py",
    "test_flow_batch.py",
    "test_canonical_admission.py",
    "test_disclosure_batch.py",
    "test_completion_batch.py",
    "test_boundary_batch.py",
    "test_canonical_selection.py",
    "test_mechanical_variants.py",
    "test_linguistic_variants.py",
    "test_adversarial_release_v2.py",
}


def pytest_ignore_collect(collection_path: Path) -> bool | None:
    # Before import: some historical tests load construction payloads at module scope.
    # These files remain immutable evidence; new development uses Dev-only fixtures.
    if (
        ROOT / "data/adversarial/release_v2/seal.json"
    ).exists() and collection_path.name in AUTHORING_MODULES:
        return True
    return None
