"""Core data types for compute-cfo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class CostEvent:
    """A single inference cost event."""

    timestamp: datetime
    provider: str
    model: str
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: Optional[float]
    latency_ms: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    budget_remaining_usd: Optional[float] = None
    raw_response: Any = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        d: Dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "provider": self.provider,
            "model": self.model,
            "operation": self.operation,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
        }
        if self.latency_ms is not None:
            d["latency_ms"] = self.latency_ms
        if self.tags:
            d["tags"] = self.tags
        if self.budget_remaining_usd is not None:
            d["budget_remaining_usd"] = self.budget_remaining_usd
        return d


class BudgetExceededError(Exception):
    """Raised when a budget limit has been exceeded."""

    def __init__(self, limit: float, current: float, window: str):
        self.limit = limit
        self.current = current
        self.window = window
        super().__init__(
            f"Budget exceeded: ${current:.4f} / ${limit:.4f} ({window} window)"
        )
