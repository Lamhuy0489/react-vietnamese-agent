from __future__ import annotations

import json
from pathlib import Path

import pytest

from react_agent.evaluation import final_config_v1 as freeze


def _tree(root: Path) -> None:
    for name in (*freeze.FROZEN_FILES, "src/react_agent/a.py", "configs/x.yaml"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(name)


def test_verify_accepts_the_frozen_tree_and_names_any_change(tmp_path: Path) -> None:
    _tree(tmp_path)
    with pytest.raises(freeze.FrozenConfigError, match="missing"):
        freeze.verify(tmp_path)
    manifest = freeze.build(tmp_path, {"a6": "v3"})
    (tmp_path / freeze.MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / freeze.MANIFEST).write_text(json.dumps(manifest))
    assert freeze.verify(tmp_path)["decisions"] == {"a6": "v3"}
    (tmp_path / "src/react_agent/__pycache__").mkdir()
    (tmp_path / "src/react_agent/__pycache__/a.pyc").write_text("cache")
    assert freeze.verify(tmp_path)
    (tmp_path / "configs/x.yaml").write_text("tuned")
    (tmp_path / "src/react_agent/new.py").write_text("added")
    with pytest.raises(freeze.FrozenConfigError, match="configs/x.yaml, src/react_agent/new.py"):
        freeze.verify(tmp_path)
