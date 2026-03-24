import { BudgetPolicy } from '../src/budget';
import { CostTracker } from '../src/tracker';
import { BudgetExceededError, CostEvent } from '../src/types';

function makeEvent(overrides: Partial<CostEvent> = {}): CostEvent {
  return {
    timestamp: new Date().toISOString(),
    provider: 'openai',
    model: 'gpt-4o',
    operation: 'chat.completions',
    inputTokens: 100,
    outputTokens: 50,
    costUsd: 0.01,
    tags: {},
    ...overrides,
  };
}

describe('BudgetPolicy', () => {
  test('throw on exceed', () => {
    const tracker = new CostTracker({
      budget: new BudgetPolicy({ maxCost: 0.05, onExceed: 'throw' }),
      quiet: true,
    });
    tracker.record(makeEvent({ costUsd: 0.03 }));
    expect(() => tracker.record(makeEvent({ costUsd: 0.03 }))).toThrow(
      BudgetExceededError
    );
  });

  test('warn on exceed', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
    const tracker = new CostTracker({
      budget: new BudgetPolicy({ maxCost: 0.05, onExceed: 'warn' }),
      quiet: true,
    });
    tracker.record(makeEvent({ costUsd: 0.03 }));
    tracker.record(makeEvent({ costUsd: 0.03 }));
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Budget warning')
    );
    warnSpy.mockRestore();
  });

  test('callback on exceed', () => {
    const exceeded: Array<[CostEvent, number]> = [];
    const tracker = new CostTracker({
      budget: new BudgetPolicy({
        maxCost: 0.05,
        onExceed: 'callback',
        onExceedCallback: (event, projected) =>
          exceeded.push([event, projected]),
      }),
      quiet: true,
    });
    tracker.record(makeEvent({ costUsd: 0.03 }));
    tracker.record(makeEvent({ costUsd: 0.03 }));
    expect(exceeded.length).toBe(1);
    expect(exceeded[0][1]).toBeGreaterThan(0.05);
  });

  test('not exceeded', () => {
    const tracker = new CostTracker({
      budget: new BudgetPolicy({ maxCost: 1.0, onExceed: 'throw' }),
      quiet: true,
    });
    tracker.record(makeEvent({ costUsd: 0.03 }));
    tracker.record(makeEvent({ costUsd: 0.03 }));
    expect(tracker.totalCost).toBeCloseTo(0.06, 10);
  });

  test('budget remaining tracked', () => {
    const tracker = new CostTracker({
      budget: new BudgetPolicy({ maxCost: 1.0 }),
      quiet: true,
    });
    tracker.record(makeEvent({ costUsd: 0.3 }));
    const event = tracker.events[0];
    expect(event.budgetRemainingUsd).toBeCloseTo(0.7, 10);
  });

  test('budget with tag filter', () => {
    const tracker = new CostTracker({
      budget: new BudgetPolicy({
        maxCost: 0.05,
        onExceed: 'throw',
        tags: { project: 'expensive' },
      }),
      quiet: true,
    });
    // Should not count toward budget
    tracker.record(makeEvent({ costUsd: 0.1, tags: { project: 'cheap' } }));
    // Should count
    tracker.record(
      makeEvent({ costUsd: 0.03, tags: { project: 'expensive' } })
    );
    // Should exceed
    expect(() =>
      tracker.record(
        makeEvent({ costUsd: 0.03, tags: { project: 'expensive' } })
      )
    ).toThrow(BudgetExceededError);
  });
});
