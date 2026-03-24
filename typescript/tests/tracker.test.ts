import { CostTracker } from '../src/tracker';
import { CostEvent } from '../src/types';

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

describe('CostTracker', () => {
  test('empty tracker', () => {
    const t = new CostTracker({ quiet: true });
    expect(t.totalCost).toBe(0);
    expect(t.events).toEqual([]);
  });

  test('record and total', () => {
    const t = new CostTracker({ quiet: true });
    t.record(makeEvent({ costUsd: 0.05 }));
    t.record(makeEvent({ costUsd: 0.03 }));
    expect(t.totalCost).toBeCloseTo(0.08, 10);
  });

  test('cost by model', () => {
    const t = new CostTracker({ quiet: true });
    t.record(makeEvent({ costUsd: 0.05, model: 'gpt-4o' }));
    t.record(makeEvent({ costUsd: 0.01, model: 'gpt-4o-mini' }));
    t.record(makeEvent({ costUsd: 0.03, model: 'gpt-4o' }));
    const byModel = t.costBy('model');
    expect(byModel['gpt-4o']).toBeCloseTo(0.08, 10);
    expect(byModel['gpt-4o-mini']).toBeCloseTo(0.01, 10);
  });

  test('cost by tag', () => {
    const t = new CostTracker({ quiet: true });
    t.record(makeEvent({ costUsd: 0.05, tags: { project: 'search' } }));
    t.record(makeEvent({ costUsd: 0.03, tags: { project: 'chat' } }));
    t.record(makeEvent({ costUsd: 0.02, tags: { project: 'search' } }));
    const byProject = t.costBy('project');
    expect(byProject['search']).toBeCloseTo(0.07, 10);
    expect(byProject['chat']).toBeCloseTo(0.03, 10);
  });

  test('reset', () => {
    const t = new CostTracker({ quiet: true });
    t.record(makeEvent({ costUsd: 0.05 }));
    t.reset();
    expect(t.totalCost).toBe(0);
    expect(t.events).toEqual([]);
  });

  test('events returns copy', () => {
    const t = new CostTracker({ quiet: true });
    t.record(makeEvent({ costUsd: 0.05 }));
    const events = t.events;
    events.length = 0;
    expect(t.events.length).toBe(1);
  });
});
