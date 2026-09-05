"""Frozen clean Dev/Test split acceptance test."""

from react_agent.validation import validate_clean_split


def test_clean_split_is_exact_disjoint_and_hash_valid() -> None:
    result = validate_clean_split()
    assert result["valid"], result["failures"][:10]
    assert result["dev_tasks"] == 150
    assert result["test_tasks"] == 100
    assert result["group_overlap"] == 0
    assert result["semantic_overlap"] == 0
