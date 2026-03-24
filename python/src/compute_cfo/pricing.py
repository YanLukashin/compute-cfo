"""Model pricing database for OpenAI and Anthropic.

Prices are in USD per 1 million tokens. Updated March 2026.
"""

from __future__ import annotations

from typing import Optional, Tuple

# {model_id: (input_price_per_1M, output_price_per_1M)}
MODEL_PRICES: dict[str, Tuple[float, float]] = {
    # ── OpenAI ──────────────────────────────────────────────
    # GPT-4.1 family
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    # GPT-4o family
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o-audio-preview": (2.50, 10.00),
    # GPT-4 legacy
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    # GPT-3.5
    "gpt-3.5-turbo": (0.50, 1.50),
    # o-series reasoning
    "o3": (2.00, 8.00),
    "o3-mini": (1.10, 4.40),
    "o4-mini": (1.10, 4.40),
    "o1": (15.00, 60.00),
    "o1-mini": (1.10, 4.40),
    "o1-preview": (15.00, 60.00),
    # Embeddings
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
    "text-embedding-ada-002": (0.10, 0.0),

    # ── Anthropic ───────────────────────────────────────────
    "claude-opus-4-20250514": (15.00, 75.00),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-3-7-sonnet-20250219": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-sonnet-20240620": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-opus-20240229": (15.00, 75.00),
    "claude-3-sonnet-20240229": (3.00, 15.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
    # Aliases
    "claude-opus-4-0": (15.00, 75.00),
    "claude-sonnet-4-0": (3.00, 15.00),
    "claude-3.7-sonnet": (3.00, 15.00),
    "claude-3.5-sonnet": (3.00, 15.00),
    "claude-3.5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
}

# Common aliases mapping
_ALIASES: dict[str, str] = {
    "gpt-4o-2024-11-20": "gpt-4o",
    "gpt-4o-2024-08-06": "gpt-4o",
    "gpt-4o-2024-05-13": "gpt-4o",
    "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
    "gpt-4-turbo-2024-04-09": "gpt-4-turbo",
    "gpt-4-turbo-preview": "gpt-4-turbo",
    "gpt-4-0125-preview": "gpt-4-turbo",
    "gpt-4-1106-preview": "gpt-4-turbo",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106": "gpt-3.5-turbo",
    "o3-2025-04-16": "o3",
    "o4-mini-2025-04-16": "o4-mini",
}


def resolve_model(model: str) -> str:
    """Resolve model aliases to canonical name."""
    return _ALIASES.get(model, model)


def get_price(model: str) -> Optional[Tuple[float, float]]:
    """Return (input_price, output_price) per 1M tokens, or None if unknown."""
    canonical = resolve_model(model)
    return MODEL_PRICES.get(canonical)


def get_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Calculate cost in USD for a given model and token counts.

    Returns None if model pricing is unknown.
    """
    price = get_price(model)
    if price is None:
        return None
    input_price, output_price = price
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
