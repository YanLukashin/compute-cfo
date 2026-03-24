"""compute-cfo: Cost tracking, attribution, and budget enforcement for AI inference APIs."""

from .budget import BudgetPolicy
from .exporters import console_exporter, jsonl_exporter, webhook_exporter
from .pricing import get_cost, get_price
from .tracker import CostTracker
from .types import BudgetExceededError, CostEvent
from .wrapper import wrap

__version__ = "0.3.0"

__all__ = [
    "wrap",
    "CostTracker",
    "CostEvent",
    "BudgetPolicy",
    "BudgetExceededError",
    "get_cost",
    "get_price",
    "console_exporter",
    "jsonl_exporter",
    "webhook_exporter",
]
