"""Frozen clean Dev/Test split acceptance test."""

from react_agent.validation import validate_clean_split


def test_archived_v1_split_is_hash_valid_but_semantically_invalid() -> None:
    result = validate_clean_split()
    assert not result["valid"]
    assert result["failures"] == ["semantic instance overlap between Dev/Test: 12"]
    assert result["dev_tasks"] == 150
    assert result["test_tasks"] == 100
    assert result["group_overlap"] == 0
    assert result["semantic_overlap"] == 12
