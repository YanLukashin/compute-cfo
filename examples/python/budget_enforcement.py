"""Budget enforcement — stop runaway spend."""

from compute_cfo import wrap, CostTracker, BudgetPolicy, BudgetExceededError
from openai import OpenAI

tracker = CostTracker(
    budget=BudgetPolicy(
        max_cost=0.05,        # $0.05 limit for demo
        window="daily",
        on_exceed="raise",
    ),
    export="console",
)

client = wrap(OpenAI(), tracker=tracker)

try:
    for i in range(100):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Count to {i}"}],
            metadata={"project": "budget-demo"},
        )
        print(f"Call {i+1}: ${tracker.total_cost:.6f} spent")
except BudgetExceededError as e:
    print(f"\nBudget exceeded! {e}")
    print(f"Total spent: ${tracker.total_cost:.6f}")
