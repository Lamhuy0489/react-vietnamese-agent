"""Phase 2 clean-pool acceptance test."""

from react_agent.validation import validate_clean_pool


def test_clean_pool_passes_all_pre_split_checks() -> None:
    result = validate_clean_pool()
    assert result["valid"], result["failures"][:10]
    assert result["schema_valid"] == 250
    assert result["oracle_valid"] == 250
    assert result["review_coverage"] == 250
