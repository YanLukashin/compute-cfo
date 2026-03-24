---
title: How Much Do Your AI Agents Actually Cost?
published: false
tags: ai, openai, python, typescript
---

You shipped an AI agent. It works great. Then the bill arrives.

$847 for a Tuesday. A single recursive loop burned through your monthly budget overnight. And the worst part — you have no idea which agent, which project, or which model caused it.

Sound familiar?

## The Problem Nobody Talks About

Most AI teams track costs the same way: they check the OpenAI dashboard at the end of the month and hope for the best. But in production, this falls apart:

- **Agent loops** — an agent retries or recurses, and suddenly one task costs 100x what you expected
- **No attribution** — you know you spent $2,000 on GPT-4o, but was it the search agent? The summarizer? The chatbot?
- **Multi-provider chaos** — you're using OpenAI for some things, Anthropic for others, maybe Gemini too. Good luck reconciling those bills
- **No hard limits** — dashboards show you what you spent *after* the damage is done

## What If You Could Control It?

We built [compute-cfo](https://github.com/YanLukashin/compute-cfo) — an open-source SDK that gives you cost tracking, attribution, and budget enforcement for LLM APIs.

One line to add. Zero config. Python + TypeScript.

```bash
pip install compute-cfo
# or
npm install compute-cfo
```

## 3 Lines to Track Every Dollar

```python
from compute_cfo import wrap
from openai import OpenAI

client = wrap(OpenAI())
```

That's it. Every call through this client now logs:
- Model used
- Input/output tokens
- Cost in USD
- Latency
- Any tags you add

## Budget Enforcement That Actually Works

This is the feature I'm most excited about. Set a hard limit, and compute-cfo raises an exception *before* you exceed it:

```python
from compute_cfo import wrap, CostTracker, BudgetPolicy

tracker = CostTracker(
    budget=BudgetPolicy(
        max_cost=10.0,       # $10 limit
        window="daily",      # resets every day
        on_exceed="raise",   # raises BudgetExceededError
    ),
)
client = wrap(OpenAI(), tracker=tracker)
```

Your agent hits $10? `BudgetExceededError`. No surprises. No $847 Tuesdays.

You can set budgets per hour, day, month, or total lifetime. And you can scope them to specific tags — so your search agent gets $50/day while your chatbot gets $200/day.

## Know Where Every Dollar Goes

Tag every call with project, agent, team, or any custom label:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Summarize this document"}],
    metadata={"project": "search", "agent": "summarizer", "team": "platform"},
)
```

Then query your spend:

```python
tracker.total_cost            # $4.23
tracker.cost_by("project")    # {"search": 3.10, "chat": 1.13}
tracker.cost_by("model")      # {"gpt-4o": 4.00, "gpt-4o-mini": 0.23}
tracker.cost_by("team")       # {"platform": 3.10, "product": 1.13}
```

## Works Across Providers

Same API for OpenAI, Anthropic, Google Gemini, and Mistral:

```python
from openai import OpenAI
from anthropic import Anthropic

tracker = CostTracker(export="console")

openai_client = wrap(OpenAI(), tracker=tracker)
anthropic_client = wrap(Anthropic(), tracker=tracker)

# Both tracked in the same place
tracker.cost_by("provider")  # {"openai": 2.50, "anthropic": 1.73}
```

60+ models with up-to-date pricing built in. Unknown models still work — you just don't get cost data.

## Export Everything

Cost events are structured JSON records. Send them wherever you want:

```python
# Console (default)
tracker = CostTracker(export="console")

# JSONL file for analysis
tracker = CostTracker(export="jsonl")

# Webhook for real-time alerts
tracker = CostTracker(export="webhook:https://your-server.com/costs")
```

Each event looks like:

```json
{
  "timestamp": "2026-03-24T12:00:00Z",
  "provider": "openai",
  "model": "gpt-4o",
  "input_tokens": 150,
  "output_tokens": 42,
  "cost_usd": 0.000795,
  "tags": {"project": "search", "agent": "summarizer"},
  "budget_remaining_usd": 9.999205
}
```

## TypeScript Too

Everything works the same in TypeScript:

```typescript
import { wrap, CostTracker, BudgetPolicy } from 'compute-cfo';
import OpenAI from 'openai';

const tracker = new CostTracker({
  budget: new BudgetPolicy({ maxCost: 10, window: 'daily', onExceed: 'throw' }),
});
const client = wrap(new OpenAI(), { tracker });
```

## Open Source, Free Forever

[compute-cfo](https://github.com/YanLukashin/compute-cfo) is Apache 2.0 licensed. Use it however you want.

We're building this because we believe every team running AI in production needs a financial control layer — not just dashboards, but actual enforcement.

**Links:**
- GitHub: [github.com/YanLukashin/compute-cfo](https://github.com/YanLukashin/compute-cfo)
- Website: [computecfo.com](https://computecfo.com)
- PyPI: `pip install compute-cfo`
- npm: `npm install compute-cfo`

If this is useful, star it on GitHub. And if you have feature requests, open an issue — we're actively building.

---

*Built by the team behind [Compute CFO](https://computecfo.com) — the financial control plane for AI inference.*
