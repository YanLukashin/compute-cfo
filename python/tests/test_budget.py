import warnings
from datetime import datetime, timezone

import pytest

from compute_cfo.budget import BudgetPolicy
from compute_cfo.tracker import CostTracker
from compute_cfo.types import BudgetExceededError, CostEvent


def _make_event(cost: float = 0.01) -> CostEvent:
    return CostEvent(
        timestamp=datetime.now(timezone.utc),
        provider="openai",
        model="gpt-4o",
        operation="chat.completions",
        input_tokens=100,
        output_tokens=50,
        cost_usd=cost,
    )


def test_budget_raise_on_exceed():
    tracker = CostTracker(
        budget=BudgetPolicy(max_cost=0.05, on_exceed="raise"),
        quiet=True,
    )
    tracker.record(_make_event(cost=0.03))
    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.record(_make_event(cost=0.03))
    assert exc_info.value.limit == 0.05
    assert exc_info.value.current > 0.05


def test_budget_warn_on_exceed():
    tracker = CostTracker(
        budget=BudgetPolicy(max_cost=0.05, on_exceed="warn"),
        quiet=True,
    )
    tracker.record(_make_event(cost=0.03))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tracker.record(_make_event(cost=0.03))
        assert len(w) == 1
        assert "Budget warning" in str(w[0].message)


def test_budget_callback_on_exceed():
    exceeded_events = []

    def on_exceed(event: CostEvent, projected: float):
        exceeded_events.append((event, projected))

    tracker = CostTracker(
        budget=BudgetPolicy(
            max_cost=0.05,
            on_exceed="callback",
            on_exceed_callback=on_exceed,
        ),
        quiet=True,
    )
    tracker.record(_make_event(cost=0.03))
    tracker.record(_make_event(cost=0.03))
    assert len(exceeded_events) == 1
    assert exceeded_events[0][1] > 0.05


def test_budget_not_exceeded():
    tracker = CostTracker(
        budget=BudgetPolicy(max_cost=1.00, on_exceed="raise"),
        quiet=True,
    )
    tracker.record(_make_event(cost=0.03))
    tracker.record(_make_event(cost=0.03))
    assert abs(tracker.total_cost - 0.06) < 1e-10


def test_budget_remaining_tracked():
    tracker = CostTracker(
        budget=BudgetPolicy(max_cost=1.00),
        quiet=True,
    )
    tracker.record(_make_event(cost=0.30))
    event = tracker.events[-1]
    assert event.budget_remaining_usd is not None
    assert abs(event.budget_remaining_usd - 0.70) < 1e-10


def test_budget_with_tag_filter():
    tracker = CostTracker(
        budget=BudgetPolicy(
            max_cost=0.05,
            on_exceed="raise",
            tags={"project": "expensive"},
        ),
        quiet=True,
    )
    # This should not count toward the budget
    cheap_event = _make_event(cost=0.10)
    cheap_event.tags = {"project": "cheap"}
    tracker.record(cheap_event)

    # This should count
    exp_event = _make_event(cost=0.03)
    exp_event.tags = {"project": "expensive"}
    tracker.record(exp_event)

    # This should exceed
    exp_event2 = _make_event(cost=0.03)
    exp_event2.tags = {"project": "expensive"}
    with pytest.raises(BudgetExceededError):
        tracker.record(exp_event2)
