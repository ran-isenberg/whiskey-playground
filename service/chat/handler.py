"""Chat Lambda: POST /chat → InvokeAgentRuntime (design §6)."""

import json
import os

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig, Response, content_types
from aws_lambda_powertools.logging import correlation_paths
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError
from pydantic import ValidationError

from models import ChatRequest, ErrorBody, ErrorDetail

logger = Logger(service='whiskey-chat')

RUNTIME_ARN = os.environ.get('AGENT_RUNTIME_ARN', '')
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', 'http://localhost:5173')

STATUS = {'INVALID_REQUEST': 400, 'THROTTLED': 429, 'TIMEOUT': 504, 'AGENT_ERROR': 500}
FRIENDLY = {
    'THROTTLED': 'The bar is busy, try again in a moment.',
    'TIMEOUT': 'The sommelier is taking too long. Try again.',
    'AGENT_ERROR': 'Something spilled. Try again.',
}
THROTTLE_CODES = {'ThrottlingException', 'TooManyRequestsException', 'ServiceQuotaExceededException'}

cors = CORSConfig(allow_origin=ALLOWED_ORIGIN, extra_origins=['http://localhost:5173'], max_age=300)
app = APIGatewayRestResolver(cors=cors)

_client = None


def client():
    global _client
    if _client is None:
        _client = boto3.client(
            'bedrock-agentcore',
            config=Config(read_timeout=27, connect_timeout=3, retries={'max_attempts': 1, 'mode': 'standard'}),
        )
    return _client


def error(code: str, message: str | None = None) -> Response:
    body = ErrorBody(error=ErrorDetail(code=code, message=message or FRIENDLY[code]))
    return Response(status_code=STATUS[code], content_type=content_types.APPLICATION_JSON, body=body.model_dump_json())


def ok(body: dict) -> Response:
    return Response(status_code=200, content_type=content_types.APPLICATION_JSON, body=json.dumps(body))


def invoke_agent(payload: dict, session_id: str) -> dict:
    resp = client().invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        qualifier='DEFAULT',
        contentType='application/json',
        accept='application/json',
        payload=json.dumps(payload).encode(),
    )
    raw = resp['response']
    data = raw.read() if hasattr(raw, 'read') else raw
    if isinstance(data, (bytes, bytearray)):
        data = data.decode()
    return json.loads(data) if isinstance(data, str) else data


@app.post('/chat')
def chat() -> Response:
    try:
        req = ChatRequest.model_validate(app.current_event.json_body or {})
    except (ValidationError, json.JSONDecodeError, TypeError) as e:
        msg = 'Please send a message between 1 and 500 characters.'
        if isinstance(e, ValidationError) and any('session_id' in map(str, err['loc']) for err in e.errors()):
            msg = 'Invalid session. Start a new conversation.'
        return error('INVALID_REQUEST', msg)

    logger.append_keys(session_id=req.session_id)
    logger.set_correlation_id(req.session_id)  # design §11: correlation_id = session_id
    payload = {'warmup': True} if req.warmup else {'message': req.message}
    try:
        body = invoke_agent(payload, req.session_id)
    except ReadTimeoutError, ConnectTimeoutError:
        logger.warning('agent timeout')
        return error('TIMEOUT')
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '')
        logger.exception('agent client error', extra={'aws_code': code})
        return error('THROTTLED' if code in THROTTLE_CODES else 'AGENT_ERROR')
    except Exception:
        logger.exception('agent invoke failed')
        return error('AGENT_ERROR')

    if isinstance(body, dict) and 'error' in body:
        code = body['error'].get('code', 'AGENT_ERROR')
        code = code if code in STATUS else 'AGENT_ERROR'
        logger.warning('agent returned error', extra={'agent_error': body['error']})
        return error(code, body['error'].get('message') if code == 'INVALID_REQUEST' else None)
    return ok(body)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event, context):
    return app.resolve(event, context)
