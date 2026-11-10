"""make clean-logs: delete log groups created outside CloudFormation (NF-4). Best effort."""

import boto3

PREFIXES = ['/aws/bedrock-agentcore/', '/aws/lambda/WhiskeyAgentStack-', '/aws/vendedlogs/bedrock']


def main() -> None:
    logs = boto3.client('logs')
    n = 0
    for prefix in PREFIXES:
        for page in logs.get_paginator('describe_log_groups').paginate(logGroupNamePrefix=prefix):
            for g in page.get('logGroups', []):
                name = g['logGroupName']
                if prefix == '/aws/bedrock-agentcore/' and 'whiskey' not in name:
                    continue
                try:
                    logs.delete_log_group(logGroupName=name)
                    print(f'deleted {name}')
                    n += 1
                except Exception as e:  # noqa: BLE001
                    print(f'skip {name}: {e}')
    print(f'done, {n} log groups deleted')


if __name__ == '__main__':
    main()
