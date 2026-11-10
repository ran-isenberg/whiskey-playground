import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'agent'))

import kb_sync  # noqa: E402


@pytest.fixture(scope='session')
def inventory() -> dict:
    return kb_sync.build_all()
