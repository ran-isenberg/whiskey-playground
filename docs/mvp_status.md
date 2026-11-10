# MVP Status

The project follows a 4-hour hackathon plan (requirements spec §9) split into two MVPs.

| Stage | Scope | Status |
| --- | --- | --- |
| **MVP 1 - Recommend** | Chat UI → agent → knowledge base → ranked, explained matches; refinement; guardrails | :white_check_mark: **Built** |
| **MVP 2 - Order** | Order 1–3 recommended bottles via AgentCore Gateway (MCP) → mock order Lambda, two-step confirmation enforced in code | :construction: Next |
| Phase 3 | Cognito login, per-user history and favorites (AgentCore Memory) | Not started |

## MVP 1: what works

=== "Agent"

    - Free text in, **0–3 ranked matches** out, each with a match %, a "why it matches you" tied to the user's own words, and a serving suggestion.
    - Multi-turn refinement in the same session (*"something cheaper"*, *"less smoky"*) - "cheaper" becomes a numeric `price_level` filter on retrieval.
    - Server-side checks on every pick: unknown ids, out-of-stock bottles, duplicates and low scores are dropped and logged; scores clamped, re-sorted, cut to N.
    - Off-topic input gets a polite steer and zero matches; distress gets a gentle answer and no alcohol push; prompt injection cannot produce non-inventory bottles or reveal the prompt.
    - Structured output validated with Pydantic, one retry, then a clean `AGENT_ERROR`. A failed turn is rolled back so the session (and the UI Retry) keeps working.

=== "API"

    - `POST /chat` with request validation, warm-up requests, and contract error codes for validation, throttling, timeouts and agent errors.
    - Stage throttling 5 rps / burst 10; Lambda timeout below the API Gateway 29 s limit.

=== "UI"

    - Chat with example prompt chips, typing indicator, ranked cards (score bar, details, tasting notes, why, serving), "nothing in our cellar fits" state, error banner with Retry, *New conversation*, responsible-drinking footer.
    - Fixtures mode (`make ui-fixtures`) to work on the UI with no backend.

=== "Ops"

    - One stack, `make deploy` / `make destroy`; agent-only redeploys for prompt or model changes; `make kb-sync` for inventory changes.
    - One JSON log line per agent turn: input, retrieved ids, raw picks, dropped ids and reasons, tool calls, latency.

## Known gaps and deviations

| Item | Notes |
| --- | --- |
| Latency target (NF-6, ≤ 10 s warm) | Local warm turns run 9–10 s; e2e runs on fresh sessions measure 12–15 s. Levers: fewer retrieved candidates (`RETRIEVE_K`), shorter snippets. |
| Low temperature (AG-3) | Claude Haiku 5.5 rejects `temperature`, so none is sent. Score stability relies on the rubric. `TEMPERATURE` can be set again for models that accept it. |
| Short persona message (AG-14) | Prompt-level only; some replies run 2–3 sentences. |

## MVP 2: what comes next

- `place_order` tool exposed through an **AgentCore Gateway** Lambda target (IAM inbound auth from the runtime role), mock order Lambda returning a UUID4.
- **Two-turn confirmation enforced in code**: the first order request only returns a `pending_order`; a Strands hook blocks `place_order` unless the previous turn proposed exactly the same items and quantities.
- UI: per-card checkbox and quantity stepper, *Order selected (n)*, Confirm / Cancel, order confirmation card.
- Golden prompts 9–10 and unit tests for the order guard and order Lambda.
