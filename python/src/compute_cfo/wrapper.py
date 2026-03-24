"""Drop-in wrapper for OpenAI, Anthropic, Google Gemini, and Mistral SDK clients."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

from .pricing import get_cost
from .tracker import CostTracker
from .types import CostEvent

_DEFAULT_TRACKER: Optional[CostTracker] = None


def _get_or_create_default_tracker() -> CostTracker:
    global _DEFAULT_TRACKER
    if _DEFAULT_TRACKER is None:
        _DEFAULT_TRACKER = CostTracker(export="console")
    return _DEFAULT_TRACKER


def wrap(client: Any, tracker: Optional[CostTracker] = None) -> Any:
    """Wrap an OpenAI or Anthropic client with cost tracking.

    Args:
        client: An instance of openai.OpenAI or anthropic.Anthropic.
        tracker: Optional CostTracker. If not provided, a default one
                 with console output is used.

    Returns:
        A wrapped client that tracks costs transparently.
    """
    tracker = tracker or _get_or_create_default_tracker()

    client_type = type(client).__module__.split(".")[0]
    client_class = type(client).__name__

    if client_type == "openai":
        if "Async" in client_class:
            return _AsyncOpenAIWrapper(client, tracker)
        return _OpenAIWrapper(client, tracker)
    elif client_type == "anthropic":
        if "Async" in client_class:
            return _AsyncAnthropicWrapper(client, tracker)
        return _AnthropicWrapper(client, tracker)
    elif client_type in ("google", "google_genai"):
        return _GeminiWrapper(client, tracker)
    elif client_type == "mistralai":
        return _MistralWrapper(client, tracker)
    elif client_type == "groq":
        return _OpenAIWrapper(client, tracker, provider="groq")
    elif client_type == "together":
        return _OpenAIWrapper(client, tracker, provider="together")
    else:
        raise TypeError(
            f"Unsupported client type: {type(client).__name__}. "
            f"Supported: openai.OpenAI, anthropic.Anthropic, "
            f"google.genai.Client, mistralai.Mistral, groq.Groq, together.Together"
        )


class _StreamWrapper:
    """Wraps an OpenAI streaming response to track cost when stream completes."""

    def __init__(
        self, stream: Any, model: str, tags: Dict[str, str],
        tracker: CostTracker, start: float, provider: str = "openai",
    ):
        self._stream = stream
        self._model = model
        self._tags = tags
        self._tracker = tracker
        self._start = start
        self._provider = provider
        self._usage = None

    def __iter__(self) -> Iterator[Any]:
        for chunk in self._stream:
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                self._usage = usage
            yield chunk
        self._record()

    def __enter__(self) -> "_StreamWrapper":
        if hasattr(self._stream, "__enter__"):
            self._stream.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if hasattr(self._stream, "__exit__"):
            self._stream.__exit__(*args)

    def _record(self) -> None:
        latency_ms = (time.monotonic() - self._start) * 1000
        input_tokens = 0
        output_tokens = 0
        if self._usage:
            input_tokens = getattr(self._usage, "prompt_tokens", 0)
            output_tokens = getattr(self._usage, "completion_tokens", 0)

        cost = get_cost(self._model, input_tokens, output_tokens)
        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider=self._provider,
            model=self._model,
            operation="chat.completions",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=self._tags,
        )
        self._tracker.record(event)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


class _TrackedCompletions:
    """Proxy for client.chat.completions with cost tracking."""

    def __init__(self, completions: Any, tracker: CostTracker, provider: str = "openai"):
        self._completions = completions
        self._tracker = tracker
        self._provider = provider

    def create(self, **kwargs: Any) -> Any:
        tags = kwargs.pop("metadata", None) or {}
        if not isinstance(tags, dict):
            tags = {}

        stream = kwargs.get("stream", False)
        model = kwargs.get("model", "unknown")
        start = time.monotonic()
        response = self._completions.create(**kwargs)

        if stream:
            return _StreamWrapper(response, model, tags, self._tracker, start, self._provider)

        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        actual_model = getattr(response, "model", model)
        cost = get_cost(actual_model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider=self._provider,
            model=actual_model,
            operation="chat.completions",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _TrackedChat:
    """Proxy for client.chat with tracked completions."""

    def __init__(self, chat: Any, tracker: CostTracker, provider: str = "openai"):
        self._chat = chat
        self._tracker = tracker
        self.completions = _TrackedCompletions(chat.completions, tracker, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class _OpenAIWrapper:
    """Proxy for OpenAI client (also used for Groq, Together AI)."""

    def __init__(self, client: Any, tracker: CostTracker, provider: str = "openai"):
        self._client = client
        self._tracker = tracker
        self.chat = _TrackedChat(client.chat, tracker, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _AsyncOpenAIWrapper:
    """Proxy for AsyncOpenAI client."""

    def __init__(self, client: Any, tracker: CostTracker, provider: str = "openai"):
        self._client = client
        self._tracker = tracker
        self._provider = provider
        self.chat = _AsyncTrackedChat(client.chat, tracker, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _AsyncTrackedChat:
    """Proxy for async client.chat."""

    def __init__(self, chat: Any, tracker: CostTracker, provider: str = "openai"):
        self._chat = chat
        self._tracker = tracker
        self.completions = _AsyncTrackedCompletions(chat.completions, tracker, provider)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class _AsyncTrackedCompletions:
    """Proxy for async client.chat.completions."""

    def __init__(self, completions: Any, tracker: CostTracker, provider: str = "openai"):
        self._completions = completions
        self._tracker = tracker
        self._provider = provider

    async def create(self, **kwargs: Any) -> Any:
        tags = kwargs.pop("metadata", None) or {}
        if not isinstance(tags, dict):
            tags = {}

        model = kwargs.get("model", "unknown")
        start = time.monotonic()
        response = await self._completions.create(**kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        actual_model = getattr(response, "model", model)
        cost = get_cost(actual_model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider=self._provider,
            model=actual_model,
            operation="chat.completions",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _AsyncAnthropicWrapper:
    """Proxy for AsyncAnthropic client."""

    def __init__(self, client: Any, tracker: CostTracker):
        self._client = client
        self._tracker = tracker
        self.messages = _AsyncTrackedMessages(client.messages, tracker)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _AsyncTrackedMessages:
    """Proxy for async client.messages (Anthropic)."""

    def __init__(self, messages: Any, tracker: CostTracker):
        self._messages = messages
        self._tracker = tracker

    async def create(self, **kwargs: Any) -> Any:
        metadata = kwargs.get("metadata", None)
        tags: Dict[str, str] = {}
        if isinstance(metadata, dict):
            tags = {k: str(v) for k, v in metadata.items() if k != "user_id"}

        explicit_tags = kwargs.pop("compute_cfo_tags", None)
        if isinstance(explicit_tags, dict):
            tags.update(explicit_tags)

        model = kwargs.get("model", "unknown")
        start = time.monotonic()
        response = await self._messages.create(**kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        actual_model = getattr(response, "model", model)
        cost = get_cost(actual_model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider="anthropic",
            model=actual_model,
            operation="messages",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._messages, name)


class _TrackedMessages:
    """Proxy for client.messages (Anthropic) with cost tracking."""

    def __init__(self, messages: Any, tracker: CostTracker):
        self._messages = messages
        self._tracker = tracker

    def create(self, **kwargs: Any) -> Any:
        metadata = kwargs.get("metadata", None)
        tags: Dict[str, str] = {}
        if isinstance(metadata, dict):
            # Anthropic metadata has a user_id field; we extract custom tags
            tags = {k: str(v) for k, v in metadata.items() if k != "user_id"}

        # Also support a compute_cfo_tags kwarg for explicit tagging
        explicit_tags = kwargs.pop("compute_cfo_tags", None)
        if isinstance(explicit_tags, dict):
            tags.update(explicit_tags)

        model = kwargs.get("model", "unknown")
        start = time.monotonic()
        response = self._messages.create(**kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        actual_model = getattr(response, "model", model)
        cost = get_cost(actual_model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider="anthropic",
            model=actual_model,
            operation="messages",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._messages, name)


class _AnthropicWrapper:
    """Proxy for Anthropic client."""

    def __init__(self, client: Any, tracker: CostTracker):
        self._client = client
        self._tracker = tracker
        self.messages = _TrackedMessages(client.messages, tracker)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _TrackedGeminiModels:
    """Proxy for Google Gemini client.models with cost tracking."""

    def __init__(self, models: Any, tracker: CostTracker):
        self._models = models
        self._tracker = tracker

    def generate_content(self, **kwargs: Any) -> Any:
        tags = kwargs.pop("compute_cfo_tags", None) or {}
        if not isinstance(tags, dict):
            tags = {}

        model = kwargs.get("model", "unknown")
        # Strip "models/" prefix for pricing lookup
        if isinstance(model, str) and model.startswith("models/"):
            model = model[len("models/"):]

        start = time.monotonic()
        response = self._models.generate_content(**kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        cost = get_cost(model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider="google",
            model=model,
            operation="generate_content",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._models, name)


class _GeminiWrapper:
    """Proxy for Google Gemini client."""

    def __init__(self, client: Any, tracker: CostTracker):
        self._client = client
        self._tracker = tracker
        self.models = _TrackedGeminiModels(client.models, tracker)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _TrackedMistralChat:
    """Proxy for Mistral client.chat with cost tracking."""

    def __init__(self, chat: Any, tracker: CostTracker):
        self._chat = chat
        self._tracker = tracker

    def complete(self, **kwargs: Any) -> Any:
        tags = kwargs.pop("compute_cfo_tags", None) or {}
        if not isinstance(tags, dict):
            tags = {}

        model = kwargs.get("model", "unknown")
        start = time.monotonic()
        response = self._chat.complete(**kwargs)
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        actual_model = getattr(response, "model", model)
        cost = get_cost(actual_model, input_tokens, output_tokens)

        event = CostEvent(
            timestamp=datetime.now(timezone.utc),
            provider="mistral",
            model=actual_model,
            operation="chat.complete",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=round(latency_ms, 1),
            tags=tags,
        )
        self._tracker.record(event)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class _MistralWrapper:
    """Proxy for Mistral client."""

    def __init__(self, client: Any, tracker: CostTracker):
        self._client = client
        self._tracker = tracker
        self.chat = _TrackedMistralChat(client.chat, tracker)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)
