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
});
