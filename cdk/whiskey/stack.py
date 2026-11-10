from aws_cdk import CfnOutput, Stack
from constructs import Construct

from cdk.whiskey.agent_construct import AgentRuntime
from cdk.whiskey.api_construct import ChatApi
from cdk.whiskey.kb_construct import KnowledgeBase
from cdk.whiskey.ui_construct import UiHosting


class WhiskeyAgentStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        kb = KnowledgeBase(self, 'Kb')
        agent = AgentRuntime(self, 'Agent', kb_id=kb.kb_id, kb_arn=kb.kb_arn, data_bucket=kb.data_bucket)
        ui = UiHosting(self, 'Ui')
        api = ChatApi(self, 'ChatApi', runtime=agent.runtime, ui_origin=ui.url)
        ui.deploy(api.chat_url)

        CfnOutput(self, 'DataBucketName', value=kb.data_bucket.bucket_name)
        CfnOutput(self, 'KnowledgeBaseId', value=kb.kb_id)
        CfnOutput(self, 'DataSourceId', value=kb.data_source.attr_data_source_id)
        CfnOutput(self, 'AgentRuntimeArn', value=agent.runtime.agent_runtime_arn)
        CfnOutput(self, 'ApiUrl', value=api.chat_url)
        CfnOutput(self, 'UiUrl', value=ui.url)
