/**
 * Budget enforcement — stop runaway spend.
 */

import { wrap, CostTracker, BudgetPolicy } from 'compute-cfo';
import OpenAI from 'openai';

const tracker = new CostTracker({
  budget: new BudgetPolicy({
    maxCost: 0.05,       // $0.05 limit for demo
    window: 'daily',
    onExceed: 'throw',
  }),
  export: 'console',
});

const client = wrap(new OpenAI(), { tracker });

try {
  for (let i = 0; i < 100; i++) {
    await client.chat.completions.create({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: `Count to ${i}` }],
      metadata: { project: 'budget-demo' },
    });
    console.log(`Call ${i + 1}: $${tracker.totalCost.toFixed(6)} spent`);
  }
} catch (e) {
  console.log(`\nBudget exceeded! ${e}`);
  console.log(`Total spent: $${tracker.totalCost.toFixed(6)}`);
}
