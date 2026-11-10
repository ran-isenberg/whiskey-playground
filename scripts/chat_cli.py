"""make chat: REPL that calls the AgentCore runtime directly (demo fallback). /new starts a new session."""

import json
import uuid
from pathlib import Path

import boto3
from botocore.config import Config
from rich.console import Console
from rich.panel import Panel

ROOT = Path(__file__).resolve().parent.parent
console = Console()


def runtime_arn() -> str:
    outputs = ROOT / 'cdk-outputs.json'
    if outputs.exists():
        return json.loads(outputs.read_text())['WhiskeyAgentStack']['AgentRuntimeArn']
    cfn = boto3.client('cloudformation')
    outs = cfn.describe_stacks(StackName='WhiskeyAgentStack')['Stacks'][0]['Outputs']
    return next(o['OutputValue'] for o in outs if o['OutputKey'] == 'AgentRuntimeArn')


def invoke(client, arn: str, sid: str, payload: dict) -> dict:
    resp = client.invoke_agent_runtime(agentRuntimeArn=arn, runtimeSessionId=sid, qualifier='DEFAULT', payload=json.dumps(payload).encode())
    return json.loads(resp['response'].read())


def render(body: dict) -> None:
    if 'error' in body:
        console.print(f'[red]{body["error"]["code"]}[/red]: {body["error"]["message"]}')
        return
    console.print(f'\n[bold yellow]🥃 {body["message"]}[/bold yellow]\n')
    for m in body.get('matches', []):
        w = m['whiskey']
        age = f'{w["age"]} yrs' if w['age'] else 'NAS'
        console.print(
            Panel(
                f'[dim]{w["distillery"]} · {w["region"]}, {w["country"]} · {age} · {w["abv"]}% · {w["price_tier"]}[/dim]\n\n'
                f'[bold]Why:[/bold] {m["why"]}\n[bold]Serve:[/bold] {m["serving"]}',
                title=f'#{m["rank"]} {w["name"]}  [yellow]{m["match_score"]}%[/yellow]  ({m["id"]})',
                title_align='left',
            )
        )


def main() -> None:
    arn = runtime_arn()
    client = boto3.client('bedrock-agentcore', config=Config(read_timeout=60, retries={'max_attempts': 1}))
    sid = str(uuid.uuid4())
    console.print(f'[dim]session {sid} — /new for a new conversation, /quit to exit[/dim]')
    invoke(client, arn, sid, {'warmup': True})
    while True:
        try:
            msg = console.input('[bold cyan]you> [/bold cyan]').strip()
        except EOFError, KeyboardInterrupt:
            break
        if not msg:
            continue
        if msg == '/quit':
            break
        if msg == '/new':
            sid = str(uuid.uuid4())
            console.print(f'[dim]new session {sid}[/dim]')
            continue
        with console.status('checking the cellar…'):
            body = invoke(client, arn, sid, {'message': msg})
        render(body)


if __name__ == '__main__':
    main()
