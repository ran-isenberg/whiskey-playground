# Getting Started

## Prerequisites

- An AWS account with **CDK bootstrapped** in `us-east-1` and credentials for it in your shell.
- **Bedrock model access** to `us.anthropic.claude-haiku-5-5` (inference profile) and `amazon.titan-embed-text-v2:0`.
- Python 3.14 and [uv](https://docs.astral.sh/uv/), Node.js (CDK CLI and UI), the AWS CLI and `jq`.

## Deploy

```bash
make dev       # uv sync, pre-commit hooks, npm ci for the UI
make deploy    # build agent + chat Lambda (ARM64 wheels) + UI, cdk deploy, then kb-sync
```

To see traces in CloudWatch GenAI Observability, run `make observability` once per account and region (it turns on CloudWatch Transaction Search, an account-wide setting outside the stack). It takes about 10 minutes to go from `PENDING` to `ACTIVE`, and the stack's trace delivery can't be created before that, so `make deploy` checks first and stops with a message if it isn't active yet.

`make deploy` writes the stack outputs to `cdk-outputs.json`: `UiUrl` (the CloudFront site), `ApiUrl`, `AgentRuntimeArn`, `KnowledgeBaseId` and more.

## Chat with it

| How | Command | Notes |
| --- | --- | --- |
| Deployed site | open `UiUrl` from `cdk-outputs.json` | Works on desktop and phone |
| Local UI, live API | `make ui-dev` → <http://localhost:5173> | Hot reload against the deployed API |
| Local UI, no backend | `make ui-fixtures` | Canned answers; try "vodka", "error", "slow" |
| Terminal | `make chat` | Talks to the runtime directly; `/new` starts a new session. Also the demo fallback. |

Try the demo script: a chip prompt → 3 cards; *"something cheaper"* → re-ranked; *"what's the capital of France?"* → polite steer.

## Change things

| To change | Edit | Then |
| --- | --- | --- |
| Persona, safety, routing | `agent/prompts/base.md` | `make deploy-agent` |
| Rubric, `why` rules, search behavior | `agent/recommend/prompt.md` | `make deploy-agent` |
| Model, N, threshold, retrieval size | `cdk/whiskey/constants.py` (runtime env vars) | `make deploy-agent` |
| Inventory | `kb/<id>.md` | `make kb-sync` (no redeploy) |
| UI look | `ui/tailwind.config.ts` (theme tokens), `ui/src/components/` | `make ui-dev`, then `make deploy` |

## All commands

| Target | Does |
| --- | --- |
| `make dev` | Install Python and UI dependencies, pre-commit hooks |
| `make deploy` | Build everything, `cdk deploy`, `kb-sync` |
| `make deploy-agent` | Rebuild the agent and chat Lambda, `cdk deploy` (≈ 3 min) |
| `make kb-sync` | Sidecars + `inventory.json` + upload + ingestion |
| `make chat` | Terminal chat against the runtime |
| `make ui-dev` / `make ui-fixtures` | Local UI against the API / against fixtures |
| `make test` | Unit tests (no AWS) |
| `make e2e` | deepeval golden set against the deployed API |
| `make observability` | One-time: enable CloudWatch Transaction Search (AgentCore Observability) |
| `make format` / `make format-fix` / `make lint` | ruff check --fix / ruff format / both |
| `make pre-commit` | Run all pre-commit hooks |
| `make destroy` | `cdk destroy`, then delete leftover log groups |

## Tear down

```bash
make destroy
```

Every resource uses `RemovalPolicy.DESTROY` and buckets auto-empty; `make clean-logs` (run by destroy) removes the log groups AgentCore and Bedrock create outside CloudFormation.
