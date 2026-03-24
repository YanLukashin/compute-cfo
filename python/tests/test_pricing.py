from compute_cfo.pricing import get_cost, get_price, resolve_model


def test_known_model_price():
    price = get_price("gpt-4o")
    assert price == (2.50, 10.00)


def test_anthropic_model_price():
    price = get_price("claude-sonnet-4-20250514")
    assert price == (3.00, 15.00)


def test_unknown_model_returns_none():
    assert get_price("nonexistent-model") is None


def test_alias_resolution():
    assert resolve_model("gpt-4o-2024-11-20") == "gpt-4o"
    assert resolve_model("gpt-4o") == "gpt-4o"  # not an alias, returns as-is


def test_get_cost_calculation():
    # gpt-4o: $2.50 input, $10.00 output per 1M tokens
    cost = get_cost("gpt-4o", input_tokens=1000, output_tokens=500)
    assert cost is not None
    expected = (1000 * 2.50 + 500 * 10.00) / 1_000_000
    assert abs(cost - expected) < 1e-10


def test_get_cost_unknown_model():
    assert get_cost("nonexistent", 100, 100) is None


def test_get_cost_alias():
    cost_alias = get_cost("gpt-4o-2024-11-20", 1000, 500)
    cost_direct = get_cost("gpt-4o", 1000, 500)
    assert cost_alias == cost_direct


def test_embedding_model_no_output_cost():
    cost = get_cost("text-embedding-3-small", input_tokens=1000, output_tokens=0)
    assert cost is not None
    expected = (1000 * 0.02) / 1_000_000
    assert abs(cost - expected) < 1e-10
