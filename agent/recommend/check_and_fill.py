"""AG-2, AG-5, AG-6: server-side checks on the LLM's picks and card filling from the inventory.

Pure functions, no AWS calls. The main target of the unit tests.
"""

from __future__ import annotations

import logging
import re

from answer import AgentAnswer, Pick
from contract import ChatResponse, Match, Whiskey

log = logging.getLogger(__name__)

ZERO_MATCH_FALLBACK = 'Nothing in our cellar fits that just right — try telling me a flavor or a mood.'
WHISKEY_FIELDS = list(Whiskey.model_fields)
# A message that promises bottles makes no sense when every pick was dropped.
PROMISE_RE = re.compile(r"\b(here (is|are)|try (the|these|this)|i'd pour|i would pour|pour you|my picks?|these)\b", re.I)


def check_picks(picks: list[Pick], inventory: dict[str, dict], *, threshold: int, max_matches: int) -> tuple[list[tuple[Pick, int]], list[dict]]:
    """Return (kept [(pick, clamped_score)] sorted and cut to N, dropped [{id, reason}])."""
    kept: list[tuple[Pick, int]] = []
    dropped: list[dict] = []
    seen: set[str] = set()
    for p in picks:
        wid = p.id.strip()
        rec = inventory.get(wid)
        score = max(0, min(100, int(p.match_score)))
        if rec is None:
            reason = 'unknown_id'
        elif not rec.get('in_stock'):
            reason = 'out_of_stock'
        elif wid in seen:
            reason = 'duplicate'
        elif score < threshold:
            reason = 'below_threshold'
        else:
            seen.add(wid)
            kept.append((p.model_copy(update={'id': wid}), score))
            continue
        dropped.append({'id': wid, 'reason': reason, 'score': score})
    kept.sort(key=lambda t: t[1], reverse=True)  # stable: ties keep model order
    for p, score in kept[max_matches:]:
        dropped.append({'id': p.id, 'reason': 'over_max', 'score': score})
    for d in dropped:
        log.info('dropped pick %s', d)
    return kept[:max_matches], dropped


def fill_card(rank: int, pick: Pick, score: int, rec: dict) -> Match:
    return Match(
        rank=rank,
        id=pick.id,
        match_score=score,
        why=pick.why.strip(),
        serving=pick.serving.strip(),
        whiskey=Whiskey(**{f: rec[f] for f in WHISKEY_FIELDS}),
    )


def check_and_fill(
    answer: AgentAnswer,
    inventory: dict[str, dict],
    session_id: str,
    *,
    threshold: int,
    max_matches: int,
) -> tuple[ChatResponse, list[dict]]:
    """Turn the LLM's AgentAnswer into a validated ChatResponse. Returns (response, dropped)."""
    kept, dropped = check_picks(answer.picks, inventory, threshold=threshold, max_matches=max_matches)
    matches = [fill_card(i + 1, p, s, inventory[p.id]) for i, (p, s) in enumerate(kept)]

    message = answer.message.strip()
    if not matches and answer.picks and (not message or PROMISE_RE.search(message)):
        message = ZERO_MATCH_FALLBACK
    if not message:
        message = ZERO_MATCH_FALLBACK

    resp = ChatResponse(session_id=session_id, message=message, matches=matches, pending_order=None, order=None)
    return ChatResponse.model_validate(resp.model_dump()), dropped
