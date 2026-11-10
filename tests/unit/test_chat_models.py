import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'service' / 'chat'))
from models import ChatRequest  # noqa: E402

SID = '3f6c1d2e-8a4b-4c1e-9f7a-2b5d8e0c4a91'


def test_valid():
    assert ChatRequest(session_id=SID, message='  rainy  ').message == 'rainy'


@pytest.mark.parametrize('msg', ['', '   ', 'x' * 501])
def test_bad_message(msg):
    with pytest.raises(ValidationError):
        ChatRequest(session_id=SID, message=msg)


def test_uuid1_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(session_id='6ba7b810-9dad-11d1-80b4-00c04fd430c8', message='hi')


def test_bad_session():
    with pytest.raises(ValidationError):
        ChatRequest(session_id='not-a-uuid-but-thirty-six-chars-long', message='hi')


def test_warmup_needs_no_message():
    assert ChatRequest(session_id=SID, warmup=True).warmup
