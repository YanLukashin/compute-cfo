"""Budget policy enforcement."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Literal, Optional

from .types import BudgetExceededError, CostEvent


@dataclass
class BudgetPolicy:
    """Defines spending limits and enforcement behavior.

    Args:
        max_cost: Maximum allowed spend in USD.
        window: Time window for the budget. "total" means lifetime of the tracker.
        on_exceed: Action when budget is exceeded.
            - "raise": raise BudgetExceededError
            - "warn": emit a warning
            - "callback": call the on_exceed_callback function
        on_exceed_callback: Called when on_exceed="callback". Receives the CostEvent
            that would exceed the budget.
        tags: If set, this budget applies only to events matching ALL these tags.
    """

    max_cost: float
    window: Literal["hourly", "daily", "monthly", "total"] = "total"
    on_exceed: Literal["raise", "warn", "callback"] = "raise"
    on_exceed_callback: Optional[Callable[[CostEvent, float], None]] = field(
        default=None, repr=False
    )
    tags: Optional[Dict[str, str]] = None

    def _get_window_start(self, now: datetime) -> Optional[datetime]:
        if self.window == "total":
            return None
        if self.window == "hourly":
            return now.replace(minute=0, second=0, microsecond=0)
        if self.window == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if self.window == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return None

    def _matches_tags(self, event: CostEvent) -> bool:
        if self.tags is None:
            return True
        return all(event.tags.get(k) == v for k, v in self.tags.items())

    def current_spend(self, events: List[CostEvent]) -> float:
        """Calculate current spend within the active window."""
        now = datetime.now(timezone.utc)
        window_start = self._get_window_start(now)
        total = 0.0
        for e in events:
            if window_start and e.timestamp < window_start:
                continue
            if not self._matches_tags(e):
                continue
            if e.cost_usd is not None:
                total += e.cost_usd
        return total

    def check(self, events: List[CostEvent], pending_event: CostEvent) -> None:
        """Check if recording pending_event would exceed the budget.

        Raises BudgetExceededError or warns depending on on_exceed setting.
        """
        if not self._matches_tags(pending_event):
            return

        current = self.current_spend(events)
        pending_cost = pending_event.cost_usd or 0.0
        projected = current + pending_cost

        if projected <= self.max_cost:
            return

        if self.on_exceed == "raise":
            raise BudgetExceededError(self.max_cost, projected, self.window)
        elif self.on_exceed == "warn":
            warnings.warn(
                f"[compute-cfo] Budget warning: ${projected:.4f} / ${self.max_cost:.4f} "
                f"({self.window} window)",
                stacklevel=3,
            )
        elif self.on_exceed == "callback" and self.on_exceed_callback:
            self.on_exceed_callback(pending_event, projected)
