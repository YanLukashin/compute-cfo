from datetime import datetime, timezone

from compute_cfo.tracker import CostTracker
from compute_cfo.types import CostEvent


def _make_event(
    cost: float = 0.01,
    model: str = "gpt-4o",
    provider: str = "openai",
    tags: dict | None = None,
) -> CostEvent:
    return CostEvent(
        timestamp=datetime.now(timezone.utc),
        provider=provider,
        model=model,
        operation="chat.completions",
        input_tokens=100,
        output_tokens=50,
        cost_usd=cost,
        tags=tags or {},
    )


def test_empty_tracker():
    t = CostTracker(quiet=True)
    assert t.total_cost == 0.0
    assert t.events == []


def test_record_and_total():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05))
    t.record(_make_event(cost=0.03))
    assert abs(t.total_cost - 0.08) < 1e-10


def test_cost_by_model():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05, model="gpt-4o"))
    t.record(_make_event(cost=0.01, model="gpt-4o-mini"))
    t.record(_make_event(cost=0.03, model="gpt-4o"))
    by_model = t.cost_by("model")
    assert abs(by_model["gpt-4o"] - 0.08) < 1e-10
    assert abs(by_model["gpt-4o-mini"] - 0.01) < 1e-10


def test_cost_by_tag():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05, tags={"project": "search"}))
    t.record(_make_event(cost=0.03, tags={"project": "chat"}))
    t.record(_make_event(cost=0.02, tags={"project": "search"}))
    by_project = t.cost_by("project")
    assert abs(by_project["search"] - 0.07) < 1e-10
    assert abs(by_project["chat"] - 0.03) < 1e-10


def test_cost_by_provider():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05, provider="openai"))
    t.record(_make_event(cost=0.03, provider="anthropic"))
    by_provider = t.cost_by("provider")
    assert abs(by_provider["openai"] - 0.05) < 1e-10
    assert abs(by_provider["anthropic"] - 0.03) < 1e-10


def test_reset():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05))
    t.reset()
    assert t.total_cost == 0.0
    assert t.events == []


def test_events_returns_copy():
    t = CostTracker(quiet=True)
    t.record(_make_event(cost=0.05))
    events = t.events
    events.clear()
    assert len(t.events) == 1  # original not affected
