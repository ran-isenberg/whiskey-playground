# Whiskey Sommelier Agent

Tell it a mood, a moment or a memory - *"rainy Sunday with a book, I love smoky stuff"* - and an AI sommelier picks bottles from **our own closed inventory**, ranks them with a **match %** and explains **why each one fits you**.

It is a hackathon proof of concept built to answer one question: **what does a small, demo-reliable AI agent look like on Amazon Bedrock AgentCore**, end to end, with infrastructure as code and real tests?

!!! info "Current stage: MVP 1 (recommend) is built"
    Free-text chat → ranked, explained recommendations from the inventory, multi-turn refinement, guard-railed off-topic and distress handling. **MVP 2 (ordering through AgentCore Gateway) is next.** See [MVP Status](mvp_status.md).

## What's inside

| Layer | Technology |
| --- | --- |
| Agent | [Strands Agents](https://strandsagents.com) on **Amazon Bedrock AgentCore Runtime** (direct code deploy, Python 3.14, ARM64) |
| Model | Claude Haiku 5.5 on Amazon Bedrock (US cross-region inference profile) |
| Retrieval | **Bedrock Knowledge Base** on **Amazon S3 Vectors** (Titan Text Embeddings v2), one chunk per bottle, metadata filters for stock and price |
| API | API Gateway REST + Python Lambda ([Powertools](https://docs.powertools.aws.dev/lambda/python/)), throttled, contract-validated with Pydantic |
| UI | React + Vite + Tailwind, private S3 bucket behind CloudFront (OAC) |
| IaC | AWS CDK (Python), one stack, one-command deploy and destroy |
| Tests | pytest unit tests + a [deepeval](https://github.com/confident-ai/deepeval) e2e **golden set** with deterministic and LLM-judged metrics ([Testing](testing.md)) |
| Observability | AgentCore Observability: OpenTelemetry traces via ADOT, CloudWatch Transaction Search |

## Key design decisions

- **The LLM never writes bottle details.** It returns only ids, scores, reasons and a serving suggestion. Code validates every id against the inventory, drops out-of-stock and duplicates, clamps and re-sorts scores, and fills the cards from `inventory.json`. Hallucinated bottles cannot reach the UI.
- **Guardrails in code, not only in the prompt.** The in-stock filter is always on in retrieval, the 3-match cap and score threshold are enforced server-side, and every drop is logged.
- **Change behavior without touching infra.** Prompts live in files, and model, threshold and N are runtime environment variables - one agent redeploy. Inventory changes need only `make kb-sync`.
- **Trusted with a golden set.** A fixed set of golden prompts runs against the deployed API with deepeval: contract invariants must hold on every prompt, per-prompt expectations must pass 80% of the time, and an LLM judge scores whether explanations are specific and refusals are safe.
- **Built to split.** Recommend and order are separate modes (prompts, tools, code modules) in one agent today, structured so they can become two agents behind an orchestrator without changing the response contract.

Continue with the [Architecture](architecture.md) or jump to [Getting Started](getting_started.md).
