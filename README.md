# Whiskey Sommelier Agent on Amazon Bedrock AgentCore (Python)

[![license](https://img.shields.io/github/license/ran-isenberg/whiskey-playground)](https://github.com/ran-isenberg/whiskey-playground/blob/main/LICENSE)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.14&color=blue?style=flat-square&logo=python)
[![release](https://github.com/ran-isenberg/whiskey-playground/actions/workflows/release.yml/badge.svg)](https://github.com/ran-isenberg/whiskey-playground/actions/workflows/release.yml)
![version](https://img.shields.io/github/v/release/ran-isenberg/whiskey-playground)
![github-star-badge](https://img.shields.io/github/stars/ran-isenberg/whiskey-playground.svg?style=social)
![issues](https://img.shields.io/github/issues/ran-isenberg/whiskey-playground)

<a href="https://ranthebuilder.cloud/">
  <img src="https://github.com/ran-isenberg/aws-lambda-mcp-cookbook/blob/main/docs/media/banner.png?raw=true" width="800" alt="Ran The Builder - Master Serverless and Platform Engineering" />
</a>

An AI whiskey sommelier: tell it a mood, a moment or a memory and it recommends bottles from **our own closed inventory**, each with a **match %** and an explanation of **why it fits you**.

It runs a [Strands](https://strandsagents.com) agent on **Amazon Bedrock AgentCore Runtime**, searches a **Bedrock Knowledge Base on Amazon S3 Vectors**, and serves a React chat UI through CloudFront - all defined in AWS CDK (Python), deployed with one command and torn down with another.

This is a hackathon proof of concept: built to be demo-reliable end to end, not production grade.

**[📜Documentation](https://ran-isenberg.github.io/whiskey-playground/)** | **[Blogs website](https://www.ranthebuilder.cloud)**
> **Contact details | mailto:ran.isenberg@ranthebuilder.cloud**

[![Twitter Follow](https://img.shields.io/twitter/follow/IsenbergRan?label=Follow&style=social)](https://twitter.com/RanBuilder)
[![Website](https://img.shields.io/badge/Website-www.ranthebuilder.cloud-blue)](https://www.ranthebuilder.cloud/)

## Getting Started

You need an AWS account with CDK bootstrapped in `us-east-1`, Bedrock access to Claude Haiku 5.5 and Titan Text Embeddings v2, Python 3.14 with [uv](https://docs.astral.sh/uv/), and Node.js.

```bash
make dev
make deploy
```

Then open the `UiUrl` from `cdk-outputs.json`, or chat from the terminal with `make chat`.

Check out the official [Documentation](https://ran-isenberg.github.io/whiskey-playground/) for the architecture, MVP status and every command.

## Current Stage

| Stage | Scope | Status |
| --- | --- | --- |
| **MVP 1 - Recommend** | Chat UI → agent → knowledge base → ranked, explained matches, refinement, guardrails | ✅ Built |
| **MVP 2 - Order** | Order recommended bottles through AgentCore Gateway (MCP) with two-step confirmation enforced in code | 🚧 Next |
| Phase 3 | Cognito login, per-user history and favorites | Not started |

Details and known gaps: [MVP Status](https://ran-isenberg.github.io/whiskey-playground/mvp_status/).

## **The Problem**

Building a demo-ready AI agent on AWS raises questions that have nothing to do with the demo itself:

* Where does the agent run, and how do you keep per-user conversation state without a database?
* How do you stop the model from recommending things you don't actually have?
* How do you make retrieval respect hard constraints like stock and budget?
* How do you change prompts and models quickly without redeploying infrastructure?
* How do you test a non-deterministic agent so you trust it on stage?

## **The Solution**

An opinionated, serverless agent stack where the guardrails live in code:

```mermaid
flowchart LR
    user(["Browser<br/>React SPA"])
    cf["CloudFront<br/>S3 UI bucket (OAC)"]
    api["API Gateway REST<br/>POST /chat · throttled"]
    chat["Chat Lambda<br/>Python 3.14 · Powertools"]

    subgraph rt["Amazon Bedrock AgentCore Runtime"]
        agent["Strands agent<br/>one per session"]
        check["check_and_fill<br/>server-side guardrails"]
    end

    llm["Claude Haiku 5.5<br/>Amazon Bedrock"]
    kb["Bedrock Knowledge Base<br/>S3 Vectors · Titan v2"]
    inv[("inventory.json<br/>S3")]
    gw["AgentCore Gateway (MCP)<br/>→ Order Lambda"]

    user --> cf
    user --> api --> chat -->|"InvokeAgentRuntime"| agent
    agent --> llm
    agent -->|"search_inventory<br/>in-stock + price filters"| kb
    agent --> check
    inv --> check
    agent -.->|"MVP 2"| gw

    classDef next stroke-dasharray: 5 5
    class gw next
```

* **The LLM returns only ids, scores, reasons and serving.** Code drops unknown, out-of-stock and duplicate ids, enforces the score threshold and the 3-match cap, and fills every card from the inventory - so a hallucinated bottle can never reach the UI.
* **Retrieval is filtered, not just prompted.** The in-stock filter is always on, and "cheaper" or a budget becomes a numeric `price_level` filter.
* **Sessions live in AgentCore Runtime.** Each `runtimeSessionId` gets its own isolated microVM holding the agent and its conversation. A failed turn is rolled back so retries work.
* **Fast iteration.** Prompts are files; model, N and threshold are runtime env vars (one agent redeploy). Inventory changes need only `make kb-sync`.
* **Built to split.** Recommend and order are separate modes (prompts, tools, modules) in one agent today, ready to become two agents behind an orchestrator without changing the API contract.

### **Features**

* Strands agent on AgentCore Runtime with direct code deploy (no Docker), Python 3.14 on ARM64.
* Bedrock Knowledge Base on S3 Vectors: one chunk per bottle, metadata sidecars generated from markdown frontmatter.
* Pydantic-validated structured output and a strict response contract shared by the API and the UI.
* Chat Lambda with [AWS Lambda Powertools](https://docs.powertools.aws.dev/lambda/python/): validation, CORS, error mapping to `INVALID_REQUEST` / `THROTTLED` / `TIMEOUT` / `AGENT_ERROR`.
* React + Vite + Tailwind UI: ranked cards with match bars, tasting notes, "why it matches you", fixtures mode for backend-free UI work.
* Secure by default S3: Block Public Access, TLS-only, SSE-S3, ACLs off, UI bucket readable only by CloudFront.
* Tests: unit tests for every guardrail, plus [deepeval](https://github.com/confident-ai/deepeval) e2e golden prompts with deterministic contract metrics and LLM-judged quality metrics.
* One JSON log line per agent turn: input, retrieved ids, raw picks, dropped ids and why, tool calls, latency.
* Makefile developer experience, ruff linting and pre-commit hooks (same config as [aws-lambda-mcp-cookbook](https://github.com/ran-isenberg/aws-lambda-mcp-cookbook)).

## Commands

| Target | Does |
| --- | --- |
| `make deploy` | Build agent, chat Lambda and UI, `cdk deploy`, then `kb-sync` |
| `make deploy-agent` | Agent or prompt change only (≈ 3 min) |
| `make kb-sync` | Inventory change: sidecars, `inventory.json`, upload, ingestion |
| `make chat` | Terminal chat against the runtime (demo fallback) |
| `make ui-dev` / `make ui-fixtures` | Local UI against the deployed API / against fixtures |
| `make test` / `make e2e` | Unit tests / deepeval golden prompts against the deployed API |
| `make lint` / `make pre-commit` | ruff check + format / all pre-commit hooks |
| `make destroy` | Tear everything down, including leftover log groups |

## Security

* No authentication: this is a hackathon demo. Cost is bounded by API Gateway throttling (5 rps, burst 10) and the 500-character message limit. Cognito is planned for phase 3.
* Least-privilege IAM for the runtime, knowledge base and chat Lambda roles.
* No bucket is public; CloudFront and API Gateway are the only public entry points.

### Known Issues

* Warm recommendation latency sits around the 10 s target; fresh sessions take longer.
* Claude Haiku 5.5 does not accept `temperature`, so score stability relies on the rubric.

## Code Contributions

Code contributions are welcomed. Open an issue or a pull request.

## Connect

- Email: ran.isenberg@ranthebuilder.cloud
- Blog: https://www.ranthebuilder.cloud
- Bluesky: [@ranthebuilder.cloud](https://bsky.app/profile/ranthebuilder.cloud)
- X:       [@RanBuilder](https://twitter.com/RanBuilder)
- LinkedIn: https://www.linkedin.com/in/ranbuilder/

## Credits

* [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
* [Strands Agents](https://strandsagents.com)
* [AWS Lambda Powertools (Python)](https://github.com/aws-powertools/powertools-lambda-python)
* [deepeval](https://github.com/confident-ai/deepeval)
* [AWS Lambda MCP Cookbook](https://github.com/ran-isenberg/aws-lambda-mcp-cookbook)

## License

This library is licensed under the MIT License. See the [LICENSE](https://github.com/ran-isenberg/whiskey-playground/blob/main/LICENSE) file.
