"""A failed turn must not leave messages in the session history (UI Retry reuses the session)."""

import pytest

import sommelier
from answer import AgentAnswer
from config import Settings
from session import SessionState


class FakeAgent:
    def __init__(self, fail: bool):
        self.messages = [{'role': 'user', 'content': [{'text': 'earlier'}]}, {'role': 'assistant', 'content': [{'text': 'ok'}]}]
        self.fail = fail

    def __call__(self, message, structured_output_model=None):
        self.messages.append({'role': 'user', 'content': [{'text': message}]})
        self.messages.append({'role': 'assistant', 'content': [{'toolUse': {'toolUseId': 't1', 'name': 'search_inventory', 'input': {}}}]})
        if self.fail:
            raise RuntimeError('model blew up mid-turn')

        class R:
            structured_output = AgentAnswer(message='Nothing fits, tell me a mood.', picks=[])

        return R()


def state_with(agent) -> SessionState:
    st = SessionState(session_id='3f6c1d2e-8a4b-4c1e-9f7a-2b5d8e0c4a91', inventory={})
    st.agent = agent
    return st


def test_failed_turn_rolls_back_history():
    st = state_with(FakeAgent(fail=True))
    before = list(st.agent.messages)
    with pytest.raises(RuntimeError):
        sommelier.turn(Settings(), st, 'rainy day')
    assert st.agent.messages == before


def test_successful_turn_keeps_history():
    st = state_with(FakeAgent(fail=False))
    resp = sommelier.turn(Settings(), st, 'rainy day')
    assert len(st.agent.messages) == 4 and resp.matches == []
