"""REST API + chat Lambda (design §6)."""

import json

from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct

from cdk.whiskey.constants import BUILD_CHAT_DIR

LOCAL_ORIGIN = 'http://localhost:5173'


class ChatApi(Construct):
    def __init__(self, scope: Construct, id: str, *, runtime: agentcore.Runtime, ui_origin: str) -> None:
        super().__init__(scope, id)

        log_group = logs.LogGroup(self, 'ChatLogs', retention=logs.RetentionDays.ONE_WEEK, removal_policy=RemovalPolicy.DESTROY)
        self.fn = lambda_.Function(
            self,
            'ChatFn',
            runtime=lambda_.Runtime.PYTHON_3_14,
            architecture=lambda_.Architecture.ARM_64,
            handler='handler.handler',
            code=lambda_.Code.from_asset(BUILD_CHAT_DIR),
            memory_size=512,
            timeout=Duration.seconds(28),  # API-5: below API Gateway's 29 s integration timeout
            log_group=log_group,
            environment={
                'AGENT_RUNTIME_ARN': runtime.agent_runtime_arn,
                'ALLOWED_ORIGIN': ui_origin,
                'POWERTOOLS_SERVICE_NAME': 'whiskey-chat',
                'POWERTOOLS_LOG_LEVEL': 'INFO',
            },
        )
        runtime.grant_invoke_runtime(self.fn)

        self.api = apigw.RestApi(
            self,
            'Api',
            rest_api_name='whiskey-chat',
            deploy_options=apigw.StageOptions(stage_name='prod', throttling_rate_limit=5, throttling_burst_limit=10),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=[ui_origin, LOCAL_ORIGIN],
                allow_methods=['POST', 'OPTIONS'],
                allow_headers=['Content-Type'],
                max_age=Duration.minutes(5),
            ),
        )
        self.api.root.add_resource('chat').add_method('POST', apigw.LambdaIntegration(self.fn))

        # Errors API Gateway produces itself (stage throttling, integration timeout, unknown routes) must follow
        # the error contract (requirements §4.5) and carry CORS headers, or the browser reports a CORS failure
        # and the UI cannot tell "busy" from "broken".
        cors = {'Access-Control-Allow-Origin': "'*'", 'Access-Control-Allow-Headers': "'Content-Type'"}
        for rid, rtype, status, code, msg in [
            ('Throttled', apigw.ResponseType.THROTTLED, '429', 'THROTTLED', 'The bar is busy, try again in a moment.'),
            ('Timeout', apigw.ResponseType.INTEGRATION_TIMEOUT, '504', 'TIMEOUT', 'The sommelier is taking too long. Try again.'),
            ('Default4xx', apigw.ResponseType.DEFAULT_4_XX, None, 'INVALID_REQUEST', 'Please send a message between 1 and 500 characters.'),
            ('Default5xx', apigw.ResponseType.DEFAULT_5_XX, None, 'AGENT_ERROR', 'Something spilled. Try again.'),
        ]:
            self.api.add_gateway_response(
                rid,
                type=rtype,
                status_code=status,
                response_headers=cors,
                templates={'application/json': json.dumps({'error': {'code': code, 'message': msg}})},
            )

    @property
    def chat_url(self) -> str:
        return f'{self.api.url}chat'
