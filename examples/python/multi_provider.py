"""Multi-provider tracking with shared CostTracker."""

from compute_cfo import wrap, CostTracker
from openai import OpenAI
from anthropic import Anthropic

# Shared tracker across providers
tracker = CostTracker(export="console")

openai_client = wrap(OpenAI(), tracker=tracker)
anthropic_client = wrap(Anthropic(), tracker=tracker)

# OpenAI call
openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello from OpenAI"}],
    metadata={"project": "multi-provider-demo", "team": "engineering"},
)

# Anthropic call
anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": "Hello from Anthropic"}],
    compute_cfo_tags={"project": "multi-provider-demo", "team": "engineering"},
)

# Analyze spend
print(f"\nTotal cost: ${tracker.total_cost:.6f}")
print(f"By provider: {tracker.cost_by('provider')}")
print(f"By model: {tracker.cost_by('model')}")
print(f"By project: {tracker.cost_by('project')}")
