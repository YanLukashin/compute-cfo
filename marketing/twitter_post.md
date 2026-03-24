# Twitter/X Post

## Main thread

**Tweet 1:**
Just open-sourced compute-cfo — a drop-in SDK to track and control LLM inference costs.

One line to add. Zero config. Works with OpenAI, Anthropic, Gemini, and Mistral.

pip install compute-cfo
npm install compute-cfo

github.com/YanLukashin/compute-cfo

🧵 Why we built this ↓

**Tweet 2:**
Most teams don't fail on AI spend because they lack dashboards.

They fail because costs become unpredictable in production: recursive agent loops, silent budget overruns, fragmented provider bills.

**Tweet 3:**
compute-cfo gives you:

→ Cost per call, per model, per agent
→ Hard budget limits that actually stop requests
→ Tag every call by project/agent/team
→ 60+ models priced out of the box
→ Python + TypeScript

**Tweet 4:**
3 lines to add cost tracking:

```python
from compute_cfo import wrap
from openai import OpenAI

client = wrap(OpenAI())
```

That's it. Every call now logs cost, tokens, and latency.

**Tweet 5:**
Budget enforcement that actually works:

```python
tracker = CostTracker(
    budget=BudgetPolicy(
        max_cost=10.0,
        window="daily",
        on_exceed="raise",
    ),
)
```

Your agent hits $10 → BudgetExceededError. No surprises.

**Tweet 6:**
Apache 2.0 license. Use it however you want.

We're building Compute CFO — the financial control plane for AI inference. This SDK is the open-source foundation.

⭐ Star it if useful: github.com/YanLukashin/compute-cfo
