"""make observability: enable CloudWatch Transaction Search (one-time, account + region wide).

`--check` (run by make deploy / deploy-agent) exits non-zero unless Transaction Search is ACTIVE: the
stack's runtime trace delivery (AWS::Logs::Delivery to X-Ray) fails to create until it is.

AgentCore Observability needs X-Ray spans delivered to CloudWatch Logs. This is an account-level setting,
so it lives outside the CDK stack (destroying the stack must not change it). Idempotent.
"""

import json
import sys

import boto3

POLICY_NAME = 'TransactionSearchXRayAccess'
SAMPLING_PERCENT = 1  # X-Ray indexing rule; spans are still ingested, this only controls indexing


def check() -> None:
    dest = boto3.client('xray').get_trace_segment_destination()
    if dest.get('Destination') == 'CloudWatchLogs' and dest.get('Status') == 'ACTIVE':
        print('Transaction Search: ACTIVE')
        return
    print(
        f'Transaction Search is not active (destination={dest.get("Destination")}, status={dest.get("Status")}).\n'
        'Run `make observability` once, wait until it reports ACTIVE (about 10 minutes), then deploy again.',
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    session = boto3.session.Session()
    region = session.region_name or 'us-east-1'
    account = session.client('sts').get_caller_identity()['Account']
    logs = session.client('logs', region_name=region)
    xray = session.client('xray', region_name=region)

    policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'TransactionSearchXRayAccess',
                'Effect': 'Allow',
                'Principal': {'Service': 'xray.amazonaws.com'},
                'Action': 'logs:PutLogEvents',
                'Resource': [
                    f'arn:aws:logs:{region}:{account}:log-group:aws/spans:*',
                    f'arn:aws:logs:{region}:{account}:log-group:/aws/application-signals/data:*',
                ],
                'Condition': {
                    'ArnLike': {'aws:SourceArn': f'arn:aws:xray:{region}:{account}:*'},
                    'StringEquals': {'aws:SourceAccount': account},
                },
            }
        ],
    }
    logs.put_resource_policy(policyName=POLICY_NAME, policyDocument=json.dumps(policy))
    print(f'logs resource policy {POLICY_NAME} set')

    current = xray.get_trace_segment_destination()
    if current.get('Destination') != 'CloudWatchLogs':
        xray.update_trace_segment_destination(Destination='CloudWatchLogs')
        print('trace segment destination -> CloudWatchLogs')
    else:
        print(f'trace segment destination already CloudWatchLogs ({current.get("Status")})')

    xray.update_indexing_rule(Name='Default', Rule={'Probabilistic': {'DesiredSamplingPercentage': SAMPLING_PERCENT}})
    print(f'indexing rule Default -> {SAMPLING_PERCENT}%')
    dest = xray.get_trace_segment_destination()
    print(f'Transaction Search: destination={dest["Destination"]} status={dest["Status"]} (PENDING turns ACTIVE in ~10 min)')


if __name__ == '__main__':
    check() if '--check' in sys.argv else main()
