"""Builds the one agent from its modes (AG-15, D12) and runs a turn (design §4.3).

Recommend mode lives in recommend/. Order mode (MVP 2) will live in order/ and plug in
through `_order_mode()` without changing the ChatResponse contract.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from strands import Agent
from strands.models import BedrockModel
from strands.types.exceptions import StructuredOutputException

from answer import AgentAnswer
from config import Settings
from contract import ChatResponse
from recommend.check_and_fill import check_and_fill
from recommend.tools import make_search_tool
from session import SessionState

log = logging.getLogger(__name__)
HERE = Path(__file__).parent


class AgentError(Exception):
    pass


def _read(rel: str) -> str:
    return (HERE / rel).read_text(encoding='utf-8')


def _order_mode(settings: Settings, state: SessionState) -> tuple[str, str, list, list]:
    """(routing line, prompt, tools, hooks) for order mode. Empty until MVP 2."""
    return '', '', [], []


def build_system_prompt(settings: Settings, order_routing: str = '', order_prompt: str = '') -> str:
    base = _read('prompts/base.md').replace('{order_mode_routing}', order_routing)
    rec = _read('recommend/prompt.md').replace('{max_matches}', str(settings.max_matches)).replace('{threshold}', str(settings.score_threshold))
    return '\n\n'.join(p for p in (base, rec, order_prompt) if p)


def build_agent(settings: Settings, state: SessionState) -> Agent:
    def on_results(query: str, max_price_level: int | None, ids: list[str]) -> None:
        state.retrieved_ids.extend(i for i in ids if i not in state.retrieved_ids)
        state.tool_calls.append({'tool': 'search_inventory', 'query': query, 'max_price_level': max_price_level, 'ids': ids})

    tools = [make_search_tool(settings.kb_id, settings.retrieve_k, settings.aws_region, on_results)]
    routing, order_prompt, order_tools, hooks = _order_mode(settings, state)
    model_config = {'model_id': settings.model_id}
    if settings.temperature is not None:
        model_config['temperature'] = settings.temperature
    model = BedrockModel(region_name=settings.aws_region, **model_config)
    return Agent(
        model=model,
        system_prompt=build_system_prompt(settings, routing, order_prompt),
        tools=tools + order_tools,
        hooks=hooks or None,
        callback_handler=None,
    )


def ensure_agent(settings: Settings, state: SessionState) -> Agent:
    """Build the session's agent once. Callers hold state.lock."""
    if state.agent is None:
        state.agent = build_agent(settings, state)
    return state.agent


def _ask(agent: Agent, message: str) -> AgentAnswer:
    try:
        result = agent(message, structured_output_model=AgentAnswer)
    except StructuredOutputException:
        log.warning('structured output failed, retrying once')
        try:
            result = agent('Return the answer in the required format.', structured_output_model=AgentAnswer)
        except StructuredOutputException as e:
            raise AgentError('structured output failed twice') from e
    out = result.structured_output
    if not isinstance(out, AgentAnswer):
        raise AgentError('no structured output')
    return out


def turn(settings: Settings, state: SessionState, message: str) -> ChatResponse:
    t0 = time.monotonic()
    with state.lock:
        state.reset_turn()
        ensure_agent(settings, state)
        # Strands keeps a failed turn's user message / tool calls in history, which would break every later
        # turn in this session (and the UI Retry). Roll the conversation back so a failed turn leaves no trace.
        snapshot = list(state.agent.messages)
        try:
            answer = _ask(state.agent, message)
        except BaseException:
            state.agent.messages[:] = snapshot
            raise
        response, dropped = check_and_fill(
            answer,
            state.inventory,
            state.session_id,
            threshold=settings.score_threshold,
            max_matches=settings.max_matches,
        )
        log.info(
            json.dumps(
                {
                    'event': 'turn',
                    'session_id': state.session_id,
                    'input': message,
                    'retrieved_ids': state.retrieved_ids,
                    'picks_raw': [p.model_dump(include={'id', 'match_score'}) for p in answer.picks],
                    'dropped': dropped,
                    'tool_calls': state.tool_calls,
                    'match_ids': [m.id for m in response.matches],
                    'pending_order': None,
                    'order_id': None,
                    'latency_ms': int((time.monotonic() - t0) * 1000),
                }
            )
        )
        return response
