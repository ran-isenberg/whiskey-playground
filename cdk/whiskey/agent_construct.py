"""AgentCore Runtime (direct code deploy) + role permissions (design §4.1, §8.1)."""

from aws_cdk import Aws
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdk.whiskey.constants import (
    AGENT_ENV_DEFAULTS,
    BUILD_AGENT_DIR,
    FALLBACK_FOUNDATION_MODEL,
    FALLBACK_MODEL_ID,
    FOUNDATION_MODEL,
    INVENTORY_KEY,
    MODEL_ID,
    PROFILE_REGIONS,
    RUNTIME_NAME,
)


def model_arns(profile_id: str, foundation: str) -> list[str]:
    return [f'arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:inference-profile/{profile_id}'] + [
        f'arn:aws:bedrock:{r}::foundation-model/{foundation}' for r in PROFILE_REGIONS
    ]


class AgentRuntime(Construct):
    def __init__(self, scope: Construct, id: str, *, kb_id: str, kb_arn: str, data_bucket: s3.IBucket) -> None:
        super().__init__(scope, id)

        env = {
            **AGENT_ENV_DEFAULTS,
            'MODEL_ID': MODEL_ID,
            'KB_ID': kb_id,
            'DATA_BUCKET': data_bucket.bucket_name,
            'INVENTORY_KEY': INVENTORY_KEY,
            'GATEWAY_URL': '',
            'AWS_REGION': Aws.REGION,
            'OBSERVABILITY_ENABLED': 'true',
        }

        self.runtime = agentcore.Runtime(
            self,
            'Runtime',
            runtime_name=RUNTIME_NAME,
            description='Whiskey sommelier agent (Strands)',
            agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_code_asset(
                path=BUILD_AGENT_DIR,
                runtime=agentcore.AgentCoreRuntime.PYTHON_3_14,
                entrypoint=['main.py'],
            ),
            environment_variables=env,
            tracing_enabled=True,  # AgentCore Observability: deliver runtime traces (needs Transaction Search)
        )

        role = self.runtime.role
        role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                resources=model_arns(MODEL_ID, FOUNDATION_MODEL) + model_arns(FALLBACK_MODEL_ID, FALLBACK_FOUNDATION_MODEL),
            )
        )
        role.add_to_principal_policy(iam.PolicyStatement(actions=['bedrock:Retrieve'], resources=[kb_arn]))
        role.add_to_principal_policy(iam.PolicyStatement(actions=['s3:GetObject'], resources=[data_bucket.arn_for_objects(INVENTORY_KEY)]))
