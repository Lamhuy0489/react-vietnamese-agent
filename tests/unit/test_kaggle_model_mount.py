"""Native startup regression: exact Kaggle model versions in both mount layouts."""

from pathlib import Path

import pytest

from react_agent.serving.structured_api_v1 import ServiceError, resolve_model_mount

SOURCES = (
    "metaresearch/llama-3.2/transformers/3b-instruct/1",
    "qwen-lm/qwen-3/transformers/8b/1",
)


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("namespaced", [True, False])
def test_exact_version_layout(tmp_path: Path, source: str, namespaced: bool) -> None:
    relative = "models/" + source if namespaced else source.split("/", 1)[1]
    target = tmp_path / relative
    target.mkdir(parents=True)
    assert resolve_model_mount(source, tmp_path) == target


def test_other_version_is_not_a_fallback(tmp_path: Path) -> None:
    (tmp_path / "llama-3.2/transformers/3b-instruct/2").mkdir(parents=True)
    with pytest.raises(ServiceError, match="EXACT_MODEL_MOUNT_MISSING"):
        resolve_model_mount(SOURCES[0], tmp_path)


def test_ambiguous_layouts_fail_closed(tmp_path: Path) -> None:
    for relative in ("models/" + SOURCES[0], SOURCES[0].split("/", 1)[1]):
        (tmp_path / relative).mkdir(parents=True)
    with pytest.raises(ServiceError, match="AMBIGUOUS_MODEL_MOUNT"):
        resolve_model_mount(SOURCES[0], tmp_path)


def test_parent_symlink_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    (outside / SOURCES[0]).mkdir(parents=True)
    (tmp_path / "models").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ServiceError, match="INVALID_MODEL_MOUNT_LINK"):
        resolve_model_mount(SOURCES[0], tmp_path)


@pytest.mark.parametrize("source", [
    "../llama-3.2/transformers/3b-instruct/1", SOURCES[0] + "/extra",
    "metaresearch/../transformers/3b-instruct/1", "/" + SOURCES[0],
    "metaresearch/llama-3.2/transformers/3b-instruct/latest",
])
def test_invalid_handle_rejected(tmp_path: Path, source: str) -> None:
    with pytest.raises(ServiceError, match="INVALID_MODEL_SOURCE"):
        resolve_model_mount(source, tmp_path)
