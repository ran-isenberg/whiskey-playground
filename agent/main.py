"""AgentCore Runtime entrypoint."""

import logging
import os
import sys

# Make sibling modules importable regardless of the runtime's working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bedrock_agentcore.runtime import BedrockAgentCoreApp  # noqa: E402
from strands.types.exceptions import ModelThrottledException  # noqa: E402

import sommelier  # noqa: E402
from config import get_settings  # noqa: E402
from inventory import load_inventory  # noqa: E402
from session import SessionRegistry, SessionState  # noqa: E402

settings = get_settings()
logging.basicConfig(level=settings.log_level, format='%(levelname)s %(name)s %(message)s', force=True)
log = logging.getLogger('whiskey')


def _new_session(session_id: str) -> SessionState:
    # KB-6: reload inventory.json at each new session so `make kb-sync` needs no redeploy.
    return SessionState(session_id=session_id, inventory=load_inventory(settings.data_bucket, settings.inventory_key))


sessions = SessionRegistry(_new_session)
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict, context) -> dict:
    sid = getattr(context, 'session_id', None) or payload.get('session_id') or 'local-session'
    try:
        state = sessions.get_or_create(sid)
        if payload.get('warmup'):
            with state.lock:  # a real message may arrive while the warm-up is still building the agent
                sommelier.ensure_agent(settings, state)
            return {'ok': True}
        message = str(payload.get('message', '')).strip()
        if not message or len(message) > 500:
            return {'error': {'code': 'INVALID_REQUEST', 'message': 'Message must be 1–500 characters.'}}
        return sommelier.turn(settings, state, message).model_dump()
    except ModelThrottledException:
        log.warning('model throttled')
        return {'error': {'code': 'THROTTLED', 'message': 'The bar is busy, try again in a moment.'}}
    except Exception:
        log.exception('turn failed')
        return {'error': {'code': 'AGENT_ERROR', 'message': 'Something spilled. Try again.'}}


if __name__ == '__main__':
    app.run()
