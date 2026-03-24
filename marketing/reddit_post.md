# Reddit Post

## For r/MachineLearning (flair: [Project])

**Title:** [P] compute-cfo: Open-source SDK to track and control LLM inference costs (Python + TypeScript)

**Body:**

We've been building AI agents at work and kept running into the same problem — we had no idea how much each agent run actually cost until the bill arrived.

Existing tools either require a proxy server setup or only do basic token counting. We wanted something that:

- Drops into existing code with one line change
- Actually enforces budgets (not just alerts)
- Tags costs by project/agent/team
- Works across providers

So we built **compute-cfo** — an open-source SDK (Python + TypeScript) for cost tracking, attribution, and budget enforcement.

**What it does:**
- Wraps OpenAI, Anthropic, Google Gemini, and Mistral SDK clients
- Tracks cost, tokens, and latency per call
- Enforces hard spending limits (hourly/daily/monthly)
- Tags every call for attribution (project, agent, team, feature)
- Exports events to console, JSONL, or webhook

**Quick example:**
```python
from compute_cfo import wrap, CostTracker, BudgetPolicy
from openai import OpenAI

tracker = CostTracker(
    budget=BudgetPolicy(max_cost=10.0, window="daily", on_exceed="raise")
)
client = wrap(OpenAI(), tracker=tracker)

# Every call is now tracked and budget-enforced
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    metadata={"project": "search", "agent": "summarizer"},
)

tracker.total_cost          # $0.000795
tracker.cost_by("project")  # {"search": 0.000795}
```

**Links:**
- GitHub: https://github.com/YanLukashin/compute-cfo
- PyPI: `pip install compute-cfo`
- npm: `npm install compute-cfo`

Apache 2.0 license. Would love feedback — especially on what providers or features to add next.

---

## For r/LocalLLaMA

**Title:** Open-sourced a cost tracking SDK for LLM APIs — tracks spend across OpenAI, Anthropic, Gemini, Mistral

**Body:**

Built this because we were tired of getting surprised by inference bills. compute-cfo wraps your existing SDK client and tracks every call — cost, tokens, latency, with attribution tags.

The killer feature is budget enforcement: set a hard daily/hourly/monthly limit, and it raises an exception before you overspend. Useful for agentic workflows that can loop unexpectedly.

Works with OpenAI, Anthropic, Google Gemini, and Mistral. Python + TypeScript.

`pip install compute-cfo` / `npm install compute-cfo`

GitHub: https://github.com/YanLukashin/compute-cfo

Happy to add more providers if there's interest (Groq, Together, etc).
