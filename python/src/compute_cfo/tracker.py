"""CostTracker — core cost accumulation and querying."""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Dict, List, Optional

from .budget import BudgetPolicy
from .exporters import Exporter, get_exporter
from .types import CostEvent


class CostTracker:
    """Accumulates cost events and provides spend queries.

    Thread-safe by default.

    Args:
        budget: Optional budget policy to enforce.
        export: Exporter specification. Can be:
            - "console" (default): print to stdout
            - "jsonl": append to compute_cfo_events.jsonl
            - "jsonl:/path/to/file.jsonl": custom file path
            - None: no automatic export
            - A callable that receives CostEvent
        quiet: If True, suppress console output even if export="console".
    """

    def __init__(
        self,
        budget: Optional[BudgetPolicy] = None,
        export: Optional[str] = "console",
        quiet: bool = False,
    ):
        self._events: List[CostEvent] = []
        self._lock = threading.Lock()
        self._budget = budget
        self._exporters: List[Exporter] = []

        if quiet:
            export = None

        if export is not None:
            self._exporters.append(get_exporter(export))

    def record(self, event: CostEvent) -> None:
        """Record a cost event. Checks budget and exports."""
        with self._lock:
            if self._budget:
                self._budget.check(self._events, event)

            remaining = None
            if self._budget and event.cost_usd is not None:
                spent = self._budget.current_spend(self._events) + event.cost_usd
                remaining = max(0, self._budget.max_cost - spent)
            event.budget_remaining_usd = remaining

            self._events.append(event)

        for exporter in self._exporters:
            exporter(event)

    @property
    def events(self) -> List[CostEvent]:
        """Return a copy of all recorded events."""
        with self._lock:
            return list(self._events)

    @property
    def total_cost(self) -> float:
        """Total cost across all events."""
        with self._lock:
            return sum(e.cost_usd for e in self._events if e.cost_usd is not None)

    def cost_by(self, key: str) -> Dict[str, float]:
        """Aggregate cost by a tag key or by 'model'/'provider'.

        Args:
            key: Tag name, or "model" / "provider" to group by those fields.

        Returns:
            Dict mapping key values to total cost.
        """
        result: Dict[str, float] = defaultdict(float)
        with self._lock:
            for e in self._events:
                if e.cost_usd is None:
                    continue
                if key == "model":
                    result[e.model] += e.cost_usd
                elif key == "provider":
                    result[e.provider] += e.cost_usd
                else:
                    tag_val = e.tags.get(key)
                    if tag_val is not None:
                        result[tag_val] += e.cost_usd
        return dict(result)

    def reset(self) -> None:
        """Clear all recorded events."""
        with self._lock:
            self._events.clear()
