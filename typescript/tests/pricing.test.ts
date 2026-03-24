import { getCost, getPrice, resolveModel } from '../src/pricing';

describe('pricing', () => {
  test('known model price', () => {
    const price = getPrice('gpt-4o');
    expect(price).toEqual({ inputPerMillion: 2.5, outputPerMillion: 10.0 });
  });

  test('anthropic model price', () => {
    const price = getPrice('claude-sonnet-4-20250514');
    expect(price).toEqual({ inputPerMillion: 3.0, outputPerMillion: 15.0 });
  });

  test('unknown model returns null', () => {
    expect(getPrice('nonexistent-model')).toBeNull();
  });

  test('alias resolution', () => {
    expect(resolveModel('gpt-4o-2024-11-20')).toBe('gpt-4o');
    expect(resolveModel('gpt-4o')).toBe('gpt-4o');
  });

  test('get cost calculation', () => {
    const cost = getCost('gpt-4o', 1000, 500);
    const expected = (1000 * 2.5 + 500 * 10.0) / 1_000_000;
    expect(cost).toBeCloseTo(expected, 10);
  });

  test('get cost unknown model', () => {
    expect(getCost('nonexistent', 100, 100)).toBeNull();
  });

  test('get cost alias', () => {
    const costAlias = getCost('gpt-4o-2024-11-20', 1000, 500);
    const costDirect = getCost('gpt-4o', 1000, 500);
    expect(costAlias).toBe(costDirect);
  });

  test('gemini model price', () => {
    const price = getPrice('gemini-2.5-flash');
    expect(price).toEqual({ inputPerMillion: 0.3, outputPerMillion: 2.5 });
  });

  test('gemini cost calculation', () => {
    const cost = getCost('gemini-2.5-pro', 1000, 500);
    const expected = (1000 * 1.25 + 500 * 10.0) / 1_000_000;
    expect(cost).toBeCloseTo(expected, 10);
  });

  test('gemini alias resolution', () => {
    expect(resolveModel('models/gemini-2.5-pro')).toBe('gemini-2.5-pro');
  });

  test('mistral model price', () => {
    const price = getPrice('mistral-large-latest');
    expect(price).toEqual({ inputPerMillion: 0.5, outputPerMillion: 1.5 });
  });

  test('mistral cost calculation', () => {
    const cost = getCost('mistral-small-latest', 1000, 500);
    const expected = (1000 * 0.03 + 500 * 0.11) / 1_000_000;
    expect(cost).toBeCloseTo(expected, 10);
  });

  test('mistral alias resolution', () => {
    expect(resolveModel('mistral-large-2501')).toBe('mistral-large-latest');
  });
});
