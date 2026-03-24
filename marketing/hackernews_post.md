# Hacker News Post

**Title:** Show HN: Compute-CFO – Open-source SDK to track and control LLM inference costs

**URL:** https://github.com/YanLukashin/compute-cfo

**Comment (post after submitting):**

Hi HN — I built compute-cfo because tracking AI inference costs across providers was a pain. The existing options were either heavyweight proxies or basic token counters.

compute-cfo is a lightweight SDK (Python + TypeScript) that wraps your existing OpenAI/Anthropic/Gemini/Mistral client and tracks cost, tokens, and latency per call. No proxy, no infra — just `wrap(client)`.

The feature I'm most excited about is budget enforcement. You set a hard limit ($10/day, $100/month, etc.) and it raises an exception before you exceed it. This is critical for agentic workflows where a bug can cause a recursive loop that burns through your budget.

Key features:
- Drop-in: one line to add
- 60+ models with up-to-date pricing
- Budget enforcement with hourly/daily/monthly windows
- Tag-based attribution (project, agent, team)
- Export to console, JSONL, or webhook

Apache 2.0. Would love feedback on the API design and what else you'd want from a tool like this.
