#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.whiskey.stack import WhiskeyAgentStack

app = cdk.App()
WhiskeyAgentStack(
    app,
    'WhiskeyAgentStack',
    env=cdk.Environment(account=os.environ.get('CDK_DEFAULT_ACCOUNT'), region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')),
)
app.synth()
