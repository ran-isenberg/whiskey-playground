import json
import os
import time
import uuid
from pathlib import Path

import pytest
import requests
import yaml

os.environ.setdefault('DEEPEVAL_TELEMETRY_OPT_OUT', 'YES')

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = yaml.safe_load((Path(__file__).parent / 'golden.yaml').read_text())['prompts']


def api_url() -> str:
    if url := os.environ.get('API_URL'):
        return url
    return json.loads((ROOT / 'cdk-outputs.json').read_text())['WhiskeyAgentStack']['ApiUrl']


def chat(url: str, sid: str, message: str) -> dict:
    for attempt in range(3):
        r = requests.post(url, json={'session_id': sid, 'message': message}, timeout=35)
        if r.status_code == 429 and attempt < 2:
            time.sleep(2)
            continue
        assert r.status_code == 200, f'HTTP {r.status_code}: {r.text}'
        return r.json()
    raise AssertionError('throttled')


def render(body: dict) -> str:
    """Flatten a ChatResponse into the text an LLM judge reads."""
    lines = [body['message']]
    for m in body['matches']:
        w = m['whiskey']
        lines += [
            '',
            f'#{m["rank"]} {w["name"]} ({w["type"]}, {w["region"]}, {w["country"]}, {w["price_tier"]}) — {m["match_score"]}% match',
            f'Flavor profile: {", ".join(w["flavor_profile"])}',
            f'WHY: {m["why"]}',
            f'SERVE: {m["serving"]}',
        ]
    if not body['matches']:
        lines.append('(no bottles recommended)')
    return '\n'.join(lines)


@pytest.fixture(scope='session')
def runs() -> dict[int, dict]:
    """Call the deployed /chat once per golden prompt (multi-turn prompts share a session)."""
    url = api_url()
    out = {}
    for p in GOLDEN:
        sid = str(uuid.uuid4())
        t0 = time.monotonic()
        bodies = [chat(url, sid, turn) for turn in p['turns']]
        out[p['n']] = {**p, 'bodies': bodies, 'secs': round(time.monotonic() - t0, 1)}
    return out


@pytest.fixture(scope='session')
def judge_model():
    from metrics import judge

    return judge()
