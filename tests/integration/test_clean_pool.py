"""Phase 2 clean-pool acceptance test."""

from react_agent.validation import validate_clean_pool


def test_archived_v1_pool_is_rejected_for_misgrouped_instances() -> None:
    result = validate_clean_pool()
    # This frozen historical artifact is intentionally not repaired in place.
    # A passing regression test means the validator rejects it, not acceptance.
    assert not result["valid"]
    assert len(result["misgrouped_instances"]) == 30
    assert ["clean_0001", "clean_0196"] in result["misgrouped_instances"]
    assert result["schema_valid"] == 250
    assert result["oracle_valid"] == 250
