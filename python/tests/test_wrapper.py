"""Tests for the wrap() function using mock SDK clients."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from compute_cfo.tracker import CostTracker
from compute_cfo.wrapper import wrap


def _make_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.__class__.__module__ = "openai.client"
    # Simulate response
    response = SimpleNamespace(
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        choices=[SimpleNamespace(message=SimpleNamespace(content="Hello!"))],
    )
    client.chat.completions.create.return_value = response
    return client


def _make_anthropic_client():
    """Create a mock Anthropic client."""
    client = MagicMock()
    client.__class__.__module__ = "anthropic.client"
    response = SimpleNamespace(
        model="claude-sonnet-4-20250514",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
        content=[SimpleNamespace(text="Hello!")],
    )
    client.messages.create.return_value = response
    return client


def test_wrap_openai_tracks_cost():
    tracker = CostTracker(quiet=True)
    client = _make_openai_client()
    wrapped = wrap(client, tracker=tracker)

    response = wrapped.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert response.model == "gpt-4o"
    assert len(tracker.events) == 1
    event = tracker.events[0]
    assert event.provider == "openai"
    assert event.model == "gpt-4o"
    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.cost_usd is not None
    assert event.cost_usd > 0


def test_wrap_openai_with_tags():
    tracker = CostTracker(quiet=True)
    client = _make_openai_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
        metadata={"project": "search", "agent": "summarizer"},
    )

    event = tracker.events[0]
    assert event.tags == {"project": "search", "agent": "summarizer"}


def test_wrap_anthropic_tracks_cost():
    tracker = CostTracker(quiet=True)
    client = _make_anthropic_client()
    wrapped = wrap(client, tracker=tracker)

    response = wrapped.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "hi"}],
    )

    assert len(tracker.events) == 1
    event = tracker.events[0]
    assert event.provider == "anthropic"
    assert event.model == "claude-sonnet-4-20250514"
    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.cost_usd is not None


def test_wrap_anthropic_with_tags():
    tracker = CostTracker(quiet=True)
    client = _make_anthropic_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "hi"}],
        compute_cfo_tags={"project": "search"},
    )

    event = tracker.events[0]
    assert event.tags == {"project": "search"}


def test_wrap_passthrough_attributes():
    """Non-tracked attributes should pass through to the original client."""
    tracker = CostTracker(quiet=True)
    client = _make_openai_client()
    client.models = MagicMock()
    client.models.list.return_value = ["gpt-4o"]

    wrapped = wrap(client, tracker=tracker)
    result = wrapped.models.list()
    assert result == ["gpt-4o"]


def test_wrap_unsupported_client():
    """Should raise TypeError for unsupported clients."""
    import pytest

    tracker = CostTracker(quiet=True)

    class FakeClient:
        pass

    with pytest.raises(TypeError, match="Unsupported client type"):
        wrap(FakeClient(), tracker=tracker)


def test_wrap_records_latency():
    tracker = CostTracker(quiet=True)
    client = _make_openai_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
    )

    event = tracker.events[0]
    assert event.latency_ms is not None
    assert event.latency_ms >= 0


# ── Google Gemini ────────────────────────────────────────────


def _make_gemini_client():
    """Create a mock Google Gemini client."""
    client = MagicMock()
    client.__class__.__module__ = "google_genai.client"
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=100,
            candidates_token_count=50,
        ),
        text="Hello!",
    )
    client.models.generate_content.return_value = response
    return client


def test_wrap_gemini_tracks_cost():
    tracker = CostTracker(quiet=True)
    client = _make_gemini_client()
    wrapped = wrap(client, tracker=tracker)

    response = wrapped.models.generate_content(
        model="gemini-2.5-flash",
        contents="hi",
    )

    assert len(tracker.events) == 1
    event = tracker.events[0]
    assert event.provider == "google"
    assert event.model == "gemini-2.5-flash"
    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.cost_usd is not None
    assert event.cost_usd > 0


def test_wrap_gemini_with_tags():
    tracker = CostTracker(quiet=True)
    client = _make_gemini_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.models.generate_content(
        model="gemini-2.5-flash",
        contents="hi",
        compute_cfo_tags={"project": "search"},
    )

    event = tracker.events[0]
    assert event.tags == {"project": "search"}


def test_wrap_gemini_strips_models_prefix():
    tracker = CostTracker(quiet=True)
    client = _make_gemini_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.models.generate_content(
        model="models/gemini-2.5-pro",
        contents="hi",
    )

    event = tracker.events[0]
    assert event.model == "gemini-2.5-pro"


# ── Mistral ──────────────────────────────────────────────────


def _make_mistral_client():
    """Create a mock Mistral client."""
    client = MagicMock()
    client.__class__.__module__ = "mistralai.client"
    response = SimpleNamespace(
        model="mistral-large-latest",
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        choices=[SimpleNamespace(message=SimpleNamespace(content="Hello!"))],
    )
    client.chat.complete.return_value = response
    return client


def test_wrap_mistral_tracks_cost():
    tracker = CostTracker(quiet=True)
    client = _make_mistral_client()
    wrapped = wrap(client, tracker=tracker)

    response = wrapped.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert len(tracker.events) == 1
    event = tracker.events[0]
    assert event.provider == "mistral"
    assert event.model == "mistral-large-latest"
    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.cost_usd is not None
    assert event.cost_usd > 0


def test_wrap_mistral_with_tags():
    tracker = CostTracker(quiet=True)
    client = _make_mistral_client()
    wrapped = wrap(client, tracker=tracker)

    wrapped.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": "hi"}],
        compute_cfo_tags={"project": "code-gen"},
    )

    event = tracker.events[0]
    assert event.tags == {"project": "code-gen"}
