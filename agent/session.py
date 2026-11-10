"""Per-session state (AG-7, D4). One Strands agent per AgentCore Runtime session, kept in process memory."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from contract import Order, PendingOrder


@dataclass
class SessionState:
    session_id: str
    inventory: dict[str, dict]
    agent: Any = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    # Order mode (MVP 2) fields, kept here so both modes share one state object.
    pending_order: PendingOrder | None = None
    placed_order: Order | None = None
    # Per-turn scratch for the turn log.
    retrieved_ids: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)

    def reset_turn(self) -> None:
        self.retrieved_ids = []
        self.tool_calls = []
        self.placed_order = None


class SessionRegistry:
    def __init__(self, factory: Callable[[str], SessionState]):
        self._factory = factory
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> SessionState:
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                state = self._factory(session_id)
                self._sessions[session_id] = state
            return state
