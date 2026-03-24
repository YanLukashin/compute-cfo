# compute-cfo

**Know what your AI agents cost. Control it before it's a problem.**

Drop-in cost tracking, attribution, and budget enforcement for OpenAI and Anthropic APIs. One line to add — zero config required.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/v/compute-cfo)](https://pypi.org/project/compute-cfo/)
[![npm](https://img.shields.io/npm/v/compute-cfo)](https://www.npmjs.com/package/compute-cfo)

---

## Why

Most teams don't fail on AI spend because they lack dashboards. They fail because costs become **unpredictable in production**: recursive agent loops, silent budget overruns, fragmented provider bills, and no hard control layer.

`compute-cfo` gives you:

- **Instant visibility** — see cost per call, per model, per agent
- **Budget enforcement** — hard spending limits that actually stop requests
- **Attribution** — tag every call by project, agent, team, or feature
- **Multi-provider** — OpenAI + Anthropic, same API
- **Zero dependencies** — beyond your existing SDK

## Install

**Python:**
```bash
pip install compute-cfo
```

**TypeScript/JavaScript:**
```bash
npm install compute-cfo
```

## Quick Start

### Python

```python
from compute_cfo import wrap
from openai import OpenAI

# One line — that's it
client = wrap(OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    metadata={"project": "search", "agent": "summarizer"},
)
# stderr: [compute-cfo] gpt-4o | 42 tokens | $0.000315 | project:search
```

### TypeScript

```typescript
import { wrap } from 'compute-cfo';
import OpenAI from 'openai';

const client = wrap(new OpenAI());

const response = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'Hello' }],
  metadata: { project: 'search', agent: 'summarizer' },
});
```

## Budget Enforcement

Stop runaway spend before it happens.

### Python

```python
from compute_cfo import wrap, CostTracker, BudgetPolicy
from openai import OpenAI

tracker = CostTracker(
    budget=BudgetPolicy(
        max_cost=10.0,       # $10 limit
        window="daily",      # resets daily
        on_exceed="raise",   # raises BudgetExceededError
    ),
)
client = wrap(OpenAI(), tracker=tracker)

# When the budget is exceeded:
# compute_cfo.BudgetExceededError: Budget exceeded: $10.0312 / $10.0000 (daily window)
```

### TypeScript

```typescript
import { wrap, CostTracker, BudgetPolicy } from 'compute-cfo';
import OpenAI from 'openai';

const tracker = new CostTracker({
  budget: new BudgetPolicy({
    maxCost: 10,
    window: 'daily',
    onExceed: 'throw',
  }),
});
const client = wrap(new OpenAI(), { tracker });
```

## Query Spend

```python
tracker.total_cost                    # $4.23
tracker.cost_by("project")           # {"search": 3.10, "chat": 1.13}
tracker.cost_by("model")             # {"gpt-4o": 4.00, "gpt-4o-mini": 0.23}
tracker.cost_by("provider")          # {"openai": 3.50, "anthropic": 0.73}
```

## Anthropic Support

```python
from compute_cfo import wrap
from anthropic import Anthropic

client = wrap(Anthropic())

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
    compute_cfo_tags={"project": "search"},
)
```

## Export Cost Events

```python
# Console output (default)
tracker = CostTracker(export="console")

# JSONL file
tracker = CostTracker(export="jsonl")

# Custom file path
tracker = CostTracker(export="jsonl:/path/to/costs.jsonl")

# Webhook
tracker = CostTracker(export="webhook:https://your-server.com/costs")

# Silent (no output)
tracker = CostTracker(quiet=True)
```

Each cost event is a structured record:

```json
{
  "timestamp": "2026-03-23T12:00:00Z",
  "provider": "openai",
  "model": "gpt-4o",
  "operation": "chat.completions",
  "input_tokens": 150,
  "output_tokens": 42,
  "cost_usd": 0.000795,
  "latency_ms": 1230,
  "tags": {"project": "search", "agent": "summarizer"},
  "budget_remaining_usd": 9.999205
}
```

## Budget Options

| Option | Values | Description |
|--------|--------|-------------|
| `max_cost` | float | Maximum spend in USD |
| `window` | `"hourly"`, `"daily"`, `"monthly"`, `"total"` | Budget reset window |
| `on_exceed` | `"raise"`, `"warn"`, `"callback"` | Action when exceeded |
| `tags` | dict | Apply budget only to matching tags |

## Supported Models

Pricing data for 40+ models including:

- **OpenAI**: GPT-4.1, GPT-4o, GPT-3.5, o3, o4-mini, embeddings
- **Anthropic**: Claude Opus 4, Sonnet 4, 3.7 Sonnet, 3.5 Sonnet/Haiku, 3 Opus/Sonnet/Haiku

Unknown models return `null` cost — your calls still work, just without cost data.

## Roadmap

- [ ] Streaming support (token counting from chunks)
- [ ] Google Gemini / Vertex AI
- [ ] Mistral, Groq, Together AI
- [ ] Async wrapper support
- [ ] Cost anomaly detection
- [ ] CLI for analyzing JSONL cost files

## About

Built by the team behind [Compute CFO](https://computecfo.com) — the financial control plane for AI inference. We're building the system of record for inference finance: spend visibility, budget control, forecasting, and procurement intelligence.

## License

[Apache 2.0](LICENSE)
