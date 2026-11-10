"""Runs the chat Lambda handler end to end (Powertools decorators included) with the agent call stubbed."""

import json
import sys
from pathlib import Path

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'service' / 'chat'))
import handler  # noqa: E402

SID = '3f6c1d2e-8a4b-4c1e-9f7a-2b5d8e0c4a91'


class Ctx:
    function_name = 'chat'
    memory_limit_in_mb = 512
    invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:chat'
    aws_request_id = 'req-1'


def event(body) -> dict:
    return {
        'resource': '/chat',
        'path': '/chat',
        'httpMethod': 'POST',
        'headers': {'Content-Type': 'application/json', 'X-Amzn-Trace-Id': 'Root=1-abc'},
        'multiValueHeaders': {},
        'queryStringParameters': None,
        'pathParameters': None,
        'stageVariables': None,
        'isBase64Encoded': False,
        'requestContext': {'requestId': 'req-1', 'resourcePath': '/chat', 'httpMethod': 'POST', 'stage': 'prod'},
        'body': json.dumps(body) if not isinstance(body, str) else body,
    }


def call(body):
    r = handler.handler(event(body), Ctx())
    return r['statusCode'], json.loads(r['body'])


def test_ok(monkeypatch):
    reply = {'session_id': SID, 'message': 'Here you go.', 'matches': [], 'pending_order': None, 'order': None}
    monkeypatch.setattr(handler, 'invoke_agent', lambda payload, sid: reply)
    assert call({'session_id': SID, 'message': 'rainy'}) == (200, reply)


def test_warmup(monkeypatch):
    seen = {}
    monkeypatch.setattr(handler, 'invoke_agent', lambda payload, sid: seen.setdefault('p', payload) and {'ok': True})
    assert call({'session_id': SID, 'warmup': True}) == (200, {'ok': True})
    assert seen['p'] == {'warmup': True}


@pytest.mark.parametrize('body', [{'session_id': SID, 'message': ''}, {'session_id': 'nope', 'message': 'hi'}, 'not json'])
def test_invalid(body):
    status, b = call(body)
    assert status == 400 and b['error']['code'] == 'INVALID_REQUEST'


def _raise(exc):
    def f(payload, sid):
        raise exc

    return f


@pytest.mark.parametrize(
    'exc,status,code',
    [
        (ReadTimeoutError(endpoint_url='x'), 504, 'TIMEOUT'),
        (ClientError({'Error': {'Code': 'ThrottlingException'}}, 'InvokeAgentRuntime'), 429, 'THROTTLED'),
        (RuntimeError('boom'), 500, 'AGENT_ERROR'),
    ],
)
def test_error_mapping(monkeypatch, exc, status, code):
    monkeypatch.setattr(handler, 'invoke_agent', _raise(exc))
    s, b = call({'session_id': SID, 'message': 'hi'})
    assert (s, b['error']['code']) == (status, code)


def test_agent_error_payload(monkeypatch):
    monkeypatch.setattr(handler, 'invoke_agent', lambda p, s: {'error': {'code': 'AGENT_ERROR', 'message': 'internal detail'}})
    s, b = call({'session_id': SID, 'message': 'hi'})
    assert s == 500 and b['error']['message'] == 'Something spilled. Try again.'
