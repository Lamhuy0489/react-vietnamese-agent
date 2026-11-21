from collections.abc import Iterator

import pytest

from react_agent.demo import session as session_module
from react_agent.prompts import a0_rebuild
from react_agent.security_v1 import a6_provenance_v3


@pytest.fixture(autouse=True)
def _restore_profiles() -> Iterator[None]:
    """DemoSession activates process-wide profiles; undo them after each test."""
    yield
    if session_module._ACTIVATED:
        a6_provenance_v3.deactivate()
        a0_rebuild.deactivate()
        session_module._ACTIVATED = False
