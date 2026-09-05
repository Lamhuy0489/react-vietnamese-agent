from pathlib import Path

import pytest

from react_agent.tools.factory import build_smoke_registry
from react_agent.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "smoke"


@pytest.fixture
def registry() -> ToolRegistry:
    return build_smoke_registry(DATA_ROOT)
