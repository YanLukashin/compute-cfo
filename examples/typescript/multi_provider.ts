/**
 * Multi-provider tracking with shared CostTracker.
 */

import { wrap, CostTracker } from 'compute-cfo';
import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';

const tracker = new CostTracker({ export: 'console' });

const openaiClient = wrap(new OpenAI(), { tracker });
const anthropicClient = wrap(new Anthropic(), { tracker });

// OpenAI call
await openaiClient.chat.completions.create({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'Hello from OpenAI' }],
  metadata: { project: 'multi-provider-demo', team: 'engineering' },
});

// Anthropic call
await anthropicClient.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 256,
  messages: [{ role: 'user', content: 'Hello from Anthropic' }],
  compute_cfo_tags: { project: 'multi-provider-demo', team: 'engineering' },
});

// Analyze spend
console.log(`\nTotal cost: $${tracker.totalCost.toFixed(6)}`);
console.log('By provider:', tracker.costBy('provider'));
console.log('By model:', tracker.costBy('model'));
console.log('By project:', tracker.costBy('project'));
