"""Model identity and template compatibility are experimental integrity gates."""

from pathlib import Path

import pytest

from react_agent.llm.pilot_profiles import PROFILES, adapt_messages, find_pilot_model


def test_gemma_preserves_a0_content_and_correction_without_mutating_input() -> None:
    messages = [
        {"role": "system", "content": "A0\nTools"},
        {"role": "user", "content": "Task"},
        {"role": "assistant", "content": "Action"},
        {"role": "user", "content": "OBSERVATION"},
        {"role": "user", "content": "Schema correction"},
    ]
    adapted = adapt_messages(messages, PROFILES["gemma"].chat_adapter)
    assert adapted == [
        {"role": "user", "content": "A0\nTools\n\nTask"},
        {"role": "assistant", "content": "Action"},
        {"role": "user", "content": "OBSERVATION\n\nSchema correction"},
    ]
    assert messages[0]["role"] == "system"
    assert len(messages) == 5
    assert adapt_messages(messages, "native") == messages
    with pytest.raises(ValueError, match="unknown"):
        adapt_messages(messages, "unrecorded_adapter")


def test_pinned_model_mount_accepts_unsharded_and_rejects_wrong_version(tmp_path: Path) -> None:
    profile = PROFILES["gemma"]
    wrong = tmp_path / "google/gemma-2/transformers/gemma-2-2b-it/1"
    wrong.mkdir(parents=True)
    (wrong / "config.json").write_text("{}")
    with pytest.raises(ValueError, match="pinned"):
        find_pilot_model(tmp_path, profile)
    right = wrong.with_name("2")
    right.mkdir()
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors"):
        (right / name).write_text("{}")
    assert find_pilot_model(tmp_path, profile) == right
    assert PROFILES["llama"].model_id == "metaresearch/llama-3.2"
    assert PROFILES["llama"].revision == "transformers/3b-instruct/1"
